import os
import sys

# Ensure Python looks in the current workspace directory for the 'agents' module
sys.path.append(os.path.abspath("."))

from agents.permission_mapper import permission_mapper_agent
from agents.purpose_analyst import purpose_analyst_agent
from agents.combination_analyst import combination_analyst_agent
from agents.skeptical_reviewer import skeptical_reviewer_agent

# 1. Defined Mock Data (Matches guidelines test scenario)
mock_app_name = "Simple Flashlight"
mock_app_purpose = "A simple flashlight app that turns on the camera flash to illuminate dark areas."
mock_permissions = [
    "android.permission.CAMERA",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.READ_CONTACTS"
]

print(f"=== TESTING ROLE B AGENT PIPELINE FOR: {mock_app_name} ===")
print(f"Purpose: {mock_app_purpose}")
print(f"Permissions: {mock_permissions}\n")

# --- STEP 1: Permission Mapper ---
print("1 Running Permission Mapper...")
mapper_finding = permission_mapper_agent.invoke({
    "permissions": mock_permissions
})
print(f"   [Mapped] Title: {mapper_finding.title}")
print(f"   [Mapped] Severity: {mapper_finding.severity}\n")

# --- STEP 2: Purpose Analyst ---
print("2 Running Purpose Analyst...")
purpose_finding = purpose_analyst_agent.invoke({
    "app_purpose": mock_app_purpose,
    "permissions": mock_permissions
})
print(f"   [Purpose] Title: {purpose_finding.title}")
print(f"   [Purpose] Severity: {purpose_finding.severity}\n")

# --- STEP 3: Combination Analyst ---
print("3 Running Combination-Risk Analyst...")
combination_finding = combination_analyst_agent.invoke({
    "app_purpose": mock_app_purpose,
    "permissions": mock_permissions
})
print(f"   [Combination] Title: {combination_finding.title}")
print(f"   [Combination] Severity: {combination_finding.severity}\n")

# --- STEP 4: Skeptical Reviewer ---
print("4 Running Skeptical Reviewer (Auditing All Draft Findings)...")
accumulated_drafts = f"""
Draft Finding 1 (Permission Capabilities):
Title: {mapper_finding.title}
Explanation: {mapper_finding.explanation}

Draft Finding 2 (Purpose Analysis):
Title: {purpose_finding.title}
Severity: {purpose_finding.severity}
Explanation: {purpose_finding.explanation}

Draft Finding 3 (Combination Analysis):
Title: {combination_finding.title}
Severity: {combination_finding.severity}
Explanation: {combination_finding.explanation}
"""

reviewed_finding = skeptical_reviewer_agent.invoke({
    "app_purpose": mock_app_purpose,
    "findings": accumulated_drafts
})

print("==================================================")
print("=== FINAL REVIEWED OUTPUT FOR HANDOFF TO PERSON C ===")
print("==================================================")
print(f"Title:       {reviewed_finding.title}")
print(f"Severity:    {reviewed_finding.severity}")
print(f"Explanation: {reviewed_finding.explanation}\n")
print(f"Evidence:    {reviewed_finding.evidence}")
print(f"Limitations: {reviewed_finding.limitations}")
print(f"Action:      {reviewed_finding.recommendation}")