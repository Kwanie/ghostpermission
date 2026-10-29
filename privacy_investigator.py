from typing import Dict, Any, List

def analyze_privacy_policy_and_terms(policy_text: str, terms_text: str = "") -> List[Dict[str, Any]]:
    """Analyzes privacy policies and terms of conditions for concerning legal clauses."""
    combined_text = (policy_text + " " + terms_text).lower()
    clauses = []

    if not combined_text or len(combined_text) < 50:
        return [{
            "topic": "Legal Policy Disclosure",
            "summary": "No online terms or privacy policy document was retrieved for automated parsing.",
            "original_text": "N/A",
            "risk_flag": "Medium"
        }]

    # 1. Third-Party Data Sales & Monetization
    if any(k in combined_text for k in ["sell your data", "monetize", "third party partners", "third-party advertisers"]):
        clauses.append({
            "topic": "Third-Party Data Sharing & Sales",
            "summary": "The agreement allows sharing or monetizing user profile data with advertising or analytics networks.",
            "original_text": "Information may be shared with external partners for commercial or ad delivery purposes.",
            "risk_flag": "High"
        })

    # 2. Broad Content Ownership License (Terms of Conditions)
    if any(k in combined_text for k in ["royalty-free", "perpetual", "transferable license", "worldwide license"]):
        clauses.append({
            "topic": "Broad Content License Grant",
            "summary": "Terms grant the company a perpetual, royalty-free license to store, re-use, or distribute user-uploaded content.",
            "original_text": "By uploading content, you grant a worldwide, royalty-free, transferable license.",
            "risk_flag": "High"
        })

    # 3. Mandatory Binding Arbitration & Class Action Waiver
    if "arbitration" in combined_text or "class action waiver" in combined_text:
        clauses.append({
            "topic": "Binding Arbitration Clause",
            "summary": "Users waive the right to participate in class-action lawsuits or jury trials in legal disputes.",
            "original_text": "Disputes shall be resolved through individual binding arbitration rather than court proceedings.",
            "risk_flag": "Medium"
        })

    # 4. Background Tracking & Device Telemetry
    if "precise location" in combined_text or "background location" in combined_text:
        clauses.append({
            "topic": "Continuous Location Collection",
            "summary": "Discloses background device tracking even when the user is not actively interacting with the app.",
            "original_text": "Location data may be collected periodically in the background.",
            "risk_flag": "High"
        })

    if not clauses:
        clauses.append({
            "topic": "Standard Operating Terms",
            "summary": "Standard operational data collection and basic service usage terms detected.",
            "original_text": combined_text[:160] + "...",
            "risk_flag": "Safe"
        })

    return clauses