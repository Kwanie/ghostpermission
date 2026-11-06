"""One shared place that says which words in an app description justify which permission."""
from core.text_match import mentions

FINE = "android.permission.ACCESS_FINE_LOCATION"
COARSE = "android.permission.ACCESS_COARSE_LOCATION"
CONTACTS = "android.permission.READ_CONTACTS"
CAMERA = "android.permission.CAMERA"
MIC = "android.permission.RECORD_AUDIO"

JUSTIFICATIONS = {
    "location": {
        "label": "location",
        "permissions": [FINE, COARSE],
        "keywords": ["map", "navigation", "navigate", "gps", "location", "ride", "taxi", "delivery",
                     "travel", "weather", "fitness", "running", "cycling", "nearby", "directions"],
    },
    "contacts": {
        "label": "contacts",
        "permissions": [CONTACTS],
        "keywords": ["chat", "message", "messaging", "social", "friend", "invite", "call",
                     "dialer", "phonebook", "contacts"],
    },
    "camera": {
        "label": "camera",
        "permissions": [CAMERA],
        "keywords": ["camera", "photo", "video", "scan", "qr", "picture", "selfie", "flashlight", "torch"],
    },
    "microphone": {
        "label": "microphone",
        "permissions": [MIC],
        "keywords": ["voice", "record", "recorder", "audio", "call", "video", "meeting", "speech",
                     "translate", "podcast"],
    },
    "sms": {
        "label": "text messages",
        "permissions": ["android.permission.READ_SMS", "android.permission.SEND_SMS",
                        "android.permission.RECEIVE_SMS"],
        "keywords": ["sms", "text message", "messaging", "verification code", "otp"],
    },
}


def group_for(permission):
    for group in JUSTIFICATIONS.values():
        if permission in group["permissions"]:
            return group
    return None


def permission_justified(permission, description):
    """True: the description explains it. False: it does not. None: we have no rule for it."""
    group = group_for(permission)
    if group is None:
        return None
    return mentions(description, group["keywords"])


# ---------------------------------------------------------------------------------------------------
# What do we know about the app's purpose?
# ---------------------------------------------------------------------------------------------------
import re

# Google Play's own category can stand in for a missing description. Only categories where a sensitive
# permission is normal are listed. "Tools", "Games" and similar say nothing, so they are left out.
# Text messages are deliberately NOT implied by any category.
GENRE_HINTS = {
    "Maps & Navigation": "maps navigation gps directions location",
    "Travel & Local": "travel maps location",
    "Weather": "weather location",
    "Auto & Vehicles": "navigation maps location",
    "Food & Drink": "food delivery location maps",
    "Health & Fitness": "fitness running cycling location",
    "Social": "chat message friends contacts",
    "Dating": "chat message friends nearby location",
    "Communication": "message chat call contacts voice",
    "Photography": "camera photo video",
    "Video Players & Editors": "video camera",
    "Music & Audio": "audio record",
}

# Placeholder text that means "nobody told us what the app is for".
PLACEHOLDER_DESCRIPTIONS = {"uploaded off-store apk file.", "a simple utility.",
                            "directly extracted android application package.", "(none)", ""}


def is_informative_description(text):
    """True if the text actually says something about what the app does."""
    cleaned = " ".join(str(text or "").split()).lower()
    return cleaned not in PLACEHOLDER_DESCRIPTIONS and len(re.findall(r"[a-z]{2,}", cleaned)) >= 3


def describe_for_analysis(payload):
    """The description plus, for Play Store apps, a clearly labelled line about the store category."""
    description = payload.get("description") or ""
    genre = payload.get("genre")
    hint = GENRE_HINTS.get(genre)
    if hint:
        description += f"\n[Play Store category: {genre}. Typical uses: {hint}.]"
    return description


def purpose_is_known(payload):
    return is_informative_description(payload.get("description")) or payload.get("genre") in GENRE_HINTS
