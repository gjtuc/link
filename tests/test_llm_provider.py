"""LLM provider resolution tests."""

from deconstructor import config


def test_resolve_gemini_when_gemini_key(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    assert config.resolve_llm_provider() == "gemini"


def test_resolve_openai_when_only_openai(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-test")
    assert config.resolve_llm_provider() == "openai"
