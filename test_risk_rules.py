import pytest
from core.manifest_parser import extract_permissions_from_xml
from core.risk_rules import analyze_permissions

SAMPLE_MANIFEST = b"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.flashlight">
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.READ_CONTACTS"/>
</manifest>
"""

def test_risk_rules_with_xml_parser():
    perms = extract_permissions_from_xml(SAMPLE_MANIFEST)
    assert len(perms) == 3
    
    findings = analyze_permissions(perms, purpose="A basic utility flashlight app")
    assert len(findings) >= 2
    
    titles = [f["title"] for f in findings]
    assert "Combined Privacy Exposure (Contacts + Location)" in titles
    assert "Unjustified Location Access" in titles