from backend.app.llm.base import LlmMessage
from schema_catalog import schema_prompt_context


def sql_messages(question):
    return [
        LlmMessage(
            role="system",
            content=(
                "You generate Postgres SQL for an aviation safety analytics app. "
                "Return one SELECT statement only. Use only the provided schema. "
                "Do not include markdown, comments, explanations, CTEs, mutations, or multiple statements. "
                "Use COUNT, SUM, AVG, MIN, MAX, ROUND, UPPER, LOWER, TRIM, COALESCE only when needed. "
                "Always include a LIMIT no larger than 500."
            ),
        ),
        LlmMessage(
            role="user",
            content=f"{schema_prompt_context()}\n\nQuestion: {question}\n\nSQL:",
        ),
    ]


def retrieval_answer_messages(question, citations):
    evidence = []
    for citation in citations:
        evidence.append(
            "\n".join(
                [
                    f"NTSB: {citation.get('ntsb_no')}",
                    f"URL: {citation.get('report_url')}",
                    f"Probable cause: {citation.get('probable_cause')}",
                    f"Matched passage: {citation.get('matched_passage')}",
                ]
            )
        )
    return [
        LlmMessage(
            role="system",
            content=(
                "Answer using only the provided NTSB report evidence. "
                "Cite accident numbers inline. Do not claim statistical frequency from examples. "
                "State limitations plainly when the evidence is narrative rather than counted."
            ),
        ),
        LlmMessage(
            role="user",
            content=f"Question: {question}\n\nEvidence:\n\n" + "\n\n---\n\n".join(evidence),
        ),
    ]
