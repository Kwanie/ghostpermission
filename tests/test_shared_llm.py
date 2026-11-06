import sys
import types
import pytest
from agents import shared_llm


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("GROQ_API_KEY", "OPENAI_API_KEY", "GHOST_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)


def install_fake_groq(monkeypatch):
    seen = {}
    class ChatGroq:
        def __init__(self, **kwargs):
            seen.update(kwargs)
    monkeypatch.setitem(sys.modules, "langchain_groq", types.SimpleNamespace(ChatGroq=ChatGroq))
    return seen


def test_no_key_means_no_model_and_a_friendly_status():
    assert shared_llm.get_llm() is None
    assert "no API key" in shared_llm.llm_status() and "rule-based" in shared_llm.llm_status()


def test_groq_key_builds_the_default_model_and_cleans_the_key(monkeypatch):
    seen = install_fake_groq(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", ' "gsk_abcdefghijklmnopqrstuvwxyz" ')
    assert shared_llm.get_llm() is not None
    assert seen["api_key"] == "gsk_abcdefghijklmnopqrstuvwxyz" and seen["model"] == "openai/gpt-oss-120b"
    assert seen["temperature"] == 0


def test_model_name_can_be_changed_in_the_env_file(monkeypatch):
    seen = install_fake_groq(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_abcdefghijklmnopqrstuvwxyz")
    monkeypatch.setenv("GHOST_LLM_MODEL", "some/other-model")
    shared_llm.get_llm()
    assert seen["model"] == "some/other-model"
    assert "some/other-model" in shared_llm.llm_status()


def test_missing_package_gives_install_advice_not_a_crash(monkeypatch):
    monkeypatch.setitem(sys.modules, "langchain_groq", None)     # makes the import fail
    monkeypatch.setenv("GROQ_API_KEY", "gsk_abcdefghijklmnopqrstuvwxyz")
    assert shared_llm.get_llm() is None
    assert "pip install langchain-groq" in shared_llm.llm_status()


def test_status_never_contains_the_key(monkeypatch):
    install_fake_groq(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_SECRETSECRETSECRETSECRET")
    assert "SECRET" not in shared_llm.llm_status()
