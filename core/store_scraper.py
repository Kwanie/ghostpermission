import re
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

from google_play_scraper import app as play_app, search as play_search

try:
    from google_play_scraper import permissions as play_permissions
except ImportError:          # very old library versions
    play_permissions = None

APP_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")
P = "android.permission."

# Google Play describes permissions in everyday words ("read your contacts"). We match common wordings to
# Android's own names. This is a best effort: wording we cannot match is REPORTED, never guessed.
PLAY_WORDING = [
    (r"location.{0,40}background|background.{0,40}location", [P + "ACCESS_BACKGROUND_LOCATION"]),
    (r"precise location|\bgps\b", [P + "ACCESS_FINE_LOCATION"]),
    (r"approximate location", [P + "ACCESS_COARSE_LOCATION"]),
    (r"read your contacts|read contacts", [P + "READ_CONTACTS"]),
    (r"modify your contacts|write contacts", [P + "WRITE_CONTACTS"]),
    (r"find accounts on the device|get accounts", [P + "GET_ACCOUNTS"]),
    (r"take pictures|record video|\bcamera\b", [P + "CAMERA"]),
    (r"record audio|microphone", [P + "RECORD_AUDIO"]),
    (r"read the contents of your .*storage", [P + "READ_EXTERNAL_STORAGE"]),
    (r"modify or delete the contents of your .*storage", [P + "WRITE_EXTERNAL_STORAGE"]),
    (r"read your text messages|read text messages", [P + "READ_SMS"]),
    (r"receive text messages", [P + "RECEIVE_SMS"]),
    (r"send sms|send text messages", [P + "SEND_SMS"]),
    (r"directly call phone numbers", [P + "CALL_PHONE"]),
    (r"read phone status", [P + "READ_PHONE_STATE"]),
    (r"read (your )?call log", [P + "READ_CALL_LOG"]),
    (r"full network access", [P + "INTERNET"]),
    (r"view network connections", [P + "ACCESS_NETWORK_STATE"]),
    (r"view wi-?fi connections", [P + "ACCESS_WIFI_STATE"]),
    (r"connect and disconnect from wi-?fi", [P + "CHANGE_WIFI_STATE"]),
    (r"run at startup", [P + "RECEIVE_BOOT_COMPLETED"]),
    (r"prevent (the )?device from sleeping", [P + "WAKE_LOCK"]),
    (r"control vibration", [P + "VIBRATE"]),
    (r"draw over other apps|appear on top of other apps", [P + "SYSTEM_ALERT_WINDOW"]),
    (r"control flashlight", [P + "FLASHLIGHT"]),
    (r"read calendar events", [P + "READ_CALENDAR"]),
    (r"add or modify calendar events", [P + "WRITE_CALENDAR"]),
    (r"pair with bluetooth devices", [P + "BLUETOOTH"]),
    (r"change your audio settings", [P + "MODIFY_AUDIO_SETTINGS"]),
]


def parse_app_id(app_id_or_url: str):
    """A Google Play package name from a link or plain text, or None if it does not look like one."""
    text = str(app_id_or_url or "").strip()
    if not text:
        return None
    if "details?id=" in text or "play.google.com" in text:
        ids = parse_qs(urlparse(text).query).get("id")
        text = ids[0].strip() if ids else ""
    return text if APP_ID_PATTERN.match(text) else None


def map_play_permissions(groups) -> Tuple[List[str], List[str]]:
    """Turn Google Play's wording into Android permission names.
    Returns (matched names, wording we could not match)."""
    labels: List[str] = []
    if isinstance(groups, dict):
        for items in groups.values():
            labels.extend(str(i) for i in (items if isinstance(items, list) else [items]))
    elif isinstance(groups, list):
        labels.extend(str(i) for i in groups)

    matched, unmatched = set(), []
    for label in labels:
        lowered = label.lower()
        names = [n for pattern, perms in PLAY_WORDING if re.search(pattern, lowered) for n in perms]
        if names:
            matched.update(names)
        else:
            unmatched.append(label.strip())
    return sorted(matched), sorted(set(unmatched))


def search_play_store_apps(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        return []
    try:
        results = play_search(query.strip(), lang="en", country="us", n_hits=limit)
    except Exception:
        return []

    parsed_results = []
    for item in results:
        app_id = item.get("appId") or item.get("app_id") or item.get("id") or item.get("package")
        if app_id:
            parsed_results.append({
                "app_id": str(app_id),
                "title": item.get("title", "Unknown App"),
                "developer": item.get("developer", "Unknown Developer"),
                "icon": item.get("icon", ""),
            })
    return parsed_results


def fetch_play_store_details(app_id_or_url: str) -> Dict[str, Any]:
    """Details for one app. Raises ValueError for text that is not an app address; network errors pass through."""
    app_id = parse_app_id(app_id_or_url)
    if app_id is None:
        raise ValueError("That does not look like a Google Play link or app ID (for example com.example.app).")

    result = play_app(app_id, lang="en", country="us")

    extracted_perms: List[str] = []
    raw_perms = result.get("permissions") or []
    if isinstance(raw_perms, list):
        for perm in raw_perms:
            if isinstance(perm, dict) and perm.get("permission"):
                extracted_perms.append(perm["permission"])
            elif isinstance(perm, str):
                extracted_perms.append(perm)

    # The app() call does not list permissions. They come from a separate Google Play request, in everyday
    # wording, which we match to Android names (and report what we could not match).
    unmatched: List[str] = []
    if not extracted_perms and play_permissions is not None:
        try:
            groups = play_permissions(app_id, lang="en", country="us")
        except Exception:
            groups = {}
        extracted_perms, unmatched = map_play_permissions(groups)

    desc = result.get("description") or result.get("summary") or ""
    clean_summary = desc[:280] + "..." if len(desc) > 280 else desc
    return {
        "app_id": app_id,
        "app_name": result.get("title", app_id),
        "developer": result.get("developer", "Unknown Developer"),
        "description": desc,
        "summary": clean_summary,
        "privacy_policy_url": result.get("privacyPolicy"),
        "permissions": sorted(set(extracted_perms)),
        # No made-up fallback: if we have nothing, we say so honestly.
        "permissions_available": len(extracted_perms) > 0,
        "permissions_unmatched": unmatched,
        "genre": result.get("genre"),
        "icon": result.get("icon"),
    }


def lookup_play_store_app(app_id_or_url: str) -> Dict[str, Any]:
    """Like fetch_play_store_details, but never raises: on a problem it returns {"error": "plain message"}."""
    try:
        return fetch_play_store_details(app_id_or_url)
    except ValueError as problem:
        return {"error": str(problem)}
    except Exception:
        return {"error": "Could not load that app from Google Play. It may not exist, or Google Play could not "
                         "be reached. You can upload its manifest or APK instead."}
