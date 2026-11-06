from core.report_generator import get_executive_verdict, generate_pdf_report, generate_markdown_report

def finding(sev): return {"title": "t", "severity": sev, "reason": "r", "evidence": []}

def test_no_permissions_is_never_a_positive_verdict():
    v = get_executive_verdict({"permissions": [], "final_findings": []})
    assert v["safety_status"] == "NOT ENOUGH INFORMATION"
    assert "safe" not in (v["status"] + v["action"] + v["summary"]).lower()

def test_high_finding_means_think_twice():
    v = get_executive_verdict({"permissions": ["android.permission.CAMERA"], "final_findings": [finding("high")]})
    assert v["safety_status"] == "HIGH RISK" and "Think twice" in v["action"]

def test_review_finding_means_install_with_care():
    v = get_executive_verdict({"permissions": ["x"], "final_findings": [finding("review")]})
    assert v["safety_status"] == "CAUTION"

def test_no_findings_with_permissions_is_reasonable_but_not_a_guarantee():
    v = get_executive_verdict({"permissions": ["android.permission.INTERNET"], "final_findings": []})
    assert v["safety_status"] == "LOOKS REASONABLE"
    assert "not a guarantee" in v["summary"]
    assert "safe" not in v["action"].lower()

def test_no_invented_numbers():
    v = get_executive_verdict({"permissions": ["x"], "final_findings": []})
    assert v["overall_risk_score"] is None and v["expected_permissions_count"] is None

def test_a_plain_list_of_findings_still_works():
    assert get_executive_verdict([finding("high")])["safety_status"] == "HIGH RISK"

def test_reports_build_for_every_verdict_state():
    for data in ({"permissions": [], "final_findings": []},
                 {"permissions": ["x"], "final_findings": [finding("high")]},
                 {"permissions": ["x"], "final_findings": []}):
        assert generate_markdown_report({"app_name": "A"}, data)
        assert generate_pdf_report({"app_name": "A"}, data)[:4] == b"%PDF"


# ---- Phase 5: what the verdict says when we do not know what the app is for ----
def _finding(severity):
    return {"title": "Location purpose unclear", "severity": severity, "evidence": ["android.permission.ACCESS_FINE_LOCATION"]}

def test_unknown_purpose_asks_for_the_purpose_instead_of_judging():
    from core.report_generator import get_executive_verdict
    verdict = get_executive_verdict({"final_findings": [_finding("review")], "permissions": ["android.permission.ACCESS_FINE_LOCATION"],
                                     "purpose_known": False})
    assert verdict["safety_status"] == "NOT ENOUGH INFORMATION"
    assert "what this app is supposed to do" in verdict["summary"]

def test_a_high_risk_finding_still_raises_the_alarm_without_a_purpose():
    from core.report_generator import get_executive_verdict
    verdict = get_executive_verdict({"final_findings": [_finding("high")], "permissions": ["android.permission.READ_CONTACTS"],
                                     "purpose_known": False})
    assert verdict["safety_status"] == "HIGH RISK"

def test_a_known_purpose_changes_nothing():
    from core.report_generator import get_executive_verdict
    review = get_executive_verdict({"final_findings": [_finding("review")], "permissions": ["x"], "purpose_known": True})
    assert review["safety_status"] == "CAUTION"
    default = get_executive_verdict({"final_findings": [], "permissions": ["x"]})
    assert default["safety_status"] == "LOOKS REASONABLE"

def test_no_permissions_still_says_there_is_nothing_to_judge():
    from core.report_generator import get_executive_verdict
    verdict = get_executive_verdict({"final_findings": [], "permissions": [], "purpose_known": False})
    assert "permissions" in verdict["summary"] and verdict["safety_status"] == "NOT ENOUGH INFORMATION"
