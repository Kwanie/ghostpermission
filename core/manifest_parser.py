import io
import os
import tempfile
import zipfile
from typing import Any, Dict, List

from defusedxml import ElementTree as ET            # a SAFE version of Python's XML reader
from defusedxml.common import DefusedXmlException   # the error it raises for dangerous files

# Compatible import handling for both androguard 3.x and 4.x
try:
    from androguard.core.bytecodes.apk import APK  # type: ignore
except ImportError:
    try:
        from androguard.core.apk import APK  # type: ignore
    except ImportError:
        APK = None

ANDROID_NS = "http://schemas.android.com/apk/res/android"

MAX_APK_BYTES = 100 * 1024 * 1024          # 100 MB
MAX_APK_ENTRIES = 50_000                   # files inside the APK
MAX_APK_UNPACKED = 2 * 1024 ** 3           # 2 GB if everything were unpacked (guards against zip bombs)


def extract_permissions_from_xml(xml_content: bytes) -> List[str]:
    """Parses raw AndroidManifest.xml bytes and extracts all declared permissions.

    Raises ValueError with a plain-language message for empty, broken or unsafe files."""
    if not xml_content or not xml_content.strip():
        raise ValueError("The file is empty.")
    try:
        root = ET.fromstring(xml_content)
    except (ET.ParseError, DefusedXmlException):
        raise ValueError("That file is not a valid, safe manifest XML.") from None

    permissions = set()
    # Standard uses-permission elements, plus the SDK 23+ conditional variant.
    for tag in ("uses-permission", "uses-permission-sdk-23"):
        for element in root.findall(tag):
            perm = element.get(f"{{{ANDROID_NS}}}name")
            if perm and perm.strip():
                permissions.add(perm.strip())
    return sorted(permissions)


def check_apk_bytes(apk_bytes: bytes) -> None:
    """Cheap safety checks BEFORE the heavy APK reader runs. Raises ValueError with a plain message."""
    if not apk_bytes:
        raise ValueError("The file is empty.")
    if len(apk_bytes) > MAX_APK_BYTES:
        raise ValueError(f"That file is too large. The limit is {MAX_APK_BYTES // (1024 * 1024)} MB.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(apk_bytes))
    except zipfile.BadZipFile:
        raise ValueError("That is not a valid APK file. An APK is a zip file, and this one could not be opened.") from None
    with archive:
        entries = archive.infolist()
        if len(entries) > MAX_APK_ENTRIES:
            raise ValueError("That APK contains an unusual number of files, so it was not opened.")
        if sum(entry.file_size for entry in entries) > MAX_APK_UNPACKED:
            raise ValueError("That APK would unpack to an unsafe size, so it was not opened.")
        if "AndroidManifest.xml" not in archive.namelist():
            raise ValueError("No AndroidManifest.xml was found inside this file, so it does not look like an APK.")


def extract_permissions_from_apk(apk_bytes: bytes) -> Dict[str, Any]:
    """Declared permissions of an APK. The file is only READ, never run.
    Raises ValueError with a plain message for anything that goes wrong."""
    if APK is None:
        raise ValueError("The APK reader (androguard) is not installed. Run: python -m pip install androguard")
    check_apk_bytes(apk_bytes)

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".apk") as temp_file:
            temp_file.write(apk_bytes)
            temp_file_path = temp_file.name
        app = APK(temp_file_path)
        package_name = app.get_package()
        return {
            "app_name": app.get_app_name() or package_name or "Uploaded APK",
            "package_name": package_name or "unknown.package",
            "permissions": sorted(set(app.get_permissions())),
            "min_sdk": app.get_min_sdk_version(),
            "target_sdk": app.get_target_sdk_version(),
        }
    except Exception as error:
        raise ValueError(f"This APK could not be read ({type(error).__name__}). "
                         f"It may be damaged or use an unsupported format.") from None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass        # Windows can hold the file for a moment; the system temp folder is cleaned later
