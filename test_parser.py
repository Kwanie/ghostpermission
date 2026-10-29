import pytest
from core.manifest_parser import extract_permissions_from_xml, extract_permissions_from_apk
from core.risk_rules import analyze_permissions

SAMPLE_MANIFEST = b"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.flashlight">
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.READ_CONTACTS"/>
</manifest>
"""

def test_extract_permissions_from_xml():
    perms = extract_permissions_from_xml(SAMPLE_MANIFEST)
    assert perms == [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.CAMERA",
        "android.permission.READ_CONTACTS"
    ]

def test_analyze_permissions_rules():
    perms = ["android.permission.READ_CONTACTS", "android.permission.ACCESS_FINE_LOCATION"]
    findings = analyze_permissions(perms, purpose="A basic utility flashlight app")
    
    assert len(findings) >= 2
    titles = [f["title"] for f in findings]
    assert "Combined Privacy Exposure (Contacts + Location)" in titles
    assert "Unjustified Location Access" in titles