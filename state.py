"""Shared LangGraph state schema."""
from __future__ import annotations
from typing import Any, TypedDict


class GhostState(TypedDict, total=False):
    manifest_path: str
    manifest_xml: str
    app_name: str
    app_description: str
    permissions: list[str]
    knowledge_base: dict[str, Any]
    rule_findings: list[dict[str, Any]]
    permission_analysis: Any
    purpose_analysis: Any
    combination_analysis: Any
    skeptical_review: Any
    errors: list[dict[str, str]]
    report: dict[str, Any]
