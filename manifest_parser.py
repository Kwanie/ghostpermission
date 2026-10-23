from defusedxml import ElementTree as ET          # a SAFE version of Python's XML reader
from defusedxml.common import DefusedXmlException  # the error it raises for dangerous files

# Every Android manifest labels its attributes with this "address".
ANDROID_NAME = "{http://schemas.android.com/apk/res/android}name"

# Manifests can declare permissions with either of these two tags.
PERMISSION_TAGS = ["uses-permission", "uses-permission-sdk-23"]


def extract_permissions(xml_content):
    """Read a manifest and return a sorted list of permission names."""
    if not xml_content or not xml_content.strip():
        raise ValueError("The file is empty.")

    try:
        root = ET.fromstring(xml_content)
    except (ET.ParseError, DefusedXmlException):
        raise ValueError("That file is not a valid, safe manifest XML.")

    found = set()                       # a set automatically removes duplicates
    for tag in PERMISSION_TAGS:
        for element in root.iter(tag):  # look at every tag with this name
            name = element.get(ANDROID_NAME)
            if name:
                found.add(name.strip())

    return sorted(found)
