from typing import List, Dict, Any
from core.state import Finding

def run_combination_analyst(permissions: List[str], mapped_perms: List[Dict[str, Any]]) -> List[Finding]:
    """Identifies risky overlapping permission patterns."""
    findings = []
    perm_set = set(permissions)
    
    # Combination: Contacts + Location + Internet
    if {"android.permission.READ_CONTACTS", "android.permission.ACCESS_FINE_LOCATION", "android.permission.INTERNET"}.issubset(perm_set):
        findings.append(Finding(
            title="High Exposure Combination (Contacts + Location + Internet)",
            severity="high",
            reason="This application requests reading contacts, fine location, and full network access simultaneously. This combination creates high data exposure potential.",
            evidence=["android.permission.READ_CONTACTS", "android.permission.ACCESS_FINE_LOCATION", "android.permission.INTERNET"],
            limitations=["Static analysis confirms capability, not intent or active data exfiltration."],
            recommendation="Restrict location access to 'Only while using the app' and revoke contacts access if unnecessary."
        ))
    # Combination: SMS + Internet
    elif {"android.permission.READ_SMS", "android.permission.INTERNET"}.issubset(perm_set):
        findings.append(Finding(
            title="SMS Exfiltration Combination",
            severity="high",
            reason="Ability to read SMS messages alongside full internet access permits remote transmission of sensitive codes.",
            evidence=["android.permission.READ_SMS", "android.permission.INTERNET"],
            limitations=["Does not inspect app binaries for actual exfiltration endpoints."],
            recommendation="Do not grant SMS access unless app primary function requires text processing."
        ))
        
    return findings