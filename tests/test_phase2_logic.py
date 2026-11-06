from core.state import Finding
from core.findings_utils import dedupe_findings
from agents.skeptical_reviewer import run_skeptical_reviewer
from core.integration import analyze_app_data
from core.report_generator import get_executive_verdict

P = "android.permission."
CAMERA, CONTACTS, FINE, INTERNET, SMS = P + "CAMERA", P + "READ_CONTACTS", P + "ACCESS_FINE_LOCATION", P + "INTERNET", P + "READ_SMS"

def make(title, severity, evidence):
    return Finding(title=title, severity=severity, reason="r", evidence=evidence)

def verdict_for(name, description, permissions):
    out = analyze_app_data({"app_name": name, "description": description, "permissions": permissions})
    return out, get_executive_verdict(out)

# ---------- the four apps from the review ----------
def test_flashlight_that_says_no_location_still_gets_a_location_finding():
    out, verdict = verdict_for("BrightTorch", "A simple flashlight app. No location or contacts needed.",
                               [CAMERA, CONTACTS, FINE, INTERNET])
    titles = [f["title"] for f in out["final_findings"]]
    unclear = [t.lower() for t in titles if t.startswith("Unclear Purpose")]
    assert any("location" in t for t in unclear)   # the "No location needed" trap is caught
    assert any("contacts" in t for t in unclear)
    assert verdict["safety_status"] == "HIGH RISK"

def test_navigation_app_with_only_location_and_internet_looks_reasonable():
    out, verdict = verdict_for("RoadGuide", "Free navigation and maps app with turn-by-turn GPS directions.", [FINE, INTERNET])
    assert verdict["safety_status"] == "LOOKS REASONABLE"

def test_navigation_app_that_also_reads_contacts_is_not_waved_through():
    out, verdict = verdict_for("RoadGuide", "Free navigation and maps app with turn-by-turn GPS directions.",
                               [FINE, CONTACTS, INTERNET])
    assert verdict["safety_status"] in ("HIGH RISK", "CAUTION")
    assert any("contacts" in f["title"].lower() for f in out["final_findings"])

def test_notes_app_with_sms_and_internet_stays_high():
    out, verdict = verdict_for("QuietNotes", "A notes app", [SMS, INTERNET])
    assert verdict["safety_status"] == "HIGH RISK"

def test_chat_app_that_explains_contacts_and_location_is_marked_justified_with_a_limitation():
    out, verdict = verdict_for("ChatNow", "A chat app to message friends and share your location.",
                               [CONTACTS, FINE, INTERNET])
    assert verdict["safety_status"] == "LOOKS REASONABLE"
    assert all(f["severity"] == "justified" for f in out["final_findings"])
    assert all(any("cannot verify" in l for l in f["limitations"]) for f in out["final_findings"])

# ---------- the reviewer ----------
def test_reviewer_does_not_downgrade_when_even_one_permission_is_unexplained():
    combo = make("Combo", "high", [CONTACTS, FINE, INTERNET])
    result = run_skeptical_reviewer("RoadGuide", "A navigation and maps app", [combo])[0]
    assert result.severity == "high"          # contacts are not explained by a navigation app
    assert result.reviewed_by_skeptic is True

def test_reviewer_downgrades_when_every_permission_is_explained():
    combo = make("Combo", "high", [CONTACTS, FINE, INTERNET])
    result = run_skeptical_reviewer("ChatNow", "Chat with friends and share your location", [combo])[0]
    assert result.severity == "justified"

def test_reviewer_never_uses_a_hard_coded_app_type():
    cam = make("Camera", "review", [CAMERA])
    assert run_skeptical_reviewer("X", "A flashlight", [cam])[0].severity == "justified"
    assert run_skeptical_reviewer("X", "A calculator", [cam])[0].severity == "review"

# ---------- duplicates ----------
def test_repeated_sms_findings_become_one():
    a = make("SMS and Network Exfiltration Risk", "high", [SMS, INTERNET])
    b = make("SMS Exfiltration Combination", "high", [INTERNET, SMS])
    assert len(dedupe_findings([a, b])) == 1

def test_smaller_combination_is_merged_into_the_bigger_one_and_keeps_the_stronger_severity():
    small = make("Contacts + Location", "high", [CONTACTS, FINE])
    big = make("Contacts + Location + Internet", "review", [CONTACTS, FINE, INTERNET])
    merged = dedupe_findings([small, big])
    assert len(merged) == 1
    assert len(merged[0].evidence) == 3 and merged[0].severity == "high"

def test_different_single_permissions_are_not_merged():
    a = make("Contacts", "review", [CONTACTS]); b = make("Location", "review", [FINE])
    assert len(dedupe_findings([a, b])) == 2
