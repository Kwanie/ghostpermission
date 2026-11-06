import pytest
from core.config import MissingKeyError, clean, explain_http_status, get_key, key_problems

KEY = "gsk_abcdefghijklmnopqrstuvwxyz"

def test_clean_removes_spaces_quotes_and_line_breaks():
    assert clean('  "abc123"\n') == "abc123" and clean("'abc123'") == "abc123"

def test_get_key_returns_cleaned_value(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", '  "' + KEY + '"  ')
    assert get_key("GROQ_API_KEY") == KEY

def test_missing_key_error_names_the_key_but_has_no_secret(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(MissingKeyError) as problem:
        get_key("GROQ_API_KEY")
    assert "GROQ_API_KEY" in str(problem.value) and ".env" in str(problem.value)

def test_key_problems_finds_quotes_spaces_and_wrong_provider():
    assert key_problems("GROQ_API_KEY", KEY) == []
    assert any("quote" in p for p in key_problems("GROQ_API_KEY", '"' + KEY + '"'))
    assert any("space" in p.lower() for p in key_problems("GROQ_API_KEY", " " + KEY))
    assert any("start with gsk_" in p for p in key_problems("GROQ_API_KEY", "sk-abcdefghijklmnopqrstuvwxyz"))
    assert key_problems("GROQ_API_KEY", "") == ["The key is empty."]

def test_status_codes_give_helpful_advice():
    assert "REJECTED" in explain_http_status(401) and "REJECTED" in explain_http_status(403)
    assert "limit" in explain_http_status(429) and "model name" in explain_http_status(400)
    assert "trouble" in explain_http_status(503)
