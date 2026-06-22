import httpx

from backend.app.llm.base import LlmProvider


class AnthropicProvider(LlmProvider):
    name = "anthropic"

    async def complete(self, *, api_key, model, messages, temperature=0):
        system = "\n\n".join(message.content for message in messages if message.role == "system")
        user_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in ("user", "assistant")
        ]
        payload = {
            "model": model or "claude-sonnet-4-6",
            "max_tokens": 1200,
            "system": system,
            "messages": user_messages,
        }
        if temperature is not None and not (payload["model"] or "").startswith(("claude-opus-4-8", "claude-opus-4-7")):
            payload["temperature"] = temperature
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return "\n".join(part["text"] for part in data.get("content", []) if part.get("type") == "text")
