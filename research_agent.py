"""Finding and reading privacy policies. Same function names as before, with safer behaviour."""
import re
from typing import Dict, List, Optional

from core.policy_analysis import TOPICS, analyze_policy
from core.policy_fetch import UnsafeAddress, check_url, fetch_policy_text

DEFAULT_RISK_KEYWORDS = [
    "sell", "sold", "third party", "third-party", "marketing", "affiliates",
    "biometric", "location", "track", "arbitration", "retain", "indefinitely",
    "data broker", "advertising ID", "profiling", "share your data"
]
HIGH_KEYWORDS = {"sell", "sold", "data broker", "biometric", "arbitration"}


def validate_url(url: str) -> bool:
    """A QUICK format check only: is it text that starts with http:// or https://?
    It does NOT make an address safe. Use is_safe_public_url() or fetch_policy_text() for that."""
    if not url or not isinstance(url, str):
        return False
    url_clean = url.strip().lower()
    return url_clean.startswith("http://") or url_clean.startswith("https://")


def is_safe_public_url(url: str) -> bool:
    """True only for a normal public web address (never localhost, private networks or odd ports)."""
    try:
        check_url(url)
        return True
    except UnsafeAddress:
        return False


def find_privacy_policy_url(app_details_or_url) -> Optional[str]:
    """Extracts or validates a privacy policy URL from store metadata or user input."""
    if not app_details_or_url:
        return None

    if isinstance(app_details_or_url, dict):
        url = app_details_or_url.get("privacy_policy") or app_details_or_url.get("privacy_policy_url")
        return url if validate_url(url) else None

    if validate_url(str(app_details_or_url)):
        return str(app_details_or_url)

    return None


def scrape_policy_text(url_or_text: str, max_bytes: int = 500_000) -> Dict[str, str]:
    """
    Fetches policy text safely (public addresses only, size and time limits, redirects re-checked),
    or treats the input as pasted text if it is not a web address.
    """
    if not url_or_text or not url_or_text.strip():
        return {"source": "None", "text": "", "error": "No input provided"}

    if not validate_url(url_or_text):
        return {"source": "Pasted Policy Text", "text": str(url_or_text)[:max_bytes]}

    fetched = fetch_policy_text(url_or_text.strip())
    result = {"source": fetched["final_url"], "text": fetched["text"][:max_bytes],
              "truncated": fetched["truncated"] or len(fetched["text"]) > max_bytes}
    if not fetched["ok"]:
        result["error"] = fetched["error"]
    return result


def find_exact_policy_quotes(policy_text: str, keywords: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Real sentences from the policy about risky topics. Handles word forms ("selling"), ignores
    negated statements ("we do not sell"), and keeps long sentences. Newest code lives in
    core/policy_analysis.py; this keeps the old return shape.
    """
    if not policy_text:
        return []
    topics = TOPICS
    if keywords:
        topics = [{"name": kw.capitalize(), "kind": "concern",
                   "risk": "High" if kw.lower() in HIGH_KEYWORDS else "Medium", "triggers": [kw]} for kw in keywords]
    report = analyze_policy(policy_text, topics=topics, min_chars=0)
    quotes = [{"topic": c["keyword"].capitalize() if not keywords else c["topic"],
               "original_text": c["original_text"], "risk_flag": c["risk_flag"]}
              for c in report["clauses"] if c["kind"] == "concern"]
    return quotes[:6]


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def verify_quote_in_policy(quote: str, policy_text: str) -> bool:
    """Verifies that an extracted quote actually exists verbatim inside the policy document
    (ignoring differences in spacing and line breaks)."""
    if not quote or not policy_text:
        return False
    return _squash(quote) in _squash(policy_text)
