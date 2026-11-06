"""Runs the agents in order: map, purpose, combinations, merge, review.
The same steps run either as a LangGraph workflow (like Class 3) or as a plain sequence.
Both give the same answer, and the plain sequence is the fallback if LangGraph is not installed."""
import os
from typing import Any, Dict

from agents.combination_analyst import run_combination_analyst
from agents.llm_helper import AIReport
from agents.permission_mapper import run_permission_mapper
from agents.purpose_analyst import run_purpose_analyst
from agents.shared_llm import get_llm
from agents.skeptical_reviewer import run_skeptical_reviewer
from core.findings_utils import dedupe_findings
from core.state import Finding, PermissionState


def _ai_update(state: PermissionState, report: AIReport) -> Dict[str, Any]:
    return {"ai_used": state.ai_used or report.used, "ai_notes": state.ai_notes + report.notes}


def step_permission_mapper(state: PermissionState, llm) -> Dict[str, Any]:
    return {"mapped_permissions": run_permission_mapper(state.permissions, llm=llm)}


def step_purpose_analyst(state: PermissionState, llm) -> Dict[str, Any]:
    report = AIReport()
    findings = run_purpose_analyst(state.app_name, state.description, state.mapped_permissions, llm=llm, report=report)
    return {"purpose_findings": findings, **_ai_update(state, report)}


def step_combination_analyst(state: PermissionState, llm) -> Dict[str, Any]:
    return {"combo_findings": run_combination_analyst(state.permissions, state.mapped_permissions)}


def step_merge_findings(state: PermissionState, llm) -> Dict[str, Any]:
    raw = list(state.purpose_findings) + list(state.combo_findings)
    for det in state.deterministic_findings:       # findings from the fixed rules (core/risk_rules.py)
        raw.append(Finding(
            title=det.get("title", "Static Finding"),
            severity=det.get("severity", "review"),
            reason=det.get("reason", ""),
            evidence=det.get("evidence", []),
        ))
    return {"agent_findings": dedupe_findings(raw)}


def step_skeptical_reviewer(state: PermissionState, llm) -> Dict[str, Any]:
    report = AIReport()
    final = run_skeptical_reviewer(state.app_name, state.description, state.agent_findings, llm=llm, report=report)
    summary = (f"Audited {len(state.agent_findings)} findings after removing repeats. A finding is marked justified "
               f"only when the app's description explains every permission it names.")
    return {"final_findings": final, "audit_summary": summary, **_ai_update(state, report)}


STEPS = [
    ("permission_mapper", step_permission_mapper),
    ("purpose_analyst", step_purpose_analyst),
    ("combination_analyst", step_combination_analyst),
    ("merge_findings", step_merge_findings),
    ("skeptical_reviewer", step_skeptical_reviewer),
]


def _run_sequential(state: PermissionState, llm) -> PermissionState:
    for _, step in STEPS:
        state = state.model_copy(update=step(state, llm))
    return state


def _run_graph(state: PermissionState, llm) -> PermissionState:
    from langgraph.graph import END, START, StateGraph      # raises ImportError if not installed

    graph = StateGraph(PermissionState)
    for name, step in STEPS:
        graph.add_node(name, (lambda fn: (lambda s: fn(s, llm)))(step))
    graph.add_edge(START, STEPS[0][0])
    for (a, _), (b, _) in zip(STEPS, STEPS[1:]):
        graph.add_edge(a, b)
    graph.add_edge(STEPS[-1][0], END)

    result = graph.compile().invoke(state)
    return result if isinstance(result, PermissionState) else PermissionState.model_validate(result)


def run_agent_pipeline(payload: Dict[str, Any], llm="auto", use_graph=None) -> PermissionState:
    """
    llm: "auto" (default) picks the model from the .env file; None turns AI off; or pass a model.
    use_graph: True/False to force LangGraph on or off. By default it is on (set GHOST_USE_LANGGRAPH=0 to turn off).
    """
    state = PermissionState(
        app_name=payload.get("app_name", "Unknown App"),
        description=payload.get("description", ""),
        permissions=payload.get("permissions", []),
        privacy_policy_url=payload.get("privacy_policy_url"),
        privacy_policy_text=payload.get("privacy_policy_text"),
        deterministic_findings=payload.get("deterministic_findings", []),
    )
    if isinstance(llm, str) and llm == "auto":
        llm = get_llm()

    if use_graph is None:
        use_graph = os.getenv("GHOST_USE_LANGGRAPH", "1") != "0"
    if use_graph:
        try:
            return _run_graph(state, llm)
        except ImportError:
            pass                                    # LangGraph is not installed: use the plain sequence
        except Exception as error:                  # a graph problem must not stop the analysis
            state = state.model_copy(update={"ai_notes": [f"The workflow graph failed ({type(error).__name__}); "
                                                          f"the plain workflow was used instead."]})
    return _run_sequential(state, llm)
