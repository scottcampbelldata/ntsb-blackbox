import re

from backend.app.llm.prompts import retrieval_answer_messages, sql_messages
from backend.app.llm.providers import get_provider


def _strip_sql(text):
    text = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    return text


async def generate_sql(provider_name, *, api_key, model, question):
    provider = get_provider(provider_name)
    text = await provider.complete(
        api_key=api_key,
        model=model,
        messages=sql_messages(question),
        temperature=0,
    )
    return _strip_sql(text)


async def synthesize_retrieval_answer(provider_name, *, api_key, model, question, citations):
    provider = get_provider(provider_name)
    return await provider.complete(
        api_key=api_key,
        model=model,
        messages=retrieval_answer_messages(question, citations),
        temperature=0,
    )
