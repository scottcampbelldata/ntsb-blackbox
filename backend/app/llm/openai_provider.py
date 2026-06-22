import httpx

from backend.app.llm.base import LlmProvider


class OpenAIProvider(LlmProvider):
    name = "openai"

    async def complete(self, *, api_key, model, messages, temperature=0):
        payload = {
            "model": model or "gpt-5.4-mini",
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
