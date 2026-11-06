import pytest
from core.orchestrator import run_agent_pipeline

def test_flashlight_suspicious_permissions():
    payload = {
        "app_name": "Simple Flashlight",
        "description": "A basic flashlight utility app to light dark spaces.",
        "permissions": [
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.READ_CONTACTS",
            "android.permission.INTERNET"
        ]
    }
    
    state = run_agent_pipeline(payload)
    
    assert len(state.mapped_permissions) == 4
    assert len(state.final_findings) > 0
    
    # Skeptical reviewer should have marked camera access as justified for flashlight
    camera_finding = next((f for f in state.final_findings if "CAMERA" in str(f.evidence)), None)
    if camera_finding:
        assert camera_finding.severity == "justified"
        assert camera_finding.reviewed_by_skeptic is True

def test_navigation_legitimate_location():
    payload = {
        "app_name": "GPS Navigator",
        "description": "Turn-by-turn map and GPS navigation app.",
        "permissions": ["android.permission.ACCESS_FINE_LOCATION"]
    }
    
    state = run_agent_pipeline(payload)
    location_finding = next((f for f in state.final_findings if "LOCATION" in str(f.evidence)), None)
    if location_finding:
        assert location_finding.severity == "justified"