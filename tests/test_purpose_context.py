from core.purpose_rules import (describe_for_analysis, is_informative_description, permission_justified,
                                purpose_is_known)

CONTACTS = "android.permission.READ_CONTACTS"
FINE = "android.permission.ACCESS_FINE_LOCATION"
SMS = "android.permission.READ_SMS"


def test_placeholder_text_says_nothing_about_the_purpose():
    for text in ("Uploaded off-store APK file.", "A simple utility.", "", None, "(none)", "App"):
        assert is_informative_description(text) is False, text

def test_a_real_description_counts():
    assert is_informative_description("A basic flashlight and torch utility.") is True

def test_store_category_fills_in_a_missing_description():
    assert purpose_is_known({"description": "", "genre": "Maps & Navigation"}) is True
    assert purpose_is_known({"description": "", "genre": "Tools"}) is False
    assert purpose_is_known({"description": "Turn-by-turn directions for drivers.", "genre": "Tools"}) is True

def test_category_hint_is_added_with_a_clear_label():
    text = describe_for_analysis({"description": "Plan trips.", "genre": "Travel & Local"})
    assert text.startswith("Plan trips.") and "[Play Store category: Travel & Local" in text

def test_vague_categories_add_nothing():
    assert describe_for_analysis({"description": "Plan trips.", "genre": "Tools"}) == "Plan trips."

def test_navigation_category_explains_location_but_not_contacts():
    text = describe_for_analysis({"description": "", "genre": "Maps & Navigation"})
    assert permission_justified(FINE, text) is True
    assert permission_justified(CONTACTS, text) is False

def test_no_category_ever_explains_reading_text_messages():
    for genre in ("Communication", "Social", "Dating"):
        text = describe_for_analysis({"description": "", "genre": genre})
        assert permission_justified(SMS, text) is False, genre
