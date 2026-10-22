import pytest
from core.manifest_parser import extract_permissions

GOOD = b"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.INTERNET"/>
</manifest>"""

EVIL = b"""<?xml version="1.0"?>
<!DOCTYPE bomb [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;">]>
<manifest>&b;</manifest>"""

def test_valid_manifest_returns_sorted_unique_permissions():
    assert extract_permissions(GOOD) == ["android.permission.CAMERA", "android.permission.INTERNET"]

def test_empty_file_is_rejected():
    with pytest.raises(ValueError):
        extract_permissions(b"   ")

def test_broken_xml_is_rejected():
    with pytest.raises(ValueError):
        extract_permissions(b"<manifest><uses-permission")

def test_dangerous_entity_trick_is_rejected():
    with pytest.raises(ValueError):
        extract_permissions(EVIL)

def test_manifest_without_permissions_gives_empty_list():
    assert extract_permissions(b"<manifest></manifest>") == []
