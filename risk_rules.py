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


def analyze_permissions(permissions, category):
    """Compare permissions with the app type. Return findings and a rating."""
    findings = []
    score = 0

    for permission in permissions:
        info = PERMISSIONS.get(permission)
        if info is None:
            findings.append({
                "title": "Unknown permission", "severity": "unknown", "evidence": [permission],
                "explanation": "This permission is not in our knowledge base yet.",
                "limitations": [LIMITATION, "We cannot assess what we do not know."],
                "recommendation": "Look it up in the official Android documentation.",
            })
            continue

        verdict = verdict_for(permission, category)
        if verdict == "expected":
            continue                                  # nothing to report
        points = info["weight"] if verdict == "unexpected" else info["weight"] / 2
        score += points
        findings.append({
            "title": info["name"] + (" - not expected" if verdict == "unexpected" else " - needs a reason"),
            "severity": "review" if verdict == "unexpected" else "low",
            "evidence": [permission],
            "explanation": info["what_it_allows"],
            "limitations": [LIMITATION],
            "recommendation": "Check the app's features and privacy policy to see why it needs this.",
        })

    for combo in COMBINATIONS:
        if all(need in permissions for need in combo["needs"]):   # are ALL of them present?
            score += combo["bonus"]
            findings.append({
                "title": "Combination: " + combo["title"], "severity": "review",
                "evidence": combo["needs"], "explanation": combo["why"],
                "limitations": [LIMITATION, "A flag means 'worth checking', not 'misuse'."],
                "recommendation": "Review whether this app really needs all of these together.",
            })

    rating = "High" if score >= 10 else "Medium" if score >= 5 else "Low"
    return {"score": score, "rating": rating, "findings": findings}
