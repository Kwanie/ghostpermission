"""Where did these permissions come from, and how far can we trust them? Shown on the results page."""

SOURCES = {
    "play_store": ("the Google Play listing",
                   "Google Play shows what the app asks for. The list can be incomplete or out of date, and we match "
                   "Google's wording to Android permission names ourselves, so something may be missing."),
    "apk": ("the APK file you uploaded",
            "These are the permissions declared inside that file. Another version of the app may ask for different ones."),
    "xml": ("the manifest file you uploaded", "These are the permissions declared in that file only."),
    "manual": ("the permissions you chose by hand", "The result depends entirely on what you entered."),
    "screenshot": ("a screenshot you uploaded",
                   "We read the words in the picture and you confirmed the permissions. Screenshots show permission "
                   "groups, not exact permissions, so treat this as an approximation."),
}


def describe_source(source_key, payload=None):
    """Returns (label, caveat) in plain words."""
    label, caveat = SOURCES.get(source_key, ("the information you gave us", "We cannot check where it came from."))
    unmatched = (payload or {}).get("permissions_unmatched") or []
    if unmatched:
        shown = "; ".join(unmatched[:5]) + (" ..." if len(unmatched) > 5 else "")
        caveat += f" {len(unmatched)} item(s) in Google's wording could not be matched and are not analysed: {shown}."
    return label, caveat
