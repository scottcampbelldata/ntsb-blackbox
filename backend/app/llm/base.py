from dataclasses import dataclass


@dataclass(frozen=True)
class LlmMessage:
    role: str
    content: str


class LlmProvider:
    name = "base"

    async def complete(self, *, api_key, model, messages, temperature=0):
        raise NotImplementedError
