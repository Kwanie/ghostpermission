import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load_json(filename):
    with open(DATA / filename, encoding="utf-8") as file:
        return json.load(file)


PERMISSIONS = load_json("permissions.json")
PROFILES = load_json("app_profiles.json")

BG = "android.permission.ACCESS_BACKGROUND_LOCATION"
FINE = "android.permission.ACCESS_FINE_LOCATION"
CONTACTS = "android.permission.READ_CONTACTS"
MIC = "android.permission.RECORD_AUDIO"
SMS = "android.permission.READ_SMS"
INTERNET = "android.permission.INTERNET"
BOOT = "android.permission.RECEIVE_BOOT_COMPLETED"

# Risky mixes. "bonus" is extra risk points. These numbers are OUR design, not an Android standard.
COMBINATIONS = [
    {"title": "Contacts plus location in the background", "needs": [CONTACTS, BG], "bonus": 4,
     "why": "Together these could build a picture of who you know and where you go, all day."},
    {"title": "Microphone that starts by itself and reaches the internet", "needs": [MIC, BOOT, INTERNET], "bonus": 4,
     "why": "Sound could be captured from the moment the phone starts and sent out."},
    {"title": "Text messages plus internet", "needs": [SMS, INTERNET], "bonus": 3,
     "why": "Messages could be read and sent off the phone."},
]

LIMITATION = "A manifest shows what an app may ask for, not what it actually does."


def verdict_for(permission, category):
    """Return 'expected', 'plausible' or 'unexpected' for this app type."""
    profile = PROFILES.get(category)
    if profile is None:
        return "unexpected"          # unknown app type: nothing can be called expected
    if permission in profile["expected"]:
        return "expected"
    if permission in profile["plausible"]:
        return "plausible"
    return "unexpected"


from typing import List, Dict, Any

def analyze_permissions(permissions: List[str], purpose: str = "") -> List[Dict[str, Any]]:
    """Evaluates requested permissions against app description using static security rules."""
    findings = []
    purpose_lower = purpose.lower()
    perm_set = set(permissions)

    # Rule 1: Risky permission combinations
    if "android.permission.READ_CONTACTS" in perm_set and "android.permission.ACCESS_FINE_LOCATION" in perm_set:
        findings.append({
            "title": "Combined Privacy Exposure (Contacts + Location)",
            "severity": "review",
            "reason": "The app requests access to both personal contacts and precise GPS location. If combined, this data allows profiling both identity and location history.",
            "evidence": ["android.permission.READ_CONTACTS", "android.permission.ACCESS_FINE_LOCATION"]
        })

    if "android.permission.READ_SMS" in perm_set and "android.permission.INTERNET" in perm_set:
        findings.append({
            "title": "SMS and Network Exfiltration Risk",
            "severity": "high",
            "reason": "The app can read SMS messages (including 2FA tokens) and has full network access to transmit data off-device.",
            "evidence": ["android.permission.READ_SMS", "android.permission.INTERNET"]
        })

    # Rule 2: Unclear Location Access
    location_keywords = ["navigation", "map", "gps", "travel", "ride", "delivery", "location", "fitness", "weather"]
    if "android.permission.ACCESS_FINE_LOCATION" in perm_set:
        if not any(kw in purpose_lower for kw in location_keywords):
            findings.append({
                "title": "Unjustified Location Access",
                "severity": "review",
                "reason": "The app declares precise location access, but its stated purpose does not appear to require geographical position.",
                "evidence": ["android.permission.ACCESS_FINE_LOCATION"]
            })

    # Rule 3: Unjustified Camera Access
    camera_keywords = ["photo", "video", "camera", "scan", "qr", "picture"]
    if "android.permission.CAMERA" in perm_set:
        if not any(kw in purpose_lower for kw in camera_keywords) and "flashlight" not in purpose_lower:
            findings.append({
                "title": "Unjustified Camera Access",
                "severity": "review",
                "reason": "The app requests camera permissions, but no photo or video capabilities are mentioned in its description.",
                "evidence": ["android.permission.CAMERA"]
            })

    return findings