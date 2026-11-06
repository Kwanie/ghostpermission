import io
import zipfile

import pytest

from core import manifest_parser as mp


def make_zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def complaint(callable_, *args):
    with pytest.raises(ValueError) as info:
        callable_(*args)
    return str(info.value)


def test_empty_file_is_refused():
    assert "empty" in complaint(mp.check_apk_bytes, b"")

def test_oversized_file_is_refused(monkeypatch):
    monkeypatch.setattr(mp, "MAX_APK_BYTES", 10)
    assert "too large" in complaint(mp.check_apk_bytes, make_zip({"AndroidManifest.xml": b"x" * 50}))

def test_a_file_that_is_not_a_zip_is_refused():
    assert "not a valid APK" in complaint(mp.check_apk_bytes, b"this is plain text, not an apk")

def test_a_zip_without_a_manifest_is_refused():
    assert "AndroidManifest.xml" in complaint(mp.check_apk_bytes, make_zip({"readme.txt": b"hello"}))

def test_a_zip_with_a_manifest_passes_the_checks():
    mp.check_apk_bytes(make_zip({"AndroidManifest.xml": b"x"}))

def test_too_many_files_are_refused(monkeypatch):
    monkeypatch.setattr(mp, "MAX_APK_ENTRIES", 2)
    data = make_zip({"AndroidManifest.xml": b"x", "a": b"1", "b": b"2"})
    assert "unusual number of files" in complaint(mp.check_apk_bytes, data)

def test_a_zip_bomb_is_refused_before_it_is_opened(monkeypatch):
    monkeypatch.setattr(mp, "MAX_APK_UNPACKED", 100)
    data = make_zip({"AndroidManifest.xml": b"x", "big.bin": b"0" * 5000})
    assert "unsafe size" in complaint(mp.check_apk_bytes, data)

def test_missing_apk_reader_gives_a_friendly_message(monkeypatch):
    monkeypatch.setattr(mp, "APK", None)
    assert "androguard" in complaint(mp.extract_permissions_from_apk, b"anything")

def test_reader_crash_is_turned_into_a_plain_message(monkeypatch):
    class Broken:
        def __init__(self, path):
            raise RuntimeError("secret internal detail")
    monkeypatch.setattr(mp, "APK", Broken)
    message = complaint(mp.extract_permissions_from_apk, make_zip({"AndroidManifest.xml": b"x"}))
    assert "could not be read" in message and "secret internal detail" not in message

def test_successful_read_returns_the_details(monkeypatch):
    class Fake:
        def __init__(self, path): pass
        def get_permissions(self): return ["android.permission.CAMERA", "android.permission.CAMERA", "android.permission.INTERNET"]
        def get_package(self): return "com.example.tool"
        def get_app_name(self): return "Tool"
        def get_min_sdk_version(self): return "21"
        def get_target_sdk_version(self): return "34"
    monkeypatch.setattr(mp, "APK", Fake)
    result = mp.extract_permissions_from_apk(make_zip({"AndroidManifest.xml": b"x"}))
    assert result["app_name"] == "Tool" and result["package_name"] == "com.example.tool"
    assert result["permissions"] == ["android.permission.CAMERA", "android.permission.INTERNET"]
