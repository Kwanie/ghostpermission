"""CLI entry point for the GhostPermission LangGraph integration."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from core.integration import adapt_langchain_agent, load_callable, load_object
from core.kb_loader import load_knowledge_base
from core.orchestrator import build_ghost_graph


def _env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value or default


def adapt_person_a_knowledge_base(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate Person A's permissions.json fields to Person C's rule schema."""
    converted: dict[str, Any] = {}
    for permission, item in raw.items():
        if not isinstance(item, dict):
            continue
        try:
            weight = float(item.get("weight", 1))
        except (TypeError, ValueError):
            weight = 1
        level = str(item.get("level", "unknown")).lower()
        risk_level = "high" if weight >= 4 else "medium" if weight >= 3 else "low"
        converted[permission] = {
            "description": str(item.get("what_it_allows", "No description available.")),
            "risk_level": risk_level,
            "sensitive": level == "dangerous",
            "display_name": str(item.get("name", permission)),
            "android_protection_level": level,
            "weight": weight,
        }
    return {"permissions": converted}


def build_app():
    """Load Person A's parser and Person B's real agents into Person C's graph."""
    load_dotenv()
    parser_fn = load_callable(
        _env("GHOST_PARSER_MODULE", "core.manifest_parser"),
        _env("GHOST_PARSER_FUNCTION", "extract_permissions"),
    )
    mapper = load_object(
        _env("GHOST_MAPPER_MODULE", "agents.permission_mapper"),
        _env("GHOST_MAPPER_OBJECT", "permission_mapper_agent"),
    )
    purpose = load_object(
        _env("GHOST_PURPOSE_MODULE", "agents.purpose_analyst"),
        _env("GHOST_PURPOSE_OBJECT", "purpose_analyst_agent"),
    )
    combination = load_object(
        _env("GHOST_COMBINATION_MODULE", "agents.combination_analyst"),
        _env("GHOST_COMBINATION_OBJECT", "combination_analyst_agent"),
    )
    reviewer = load_object(
        _env("GHOST_REVIEWER_MODULE", "agents.skeptical_reviewer"),
        _env("GHOST_REVIEWER_OBJECT", "skeptical_reviewer_agent"),
    )

    kb_path = Path(_env("GHOST_KNOWLEDGE_BASE", "data/permissions.json"))
    raw_kb = load_knowledge_base(kb_path)
    knowledge_base = adapt_person_a_knowledge_base(raw_kb)

    return build_ghost_graph(
        parser_fn=parser_fn,
        knowledge_base=knowledge_base,
        permission_mapper_fn=adapt_langchain_agent(mapper, "permission_mapper"),
        purpose_analyst_fn=adapt_langchain_agent(purpose, "purpose_analyst"),
        combination_analyst_fn=adapt_langchain_agent(combination, "combination_analyst"),
        skeptical_reviewer_fn=adapt_langchain_agent(reviewer, "skeptical_reviewer"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse an Android manifest with GhostPermission.")
    parser.add_argument("manifest", help="Path to AndroidManifest.xml")
    parser.add_argument("--app-name", default="", help="Optional app name")
    parser.add_argument("--app-description", default="", help="Intended app purpose; do not include personal data")
    parser.add_argument("--output", default="ghostpermission-report.json", help="Output JSON report path")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        parser.error(f"Manifest file not found: {manifest_path}")

    graph = build_app()
    result = graph.invoke({
        "manifest_path": str(manifest_path),
        "app_name": args.app_name,
        "app_description": args.app_description,
        "knowledge_base": {},
        "errors": [],
    })
    report = result.get("report", {})
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"Report written to: {output_path.resolve()}")
    print(f"Permissions found: {report.get('permissions_count', 0)}")
    print(f"Highest deterministic rule severity: {report.get('highest_rule_severity', 'unknown')}")
    if report.get("errors"):
        print(f"Workflow completed with {len(report['errors'])} error(s). Check the report's errors field.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
