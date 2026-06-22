from dataclasses import dataclass


ALLOWED_MARKS = {"bar", "line", "point", "area", "tick", "rect", "circle"}
ALLOWED_TOP_LEVEL_KEYS = {
    "$schema",
    "mark",
    "encoding",
    "title",
    "width",
    "height",
    "config",
}
ALLOWED_ENCODING_CHANNELS = {
    "x",
    "y",
    "color",
    "column",
    "row",
    "size",
    "tooltip",
    "xOffset",
    "yOffset",
}
DISALLOWED_KEYS = {"data", "datasets", "transform", "params", "selection"}


class ChartValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ChartValidationResult:
    spec: dict
    referenced_fields: tuple[str, ...]


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _normalize_dataframe_columns(dataframe_columns):
    return {str(col) for col in dataframe_columns}


def _mark_type(mark):
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        return mark.get("type")
    return None


def _collect_fields(channel_def, fields):
    if isinstance(channel_def, list):
        for item in channel_def:
            _collect_fields(item, fields)
        return
    if not isinstance(channel_def, dict):
        return
    field = channel_def.get("field")
    if field is not None:
        fields.add(str(field))


def validate_vega_lite_spec(spec, dataframe_columns):
    """Validate an LLM-generated Vega-Lite spec against a real dataframe schema."""
    if not isinstance(spec, dict):
        raise ChartValidationError("Chart spec must be a JSON object.")

    unknown_top_level = set(spec) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_top_level:
        names = ", ".join(sorted(unknown_top_level))
        raise ChartValidationError(f"Unsupported Vega-Lite top-level keys: {names}.")

    for key in _walk_keys(spec):
        if key in DISALLOWED_KEYS:
            raise ChartValidationError(f"Chart spec may not contain {key!r}.")

    mark = _mark_type(spec.get("mark"))
    if mark not in ALLOWED_MARKS:
        raise ChartValidationError(f"Unsupported mark type: {mark!r}.")

    encoding = spec.get("encoding")
    if not isinstance(encoding, dict):
        raise ChartValidationError("Chart spec must include an encoding object.")
    if "x" not in encoding or "y" not in encoding:
        raise ChartValidationError("Chart spec must include x and y encodings.")

    unknown_channels = set(encoding) - ALLOWED_ENCODING_CHANNELS
    if unknown_channels:
        names = ", ".join(sorted(unknown_channels))
        raise ChartValidationError(f"Unsupported encoding channels: {names}.")

    referenced_fields = set()
    for channel_def in encoding.values():
        _collect_fields(channel_def, referenced_fields)

    if not referenced_fields:
        raise ChartValidationError("Chart spec must reference dataframe fields.")

    allowed_fields = _normalize_dataframe_columns(dataframe_columns)
    missing = referenced_fields - allowed_fields
    if missing:
        names = ", ".join(sorted(missing))
        raise ChartValidationError(f"Chart references fields not in dataframe: {names}.")

    return ChartValidationResult(
        spec=spec,
        referenced_fields=tuple(sorted(referenced_fields)),
    )
