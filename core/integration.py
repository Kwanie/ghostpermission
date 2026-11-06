from typing import Dict, Any

from core.orchestrator import run_agent_pipeline
from core.purpose_rules import describe_for_analysis, purpose_is_known
from core.risk_rules import analyze_permissions


def analyze_app_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Master pipeline execution: runs the rule checks, then the agent pipeline.

    For Play Store apps the store category is added to the description (clearly labelled) so a navigation app
    is judged as a navigation app. If nobody told us what the app is for, the result says so
    ("purpose_known": False) and the verdict asks for it instead of guessing."""
    analysis_payload = dict(payload)
    analysis_payload["description"] = describe_for_analysis(payload)

    static_rules = analyze_permissions(
        permissions=payload.get("permissions", []),
        purpose=analysis_payload["description"],
    )
    payload["deterministic_findings"] = static_rules
    analysis_payload["deterministic_findings"] = static_rules

    final_state = run_agent_pipeline(analysis_payload)
    result = final_state.model_dump()
    result["purpose_known"] = purpose_is_known(payload)
    return result
