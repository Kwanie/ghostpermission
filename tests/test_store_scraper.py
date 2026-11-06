from core import store_scraper as ss

GROUPS = {
    "Location": ["approximate location (network-based)", "precise location (GPS and network-based)"],
    "Contacts": ["read your contacts"],
    "Camera": ["take pictures and videos"],
    "Other": ["full network access", "run at startup", "prevent device from sleeping",
              "receive data from Internet", "install shortcuts"],
}


def _app(permissions=None, **extra):
    data = {"title": "Tool", "genre": "Tools", "permissions": permissions or []}
    data.update(extra)
    return lambda *a, **k: data


def test_missing_permissions_are_not_invented(monkeypatch):
    monkeypatch.setattr(ss, "play_app", _app())
    monkeypatch.setattr(ss, "play_permissions", lambda *a, **k: {})
    result = ss.fetch_play_store_details("com.example.tool")
    assert result["permissions"] == [] and result["permissions_available"] is False
    assert result["permissions_unmatched"] == []

def test_permissions_already_in_the_app_answer_are_kept_without_a_second_request(monkeypatch):
    def must_not_be_called(*a, **k):
        raise AssertionError("play_permissions should not be called")
    monkeypatch.setattr(ss, "play_app", _app([{"permission": "android.permission.CAMERA"}, "android.permission.INTERNET"]))
    monkeypatch.setattr(ss, "play_permissions", must_not_be_called)
    result = ss.fetch_play_store_details("com.example.tool")
    assert result["permissions"] == ["android.permission.CAMERA", "android.permission.INTERNET"]
    assert result["permissions_available"] is True

def test_google_wording_is_matched_to_android_names_and_leftovers_are_reported(monkeypatch):
    monkeypatch.setattr(ss, "play_app", _app())
    monkeypatch.setattr(ss, "play_permissions", lambda *a, **k: GROUPS)
    result = ss.fetch_play_store_details("com.example.tool")
    assert result["permissions"] == [
        "android.permission.ACCESS_COARSE_LOCATION", "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.CAMERA", "android.permission.INTERNET", "android.permission.READ_CONTACTS",
        "android.permission.RECEIVE_BOOT_COMPLETED", "android.permission.WAKE_LOCK"]
    assert result["permissions_unmatched"] == ["install shortcuts", "receive data from Internet"]
    assert result["permissions_available"] is True

def test_a_failing_permissions_request_means_no_permissions_not_a_crash(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(ss, "play_app", _app())
    monkeypatch.setattr(ss, "play_permissions", boom)
    assert ss.fetch_play_store_details("com.example.tool")["permissions_available"] is False

def test_background_location_wording_is_recognised():
    matched, unmatched = ss.map_play_permissions({"Location": ["access location in the background"]})
    assert matched == ["android.permission.ACCESS_BACKGROUND_LOCATION"] and unmatched == []

def test_app_ids_are_read_from_links_and_plain_text():
    assert ss.parse_app_id("com.innersloth.spacemafia") == "com.innersloth.spacemafia"
    assert ss.parse_app_id("https://play.google.com/store/apps/details?id=com.innersloth.spacemafia&hl=en") == "com.innersloth.spacemafia"
    assert ss.parse_app_id("  com.discord  ") == "com.discord"

def test_text_that_is_not_an_app_id_is_rejected():
    for text in ("Among Us", "javascript:alert(1)", "", "com..x", "http://evil.test/?id=a.b", "../../etc/passwd"):
        assert ss.parse_app_id(text) is None, text

def test_lookup_returns_an_error_message_instead_of_raising(monkeypatch):
    assert "does not look like" in ss.lookup_play_store_app("Among Us")["error"]
    def boom(*a, **k):
        raise RuntimeError("blocked")
    monkeypatch.setattr(ss, "play_app", boom)
    assert "Could not load" in ss.lookup_play_store_app("com.example.tool")["error"]

def test_lookup_returns_details_on_success(monkeypatch):
    monkeypatch.setattr(ss, "play_app", _app(description="A tool.", privacyPolicy="https://example.com/p"))
    monkeypatch.setattr(ss, "play_permissions", lambda *a, **k: {})
    result = ss.lookup_play_store_app("com.example.tool")
    assert "error" not in result and result["privacy_policy_url"] == "https://example.com/p"
