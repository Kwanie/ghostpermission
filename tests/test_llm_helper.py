from typing import List
from pydantic import BaseModel
from agents.llm_helper import ask_structured, quote_is_in


class Answer(BaseModel):
    items: List[str]


def test_good_json_is_parsed(fake_llm):
    result, error = ask_structured(fake_llm(['{"items": ["a", "b"]}']), Answer, "sys", "user")
    assert error is None and result.items == ["a", "b"]


def test_json_inside_code_fences_and_extra_words_is_still_parsed(fake_llm):
    reply = 'Sure! Here you go:\n```json\n{"items": ["x"]}\n```\nHope that helps.'
    result, _ = ask_structured(fake_llm([reply]), Answer, "sys", "user")
    assert result.items == ["x"]


def test_one_bad_answer_is_retried_once(fake_llm):
    llm = fake_llm(["not json at all", '{"items": ["ok"]}'])
    result, error = ask_structured(llm, Answer, "sys", "user")
    assert result.items == ["ok"] and len(llm.calls) == 2


def test_wrong_shape_twice_gives_a_clear_error_and_never_raises(fake_llm):
    result, error = ask_structured(fake_llm(['{"wrong": 1}', '{"wrong": 2}']), Answer, "sys", "user")
    assert result is None and "ValidationError" in error


def test_provider_error_is_caught(fake_llm):
    result, error = ask_structured(fake_llm([RuntimeError("401 invalid key"), RuntimeError("401 invalid key")]), Answer, "s", "u")
    assert result is None and "RuntimeError" in error


def test_the_schema_is_sent_to_the_model(fake_llm):
    llm = fake_llm(['{"items": []}'])
    ask_structured(llm, Answer, "sys", "user")
    assert "items" in llm.calls[0][0][1]


def test_quote_check_ignores_case_quotes_and_spacing():
    assert quote_is_in("  Track  EVERY trip ", 'Helps cyclists "track every trip" daily') is True
    assert quote_is_in("record rides", "Helps cyclists track every trip") is False
    assert quote_is_in("", "anything") is False and quote_is_in("ab", "abc") is False
