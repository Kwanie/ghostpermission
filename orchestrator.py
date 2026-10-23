"""LangGraph orchestration for GhostPermission.

The graph accepts functions as dependencies so it can integrate with Person A/B's
actual code without copying their implementation into this file. See README.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from langgraph.graph import StateGraph, START, END

from core.state import GhostState
from core.graph_risk_rules import evaluate_rules
from core.integration import call_parser


Parser = Callable[..., Any]
Agent = Callable[..., Any]


def _append_error(state: GhostState, component: str, exc: Exception) -> dict[str, Any]:
    errors = list(state.get("errors", []))
    errors.append({
        "component": component,
        "type": type(exc).__name__,
        "message": "The component failed. Check local server logs for diagnostic details; secrets are not included in this report.",
    })
    return {"errors": errors}


def _parse_result(value: Any) -> list[str]:
    """Normalize common parser returns into a list of permission strings."""
    if isinstance(value, Mapping):
        value = value.get("permissions", value.get("requested_permissions", []))
    if not isinstance(value, (list, tuple, set)):
        raise TypeError(
            "Parser must return a list of permission names or a mapping containing 'permissions'. "
            f"Received {type(value).__name__}."
        )
    permissions = []
    for item in value:
        if isinstance(item, str) and item.strip():
            permissions.append(item.strip())
        elif isinstance(item, Mapping):
            name = item.get("name") or item.get("permission")
            if name:
                permissions.append(str(name).strip())
    return sorted(set(permissions))


def _call_agent(agent: Agent | None, **kwargs: Any) -> Any:
    if agent is None:
        return {"status": "skipped", "reason": "No agent function was configured."}
    return agent(**kwargs)


def build_ghost_graph(
    *,
    parser_fn: Parser,
    knowledge_base: Mapping[str, Any],
    permission_mapper_fn: Agent | None = None,
    purpose_analyst_fn: Agent | None = None,
    combination_analyst_fn: Agent | None = None,
    skeptical_reviewer_fn: Agent | None = None,
    rules_fn: Callable[..., list[dict[str, Any]]] = evaluate_rules,
):
    """Build and compile the workflow.

    parser_fn may accept manifest_path=... or manifest_xml=...; the builder
    chooses based on the state supplied at invocation time. Agent functions
    should accept keyword arguments described in README.md.
    """
    def parse_node(state: GhostState) -> dict[str, Any]:
        try:
            if state.get("manifest_xml") is not None:
                raw = call_parser(parser_fn, manifest_xml=state["manifest_xml"])
            elif state.get("manifest_path"):
                raw = call_parser(parser_fn, manifest_path=state["manifest_path"])
            else:
                raise ValueError("Provide either manifest_path or manifest_xml.")
            return {"permissions": _parse_result(raw)}
        except Exception as exc:
            return _append_error(state, "manifest_parser", exc)

    def rules_node(state: GhostState) -> dict[str, Any]:
        if state.get("errors"):
            return {"rule_findings": []}
        try:
            # Prefer a non-empty KB supplied in state; otherwise use the KB
            # passed to build_ghost_graph. This avoids an empty CLI state value
            # accidentally shadowing the loaded local permission database.
            state_kb = state.get("knowledge_base")
            active_kb = state_kb if state_kb else knowledge_base
            return {"rule_findings": rules_fn(
                state.get("permissions", []), active_kb
            )}
        except Exception as exc:
            return _append_error(state, "risk_rules", exc)

    def mapper_node(state: GhostState) -> dict[str, Any]:
        if state.get("errors"):
            return {"permission_analysis": {"status": "skipped", "reason": "Earlier step failed."}}
        try:
            result = _call_agent(
                permission_mapper_fn,
                permissions=state.get("permissions", []),
                knowledge_base=state.get("knowledge_base", {}),
                rule_findings=state.get("rule_findings", []),
                app_name=state.get("app_name", ""),
                app_description=state.get("app_description", ""),
            )
            return {"permission_analysis": result}
        except Exception as exc:
            return {**_append_error(state, "permission_mapper", exc),
                    "permission_analysis": {"status": "error", "message": "The agent failed. Check local server logs for diagnostic details; secrets are not included in this report."}}

    def purpose_node(state: GhostState) -> dict[str, Any]:
        if state.get("errors"):
            return {"purpose_analysis": {"status": "skipped", "reason": "Earlier step failed."}}
        try:
            result = _call_agent(
                purpose_analyst_fn,
                permissions=state.get("permissions", []),
                knowledge_base=state.get("knowledge_base", {}),
                app_name=state.get("app_name", ""),
                app_description=state.get("app_description", ""),
                permission_analysis=state.get("permission_analysis"),
                rule_findings=state.get("rule_findings", []),
            )
            return {"purpose_analysis": result}
        except Exception as exc:
            return {**_append_error(state, "purpose_analyst", exc),
                    "purpose_analysis": {"status": "error", "message": "The agent failed. Check local server logs for diagnostic details; secrets are not included in this report."}}

    def combination_node(state: GhostState) -> dict[str, Any]:
        if state.get("errors"):
            return {"combination_analysis": {"status": "skipped", "reason": "Earlier step failed."}}
        try:
            result = _call_agent(
                combination_analyst_fn,
                permissions=state.get("permissions", []),
                knowledge_base=state.get("knowledge_base", {}),
                rule_findings=state.get("rule_findings", []),
                permission_analysis=state.get("permission_analysis"),
                purpose_analysis=state.get("purpose_analysis"),
            )
            return {"combination_analysis": result}
        except Exception as exc:
            return {**_append_error(state, "combination_analyst", exc),
                    "combination_analysis": {"status": "error", "message": "The agent failed. Check local server logs for diagnostic details; secrets are not included in this report."}}

    def reviewer_node(state: GhostState) -> dict[str, Any]:
        if state.get("errors"):
            return {"skeptical_review": {"status": "skipped", "reason": "Earlier step failed."}}
        try:
            result = _call_agent(
                skeptical_reviewer_fn,
                permissions=state.get("permissions", []),
                knowledge_base=state.get("knowledge_base", {}),
                rule_findings=state.get("rule_findings", []),
                permission_analysis=state.get("permission_analysis"),
                purpose_analysis=state.get("purpose_analysis"),
                combination_analysis=state.get("combination_analysis"),
            )
            return {"skeptical_review": result}
        except Exception as exc:
            return {**_append_error(state, "skeptical_reviewer", exc),
                    "skeptical_review": {"status": "error", "message": "The agent failed. Check local server logs for diagnostic details; secrets are not included in this report."}}

    def report_node(state: GhostState) -> dict[str, Any]:
        findings = list(state.get("rule_findings", []))
        severity_rank = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        highest = max((str(f.get("severity", "info")).lower() for f in findings),
                      key=lambda s: severity_rank.get(s, 0), default="info")
        report = {
            "product": "GhostPermission",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "app_name": state.get("app_name") or "Unknown Android app",
            "permissions_count": len(state.get("permissions", [])),
            "permissions": state.get("permissions", []),
            "highest_rule_severity": highest,
            "rule_findings": findings,
            "permission_analysis": state.get("permission_analysis"),
            "purpose_analysis": state.get("purpose_analysis"),
            "combination_analysis": state.get("combination_analysis"),
            "skeptical_review": state.get("skeptical_review"),
            "errors": state.get("errors", []),
            "interpretation_limit": (
                "Manifest permissions show what an app requests, not proof of actual runtime "
                "use or malicious intent. Findings require contextual verification."
            ),
        }
        return {"report": report}

    builder = StateGraph(GhostState)
    builder.add_node("parse_manifest", parse_node)
    builder.add_node("risk_rules", rules_node)
    builder.add_node("permission_mapper", mapper_node)
    builder.add_node("purpose_analyst", purpose_node)
    builder.add_node("combination_analyst", combination_node)
    builder.add_node("skeptical_reviewer", reviewer_node)
    builder.add_node("build_report", report_node)

    builder.add_edge(START, "parse_manifest")
    builder.add_edge("parse_manifest", "risk_rules")
    builder.add_edge("risk_rules", "permission_mapper")
    builder.add_edge("permission_mapper", "purpose_analyst")
    builder.add_edge("purpose_analyst", "combination_analyst")
    builder.add_edge("combination_analyst", "skeptical_reviewer")
    builder.add_edge("skeptical_reviewer", "build_report")
    builder.add_edge("build_report", END)
    return builder.compile()
