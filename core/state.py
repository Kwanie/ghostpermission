from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Finding(BaseModel):
    title: str = Field(description="Short descriptive name of the security finding")
    severity: str = Field(description="Risk level: 'high', 'review', or 'justified' (explained by the app's description)")
    reason: str = Field(description="Plain-language explanation of why this finding exists")
    evidence: List[str] = Field(default_factory=list, description="List of permissions or text snippets supporting this claim")
    limitations: List[str] = Field(default_factory=list, description="What cannot be concluded from manifest alone")
    recommendation: str = Field(default="", description="Suggested user remediation action")
    reviewed_by_skeptic: bool = Field(default=False, description="Whether Skeptical Reviewer evaluated this claim")

class PermissionState(BaseModel):
    app_name: str
    description: str
    permissions: List[str]
    privacy_policy_url: Optional[str] = None
    privacy_policy_text: Optional[str] = None
    deterministic_findings: List[Dict[str, Any]] = Field(default_factory=list)
    mapped_permissions: List[Dict[str, Any]] = Field(default_factory=list)
    purpose_findings: List[Finding] = Field(default_factory=list)
    combo_findings: List[Finding] = Field(default_factory=list)
    agent_findings: List[Finding] = Field(default_factory=list)
    final_findings: List[Finding] = Field(default_factory=list)
    audit_summary: str = ""
    ai_used: bool = Field(default=False, description="True only if a language model actually helped in this run")
    ai_notes: List[str] = Field(default_factory=list, description="Plain-language notes about AI problems or fallbacks")