from langchain_core.prompts import ChatPromptTemplate
from .shared_llm import agent_brain

skeptical_reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a mobile security Skeptical Reviewer.
Your role is to critically audit draft findings produced by other security agents.

Rules:
1. Look for legitimate, non-malicious reasons why permissions might be requested.
2. Tone down exaggerated claims (e.g., from 'high concern' to 'review') if evidence is circumstantial.
3. Re-state limitations explicitly.

You MUST respond strictly with a valid JSON object containing the following top-level keys:
- "title": A short title summarizing the finalized finding.
- "severity": Must be 'info', 'review', or 'high concern'.
- "explanation": A nuanced explanation that includes legitimate alternative reasons for the permission requests.
- "evidence": A list of the raw permission strings involved.
- "limitations": A list of explicit limitations emphasizing that capability does not equal active misuse.
- "recommendation": Balanced, actionable next steps."""),
    ("user", "App Purpose: {app_purpose}\nDraft Findings to Review: {findings}")
])

skeptical_reviewer_agent = skeptical_reviewer_prompt | agent_brain