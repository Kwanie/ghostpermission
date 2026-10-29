"""Deterministic, explainable permission-risk rules for GhostPermission.

These rules flag review-worthy patterns; they do NOT prove malicious behaviour.
The knowledge-base schema is intentionally flexible so Person A's permissions.json
can be adapted without changing the orchestration layer.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable, Mapping
import re


SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def normalize_permission(permission: str) -> str:
    """Normalize Android permission names without guessing missing prefixes."""
    return re.sub(r"\s+", "", str(permission or "")).strip().upper()


def _severity(value: Any, default: str = "medium") -> str:
    candidate = str(value or default).strip().lower()
    aliases = {"moderate": "medium", "warning": "medium", "severe": "high"}
    candidate = aliases.get(candidate, candidate)
    return candidate if candidate in SEVERITY_ORDER else default


def _kb_permissions(knowledge_base: Mapping[str, Any]) -> Mapping[str, Any]:
    """Accept common shapes: {permissions:{...}}, a direct mapping, or a list."""
    if not isinstance(knowledge_base, Mapping):
        return {}
    candidate = knowledge_base.get("permissions", knowledge_base)
    if isinstance(candidate, Mapping):
        return {normalize_permission(k): v for k, v in candidate.items()}
    if isinstance(candidate, list):
        result = {}
        for item in candidate:
            if isinstance(item, Mapping):
                name = item.get("name") or item.get("permission")
                if name:
                    result[normalize_permission(name)] = item
        return result
    return {}


def _metadata_for(permission: str, kb: Mapping[str, Any]) -> dict[str, Any]:
    value = kb.get(permission, {})
    if isinstance(value, str):
        return {"description": value}
    return dict(value) if isinstance(value, Mapping) else {}


def evaluate_rules(
    permissions: Iterable[str],
    knowledge_base: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate transparent permission and combination rules.

    Returns a list of dictionaries suitable for JSON serialization.
    Expected finding keys: id, category, severity, title, permissions,
    explanation, evidence, recommendation.
    """
    if permissions is None:
        raise ValueError("permissions cannot be None")
    if isinstance(permissions, (str, bytes)):
        raise TypeError("permissions must be an iterable of permission names, not a string")

    normalized = sorted({normalize_permission(p) for p in permissions if normalize_permission(p)})
    kb = _kb_permissions(knowledge_base or {})
    findings: list[dict[str, Any]] = []

    for permission in normalized:
        metadata = _metadata_for(permission, kb)
        declared_severity = _severity(metadata.get("risk_level") or metadata.get("severity"), "low")
        sensitive = bool(metadata.get("sensitive", False))
        description = str(metadata.get("description") or metadata.get("purpose") or
                          "No description is available in the local permission knowledge base.")

        if sensitive or declared_severity in {"medium", "high", "critical"}:
            findings.append({
                "id": f"PERMISSION-{permission}",
                "category": "individual_permission",
                "severity": declared_severity if declared_severity != "info" else "low",
                "title": f"Review requested permission: {permission}",
                "permissions": [permission],
                "explanation": (
                    f"The manifest requests {permission}. The local knowledge base "
                    f"describes it as: {description} This is a review signal, not proof "
                    "that the app uses the permission or misuses it."
                ),
                "evidence": [{"source": "Android manifest", "value": permission},
                             {"source": "local permission knowledge base", "value": metadata}],
                "recommendation": (
                    "Check whether this permission is necessary for the app's stated "
                    "features and verify its use in the app and privacy policy."
                ),
            })

    # Conservative, explicit combinations. These identify data-access combinations,
    # not malicious intent. Add project-specific combinations only with documented rationale.
    combination_rules = [
        {
            "permissions": {"ANDROID.PERMISSION.CAMERA", "ANDROID.PERMISSION.RECORD_AUDIO"},
            "severity": "medium",
            "title": "Camera and microphone requested together",
            "explanation": "The app requests both camera and microphone access, which can enable audio/video capture when granted and used.",
            "recommendation": "Verify that audio/video features justify both permissions and review runtime prompts and privacy disclosures.",
        },
        {
            "permissions": {"ANDROID.PERMISSION.ACCESS_FINE_LOCATION", "ANDROID.PERMISSION.INTERNET"},
            "severity": "medium",
            "title": "Precise location and internet access requested together",
            "explanation": "The app requests precise location and internet access. This combination can enable location data to be transmitted, depending on app behaviour.",
            "recommendation": "Check the app's location features, privacy policy, data destinations, and whether approximate location would suffice.",
        },
        {
            "permissions": {"ANDROID.PERMISSION.READ_CONTACTS", "ANDROID.PERMISSION.INTERNET"},
            "severity": "medium",
            "title": "Contacts and internet access requested together",
            "explanation": "The app requests access to contacts and internet access. The manifest alone cannot establish whether contacts are transmitted.",
            "recommendation": "Confirm contact access is necessary and review data handling and network behaviour.",
        },
        {
            "permissions": {"ANDROID.PERMISSION.READ_SMS", "ANDROID.PERMISSION.RECEIVE_SMS"},
            "severity": "high",
            "title": "Multiple SMS-related permissions requested",
            "explanation": "The app requests permissions related to reading and receiving SMS messages, which can expose sensitive message content or metadata when granted and used.",
            "recommendation": "Verify a legitimate SMS-related feature and assess whether less sensitive alternatives are available.",
        },
    ]
    permission_set = set(normalized)
    for rule in combination_rules:
        if rule["permissions"].issubset(permission_set):
            matched = sorted(rule["permissions"])
            findings.append({
                "id": "COMBINATION-" + "-".join(p.rsplit(".", 1)[-1] for p in matched),
                "category": "permission_combination",
                "severity": rule["severity"],
                "title": rule["title"],
                "permissions": matched,
                "explanation": rule["explanation"],
                "evidence": [{"source": "Android manifest", "value": p} for p in matched],
                "recommendation": rule["recommendation"],
            })

    # Stable ordering: highest severity first, then finding ID.
    findings.sort(key=lambda f: (-SEVERITY_ORDER[f["severity"]], f["id"]))
    return findings
