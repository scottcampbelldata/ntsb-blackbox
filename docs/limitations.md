# Limitations

Black Box AI is an analytical exploration tool over a loaded public NTSB dataset. It is not an official aviation safety system and should not be used for operational decisions.

## Dataset Limits

- The loaded corpus is not every aviation accident.
- The current README notes that 2020 and 2021 are absent from this dataset.
- Recent years can be incomplete because NTSB final reports take time to publish.
- Some source fields are sparse or corrupted, including `highest_injury_level`.
- Multi-aircraft records can concatenate values in fields such as `number_of_engines`.

## Modeling Limits

- Model-generated answers can be wrong if they are not grounded.
- The system must distinguish SQL-backed counts from retrieval-backed explanations.
- Narrative retrieval examples do not prove statistical frequency.
- SQL results only reflect fields present in the structured table.

## Safety Limits

- Generated SQL is accepted only after validation.
- Generated charts are accepted only after validation.
- Provider keys are user-owned secrets and should stay server-side after submission.
- The audit trail should expose route, SQL, chart fields, citations, and limitations.

## Product Positioning

The product promise is not "ask anything about anything."

The promise is:

Ask plain-English questions about the NTSB accident corpus. The system decides whether to search narratives, run SQL, build a chart, or combine both, then returns cited evidence, executed queries, visualizations, and clear limitations.

