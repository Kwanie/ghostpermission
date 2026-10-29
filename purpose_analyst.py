from typing import List, Dict, Any
from core.state import Finding
from agents.shared_llm import get_llm

def run_purpose_analyst(app_name: str, description: str, mapped_perms: List[Dict[str, Any]]) -> List[Finding]:
    """Analyzes whether requested permissions match stated app functionality."""
    findings = []
    desc_lower = description.lower()
    
    for item in mapped_perms:
        perm = item["permission"]
        risk = item.get("risk_level", "Low")
        
        # Static heuristic check fallback
        if "LOCATION" in perm and not any(k in desc_lower for k in ["map", "nav", "location", "gps", "ride"]):
            findings.append(Finding(
                title=f"Unclear Purpose: {item['display_name']}",
                severity="review",
                reason=f"{app_name} requests location access, but its description does not explain why location is required.",
                evidence=[perm],
                limitations=["The manifest declares access capability but cannot confirm actual background tracking."],
                recommendation="Verify whether location services are required for main app features."
            ))
        elif "CONTACTS" in perm and not any(k in desc_lower for k in ["chat", "social", "message", "share", "invite"]):
            findings.append(Finding(
                title=f"Unclear Purpose: {item['display_name']}",
                severity="review",
                reason=f"{app_name} requests contact reading permissions, but lacks social or messaging functionality in its description.",
                evidence=[perm],
                limitations=["Manifest presence does not prove contact transmission."],
                recommendation="Review contact permissions in Android Settings."
            ))
            
    return findings