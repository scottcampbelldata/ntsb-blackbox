import httpx

from backend.app.llm.base import LlmProvider


class GeminiProvider(LlmProvider):
    name = "gemini"

    async def complete(self, *, api_key, model, messages, temperature=0):
        prompt = "\n\n".join(f"{message.role}: {message.content}" for message in messages)
        model_name = model or "gemini-3.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, params={"key": api_key}, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "\n".join(part.get("text", "") for part in parts)
