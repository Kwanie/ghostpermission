import re
import io
from typing import List
from PIL import Image

# Permission keyword mapper for screenshot OCR recognition
KEYWORD_PERM_MAP = {
    "camera": "android.permission.CAMERA",
    "location": "android.permission.ACCESS_FINE_LOCATION",
    "contacts": "android.permission.READ_CONTACTS",
    "microphone": "android.permission.RECORD_AUDIO",
    "mic": "android.permission.RECORD_AUDIO",
    "storage": "android.permission.READ_EXTERNAL_STORAGE",
    "photos": "android.permission.READ_MEDIA_IMAGES",
    "media": "android.permission.READ_MEDIA_IMAGES",
    "sms": "android.permission.READ_SMS",
    "phone": "android.permission.READ_PHONE_STATE",
    "call": "android.permission.CALL_PHONE",
    "calendar": "android.permission.READ_CALENDAR",
    "notifications": "android.permission.POST_NOTIFICATIONS",
    "bluetooth": "android.permission.BLUETOOTH_CONNECT",
    "nearby": "android.permission.BLUETOOTH_CONNECT"
}

def extract_permissions_from_image(image_bytes: bytes) -> List[str]:
    """Best-effort permission extraction from screenshot images."""
    try:
        import pytesseract # type: ignore
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img).lower()
    except Exception:
        text = ""

    detected = set()
    for keyword, perm in KEYWORD_PERM_MAP.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            detected.add(perm)

    return sorted(list(detected))