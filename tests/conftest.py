import json
import pytest


class FakeLLM:
    """A pretend AI model for tests. It returns the replies you give it, one per call."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        reply = self.replies.pop(0) if self.replies else "{}"
        if isinstance(reply, Exception):
            raise reply
        if not isinstance(reply, str):
            reply = json.dumps(reply)
        return type("Reply", (), {"content": reply})()


@pytest.fixture
def fake_llm():
    return FakeLLM


@pytest.fixture(autouse=True)
def tests_never_call_a_real_ai(monkeypatch):
    """Even if your .env has real keys, tests must never reach a real AI service
    (it would be slow, cost quota, and make results unpredictable)."""
    for name in ("GROQ_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
