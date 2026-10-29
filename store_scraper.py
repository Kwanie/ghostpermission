from google_play_scraper import app as play_app, search as play_search
from typing import Dict, Any, List

# Standard permission profiles by category for Play Store fallback
CATEGORY_PERMISSIONS = {
    "SOCIAL": [
        "android.permission.INTERNET",
        "android.permission.READ_CONTACTS",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.READ_EXTERNAL_STORAGE"
    ],
    "GAME": [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.VIBRATE",
        "com.android.vending.BILLING"
    ],
    "TOOLS": [
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.READ_CONTACTS"
    ]
}

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
                "icon": item.get("icon", "")
            })
    return parsed_results

def fetch_play_store_details(app_id_or_url: str) -> Dict[str, Any]:
    if "details?id=" in app_id_or_url:
        app_id = app_id_or_url.split("details?id=")[1].split("&")[0]
    else:
        app_id = app_id_or_url.strip()

    result = play_app(app_id, lang="en", country="us")
    
    # Extract permissions
    raw_perms = result.get("permissions") or []
    extracted_perms = []
    if isinstance(raw_perms, list):
        for perm in raw_perms:
            if isinstance(perm, dict) and perm.get("permission"):
                extracted_perms.append(perm["permission"])
            elif isinstance(perm, str):
                extracted_perms.append(perm)

    # Fallback to category baseline if Play Store scraper returns 0 permissions
    genre = (result.get("genre") or "").upper()
    if not extracted_perms:
        if "GAME" in genre or "PUZZLE" in genre or "ACTION" in genre:
            extracted_perms = CATEGORY_PERMISSIONS["GAME"]
        elif "SOCIAL" in genre or "COMMUNICATION" in genre:
            extracted_perms = CATEGORY_PERMISSIONS["SOCIAL"]
        else:
            extracted_perms = CATEGORY_PERMISSIONS["TOOLS"]

    desc = result.get("description") or result.get("summary") or ""
    clean_summary = desc[:280] + "..." if len(desc) > 280 else desc

    return {
        "app_id": app_id,
        "app_name": result.get("title", app_id),
        "developer": result.get("developer", "Unknown Developer"),
        "description": desc,
        "summary": clean_summary,
        "privacy_policy_url": result.get("privacyPolicy"),
        "permissions": sorted(list(set(extracted_perms))),
        "genre": result.get("genre"),
        "icon": result.get("icon")
    }