from pathlib import Path
from core.manifest_parser import extract_permissions
from core.risk_rules import analyze_permissions

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "sample_manifests"

def run(file, category):
    return analyze_permissions(extract_permissions((SAMPLES / file).read_bytes()), category)

def test_flashlight_with_contacts_and_location_is_high():
    result = run("flashlight.xml", "flashlight")
    assert result["rating"] == "High"
    assert any("Combination" in f["title"] for f in result["findings"])

def test_navigation_app_is_low():
    assert run("navigation.xml", "navigation")["rating"] == "Low"

def test_same_permissions_different_purpose_changes_the_rating():
    # Same file, different stated purpose: context changes the answer.
    assert run("navigation.xml", "flashlight")["rating"] != run("navigation.xml", "navigation")["rating"]

def test_unknown_permission_is_reported_not_ignored():
    result = analyze_permissions(["android.permission.MADE_UP"], "flashlight")
    assert result["findings"][0]["title"] == "Unknown permission"
