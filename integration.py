from typing import Dict, Any
from core.risk_rules import analyze_permissions
from core.orchestrator import run_agent_pipeline

def analyze_app_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Master pipeline execution: runs P1 rules then passes payload to P2 agent pipeline."""
    # Ensure static risk rules are evaluated
    static_rules = analyze_permissions(
        permissions=payload.get("permissions", []),
        purpose=payload.get("description", "")
    )
    payload["deterministic_findings"] = static_rules
    
    # Run Person 2 pipeline
    final_state = run_agent_pipeline(payload)
    return final_state.model_dump()