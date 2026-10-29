from core.graph_risk_rules import evaluate_rules, normalize_permission
import pytest


def test_normalize_permission():
    assert normalize_permission(" android.permission.camera ") == "ANDROID.PERMISSION.CAMERA"


def test_empty_permissions_returns_no_findings():
    assert evaluate_rules([], {}) == []


def test_camera_and_audio_combination_is_flagged():
    findings = evaluate_rules([
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
    ], {})
    assert any(f["category"] == "permission_combination" for f in findings)


def test_known_sensitive_permission_uses_knowledge_base():
    kb = {"permissions": {
        "android.permission.READ_CONTACTS": {
            "description": "Read contacts",
            "risk_level": "high",
            "sensitive": True,
        }
    }}
    findings = evaluate_rules(["android.permission.READ_CONTACTS"], kb)
    assert findings
    assert findings[0]["severity"] == "high"


def test_duplicate_permissions_are_deduplicated():
    findings = evaluate_rules([
        "android.permission.CAMERA",
        "android.permission.CAMERA",
    ], {})
    ids = [f["id"] for f in findings]
    assert len(ids) == len(set(ids))


def test_string_is_not_accepted_as_permission_iterable():
    with pytest.raises(TypeError):
        evaluate_rules("android.permission.CAMERA", {})
