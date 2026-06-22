from backend.app.llm.anthropic_provider import AnthropicProvider
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.openai_provider import OpenAIProvider


PROVIDERS = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini": GeminiProvider(),
}


def get_provider(name):
    return PROVIDERS[name]
