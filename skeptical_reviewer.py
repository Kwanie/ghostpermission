from typing import List, Dict, Any
from core.state import Finding

def run_skeptical_reviewer(app_name: str, description: str, findings: List[Finding]) -> List[Finding]:
    """
    Audits finding claims. If an app's description explicitly justifies a permission,
    the Skeptical Reviewer downgrades or removes false positive flags.
    """
    audited_findings = []
    desc_lower = description.lower()
    
    for finding in findings:
        audited_finding = finding.model_copy()
        audited_finding.reviewed_by_skeptic = True
        
        # Check if flashlight app legitimately needs camera flash
        if "CAMERA" in str(finding.evidence) and "flashlight" in desc_lower:
            audited_finding.severity = "safe"
            audited_finding.reason = f"Camera access flagged initially, but {app_name} is a Flashlight app which requires camera hardware access for the LED flash."
            audited_finding.limitations.append("Camera hardware permission is required by Android API for physical flash control.")
            
        # Check if navigation app legitimately needs location
        if "LOCATION" in str(finding.evidence) and any(kw in desc_lower for kw in ["map", "navigation", "gps"]):
            audited_finding.severity = "safe"
            audited_finding.reason = f"Location access is expected and aligned with {app_name}'s stated navigation functionality."
            
        audited_findings.append(audited_finding)
        
    return audited_findings