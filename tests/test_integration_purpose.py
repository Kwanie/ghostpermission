from types import SimpleNamespace

from core import integration


def _capture(monkeypatch):
    seen = {}

    def fake_pipeline(payload):
        seen.update(payload)
        return SimpleNamespace(model_dump=lambda: {"final_findings": [], "permissions": payload["permissions"]})

    monkeypatch.setattr(integration, "run_agent_pipeline", fake_pipeline)
    return seen


def test_a_placeholder_description_means_the_purpose_is_unknown(monkeypatch):
    _capture(monkeypatch)
    result = integration.analyze_app_data({"app_name": "X", "description": "Uploaded off-store APK file.",
                                           "permissions": ["android.permission.CAMERA"]})
    assert result["purpose_known"] is False

def test_the_store_category_reaches_the_agents_with_a_label(monkeypatch):
    seen = _capture(monkeypatch)
    payload = {"app_name": "Maps", "description": "", "genre": "Maps & Navigation",
               "permissions": ["android.permission.ACCESS_FINE_LOCATION"]}
    result = integration.analyze_app_data(payload)
    assert "[Play Store category: Maps & Navigation" in seen["description"]
    assert result["purpose_known"] is True
    assert payload["description"] == ""                    # the caller's own data is not rewritten

def test_a_written_description_is_known(monkeypatch):
    _capture(monkeypatch)
    result = integration.analyze_app_data({"app_name": "Torch", "description": "A basic flashlight and torch utility.",
                                           "permissions": ["android.permission.CAMERA"]})
    assert result["purpose_known"] is True
