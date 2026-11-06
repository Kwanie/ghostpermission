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


# ---- restored safety tests (XML bombs, empty and broken files) ----
BOMB = b"""<?xml version="1.0"?>
<!DOCTYPE bomb [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">]>
<manifest>&b;</manifest>"""

def test_dangerous_entity_trick_is_rejected():
    with pytest.raises(ValueError):
        extract_permissions_from_xml(BOMB)

def test_empty_file_is_rejected():
    with pytest.raises(ValueError):
        extract_permissions_from_xml(b"   ")

def test_broken_xml_is_rejected_with_a_plain_message():
    with pytest.raises(ValueError) as info:
        extract_permissions_from_xml(b"<manifest><uses-permission")
    assert str(info.value) == "That file is not a valid, safe manifest XML."     # no parser internals leaked

def test_manifest_without_permissions_gives_empty_list():
    assert extract_permissions_from_xml(b"<manifest></manifest>") == []

def test_sdk_23_permissions_are_found():
    xml = (b'<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
           b'<uses-permission-sdk-23 android:name="android.permission.CAMERA"/></manifest>')
    assert extract_permissions_from_xml(xml) == ["android.permission.CAMERA"]

def test_duplicates_are_removed_and_the_list_is_sorted():
    xml = (b'<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
           b'<uses-permission android:name="android.permission.INTERNET"/>'
           b'<uses-permission android:name="android.permission.CAMERA"/>'
           b'<uses-permission android:name="android.permission.CAMERA"/></manifest>')
    assert extract_permissions_from_xml(xml) == ["android.permission.CAMERA", "android.permission.INTERNET"]
