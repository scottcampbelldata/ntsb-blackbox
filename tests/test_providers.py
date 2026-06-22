import pytest

from providers import ProviderKeyError, SessionKeyStore, normalize_provider, redact_secrets


def test_provider_names_are_normalized():
    assert normalize_provider(" OpenAI ") == "openai"
    assert normalize_provider("ANTHROPIC") == "anthropic"
    assert normalize_provider("gemini") == "gemini"


def test_unsupported_provider_is_rejected():
    with pytest.raises(ProviderKeyError):
        normalize_provider("not-a-provider")


def test_session_key_store_is_in_memory_and_clearable():
    store = SessionKeyStore()
    store.set_key("session-1", "openai", "sk-test")
    assert store.get_key("session-1", "openai") == "sk-test"

    store.clear_key("session-1", "openai")
    assert store.get_key("session-1", "openai") is None


def test_session_clear_removes_all_provider_keys():
    store = SessionKeyStore()
    store.set_key("session-1", "openai", "sk-openai")
    store.set_key("session-1", "gemini", "gemini-key")

    store.clear_session("session-1")

    assert store.get_key("session-1", "openai") is None
    assert store.get_key("session-1", "gemini") is None


def test_redact_secrets_removes_exact_key_values():
    message = "OpenAI failed with sk-openai and Gemini failed with gemini-key"
    redacted = redact_secrets(message, ["sk-openai", "gemini-key"])
    assert "sk-openai" not in redacted
    assert "gemini-key" not in redacted
    assert redacted.count("[REDACTED_API_KEY]") == 2
