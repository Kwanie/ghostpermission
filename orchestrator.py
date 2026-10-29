from typing import Dict, Any
from core.state import PermissionState, Finding
from agents.permission_mapper import run_permission_mapper
from agents.purpose_analyst import run_purpose_analyst
from agents.combination_analyst import run_combination_analyst
from agents.skeptical_reviewer import run_skeptical_reviewer
from agents.shared_llm import get_llm

def run_agent_pipeline(payload: Dict[str, Any]) -> PermissionState:
    """Runs Person 1 payload through Person 2 multi-agent workflow."""
    state = PermissionState(
        app_name=payload.get("app_name", "Unknown App"),
        description=payload.get("description", ""),
        permissions=payload.get("permissions", []),
        privacy_policy_url=payload.get("privacy_policy_url"),
        privacy_policy_text=payload.get("privacy_policy_text"),
        deterministic_findings=payload.get("deterministic_findings", [])
    )
    
    llm = get_llm()
    
    # 1. Map permissions
    state.mapped_permissions = run_permission_mapper(state.permissions, llm=llm)
    
    # 2. Analyze purpose alignment
    purpose_findings = run_purpose_analyst(state.app_name, state.description, state.mapped_permissions)
    
    # 3. Analyze risky combinations
    combo_findings = run_combination_analyst(state.permissions, state.mapped_permissions)
    
    raw_findings = purpose_findings + combo_findings
    
    # Add initial deterministic findings from P1
    for det in state.deterministic_findings:
        raw_findings.append(Finding(
            title=det.get("title", "Static Finding"),
            severity=det.get("severity", "review"),
            reason=det.get("reason", ""),
            evidence=det.get("evidence", [])
        ))
        
    state.agent_findings = raw_findings
    
    # 4. Skeptical Reviewer Auditing Stage
    state.final_findings = run_skeptical_reviewer(state.app_name, state.description, raw_findings)
    state.audit_summary = f"Audited {len(raw_findings)} initial findings. Refined severity ratings based on evidence."
    
    return state