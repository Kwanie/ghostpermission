from langchain_core.prompts import ChatPromptTemplate
from .shared_llm import agent_brain

purpose_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a mobile privacy Purpose Analyst.
Your job is to compare an app's stated purpose with its extracted permissions.

Rules:
1. If a permission is disproportionate to the app's purpose, flag it.
2. State explicit limitations to prevent unsupported claims.
3. Keep explanations concise and focused.

You MUST respond strictly with a valid JSON object containing the following top-level keys:
- "title": A short title summarizing the purpose mismatch (e.g., "Unnecessary Location Access").
- "severity": Must be 'info', 'review', or 'high concern'.
- "explanation": Detailed plain-English explanation of why the permission doesn't match the stated purpose.
- "evidence": A list of the raw permission strings involved.
- "limitations": A list of explicit limitations (e.g., the manifest does not confirm actual data collection).
- "recommendation": Actionable next steps for reviewing or removing these permissions."""),
    ("user", "App Purpose: {app_purpose}\nExtracted Permissions: {permissions}")
])

purpose_analyst_agent = purpose_prompt | agent_brain