from dataclasses import dataclass, field


SUPPORTED_PROVIDERS = ("openai", "anthropic", "gemini")
REDACTION = "[REDACTED_API_KEY]"


class ProviderKeyError(ValueError):
    pass


def normalize_provider(provider):
    normalized = str(provider or "").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        choices = ", ".join(SUPPORTED_PROVIDERS)
        raise ProviderKeyError(f"Unsupported provider {provider!r}. Choose one of: {choices}.")
    return normalized


def redact_secrets(text, secrets):
    redacted = str(text)
    for secret in secrets:
        if secret:
            redacted = redacted.replace(str(secret), REDACTION)
    return redacted


@dataclass
class SessionKeyStore:
    """In-memory BYOK storage for a running app process.

    This object is intentionally boring: no files, no environment mutation, no
    logging hooks. A web backend can keep one of these per process and clear it
    when a user session ends.
    """

    _keys: dict[str, dict[str, str]] = field(default_factory=dict)

    def set_key(self, session_id, provider, api_key):
        session_id = str(session_id or "").strip()
        api_key = str(api_key or "").strip()
        if not session_id:
            raise ProviderKeyError("Session id is required.")
        if not api_key:
            raise ProviderKeyError("API key is required.")
        provider = normalize_provider(provider)
        self._keys.setdefault(session_id, {})[provider] = api_key

    def get_key(self, session_id, provider):
        provider = normalize_provider(provider)
        return self._keys.get(str(session_id), {}).get(provider)

    def clear_key(self, session_id, provider):
        provider = normalize_provider(provider)
        keys = self._keys.get(str(session_id))
        if not keys:
            return
        keys.pop(provider, None)
        if not keys:
            self._keys.pop(str(session_id), None)

    def clear_session(self, session_id):
        self._keys.pop(str(session_id), None)
