import pytest
from core.text_match import mentions

LOCATION = ["location", "map", "navigation", "gps"]

@pytest.mark.parametrize("text", [
    "A simple flashlight app. No location or contacts needed.",
    "This app does not use your location.",
    "It doesn't need location access.",
    "Never shares your location with anyone.",
    "Works without GPS.",
    "A bitmap image editor.",
    "A heatmap viewer for spreadsheets.",
    "Location is not needed for this app.",
])
def test_location_is_not_counted_when_negated_or_part_of_another_word(text):
    assert mentions(text, LOCATION) is False

@pytest.mark.parametrize("text", [
    "Turn-by-turn GPS navigation app.",
    "Free maps and directions.",
    "Share your location with friends.",
    "Not only maps, but also live traffic.",
    "Works with no internet and shows your location on the map.",
])
def test_location_is_counted_when_the_app_really_uses_it(text):
    assert mentions(text, LOCATION) is True

def test_plural_and_case_are_handled():
    assert mentions("Offline MAPS for travel", ["map"]) is True

def test_empty_text_mentions_nothing():
    assert mentions("", LOCATION) is False and mentions(None, LOCATION) is False


# ---- Phase 4 fixes: negations that reach further, cancel out, or grant permission ----
from core.text_match import find_mentions as _find

def test_wider_window_sees_a_denial_that_covers_a_whole_clause():
    sentence = "we do not sell your personal information to third parties"
    assert _find(sentence, ["third part"], prefix=True)[0][2] is False                 # default window: unchanged
    assert _find(sentence, ["third part"], prefix=True, window=8)[0][2] is True

def test_a_negation_does_not_reach_past_but_or_except():
    sentence = "we do not sell your data but we share it with advertisers"
    assert _find(sentence, ["share"], prefix=True, window=8)[0][2] is False

def test_not_hesitate_to_is_not_a_denial():
    assert _find("we will not hesitate to sell your information", ["sell"], prefix=True, window=8)[0][2] is False
    assert _find("we won't fail to share your data", ["share"], prefix=True, window=8)[0][2] is False

def test_nothing_prevents_us_from_is_not_a_denial():
    sentence = "nothing in this policy prevents us from selling your personal information"
    assert _find(sentence, ["sell"], prefix=True, window=8)[0][2] is False

def test_wont_is_a_negation():
    assert _find("we won't sell your data", ["sell"], prefix=True)[0][2] is True
