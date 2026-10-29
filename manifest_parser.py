import xml.etree.ElementTree as ET
import tempfile
import os
from typing import List, Dict, Any

# Compatible import handling for both androguard 3.x and 4.x
try:
    from androguard.core.bytecodes.apk import APK  # type: ignore
except ImportError:
    try:
        from androguard.core.apk import APK  # type: ignore
    except ImportError:
        APK = None

ANDROID_NS = "http://schemas.android.com/apk/res/android"

def extract_permissions_from_xml(xml_content: bytes) -> List[str]:
    """Parses raw AndroidManifest.xml bytes and extracts all declared permissions."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid Manifest XML: {str(e)}")
        
    permissions = set()
    
    # Check standard uses-permission elements
    for element in root.findall("uses-permission"):
        perm = element.get(f"{{{ANDROID_NS}}}name")
        if perm:
            permissions.add(perm.strip())
            
    # Check SDK 23+ conditional uses-permission-sdk-23 elements
    for element in root.findall("uses-permission-sdk-23"):
        perm = element.get(f"{{{ANDROID_NS}}}name")
        if perm:
            permissions.add(perm.strip())
            
    return sorted(list(permissions))

def extract_permissions_from_apk(apk_bytes: bytes) -> Dict[str, Any]:
    if APK is None:
        raise ImportError("androguard is not installed. Run 'pip install androguard'.")
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".apk") as temp_file:
        temp_file.write(apk_bytes)
        temp_file_path = temp_file.name

    try:
        app = APK(temp_file_path)
        permissions = sorted(list(set(app.get_permissions())))
        package_name = app.get_package()
        app_name = app.get_app_name()
        
        return {
            "app_name": app_name or package_name or "Uploaded APK",
            "package_name": package_name or "unknown.package",
            "permissions": permissions,
            "min_sdk": app.get_min_sdk_version(),
            "target_sdk": app.get_target_sdk_version()
        }
    except Exception as e:
        raise ValueError(f"Failed to unpack APK file: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)