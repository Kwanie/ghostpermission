import pytest
from core.integration import analyze_app_data

def test_full_integration_pipeline():
    payload = {
        "app_name": "Simple Flashlight",
        "description": "A basic utility flashlight app to light up dark spaces.",
        "permissions": [
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.READ_CONTACTS"
        ]
    }
    
    result = analyze_app_data(payload)
    
    assert "app_name" in result
    assert result["app_name"] == "Simple Flashlight"
    assert len(result["mapped_permissions"]) == 3
    assert len(result["final_findings"]) > 0