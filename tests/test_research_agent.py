import pytest
from research_agent import (
    validate_url,
    find_privacy_policy_url,
    scrape_policy_text,
    find_exact_policy_quotes,
    verify_quote_in_policy
)

def test_validate_url_security():
    assert validate_url("https://example.com/privacy") is True
    assert validate_url("http://example.com/privacy") is True
    assert validate_url("file:///etc/passwd") is False
    assert validate_url("ftp://example.com") is False
    assert validate_url(None) is False

def test_find_exact_policy_quotes_matching():
    sample_policy = (
        "We welcome you to our service. We may sell your data to third party marketing affiliates. "
        "We also track location for ad targeting purposes."
    )
    quotes = find_exact_policy_quotes(sample_policy)
    assert len(quotes) >= 2
    topics = [q["topic"] for q in quotes]
    assert "Sell" in topics or "Third party" in topics

def test_verify_quote_in_policy_truthfulness():
    sample_text = "We retain user records indefinitely upon account closure."
    valid_quote = "We retain user records indefinitely upon account closure."
    fake_quote = "We delete all user records immediately."
    
    assert verify_quote_in_policy(valid_quote, sample_text) is True
    assert verify_quote_in_policy(fake_quote, sample_text) is False

def test_pasted_text_fallback():
    raw_text = "Direct pasted terms text without URL."
    result = scrape_policy_text(raw_text)
    assert result["source"] == "Pasted Policy Text"
    assert result["text"] == raw_text
    