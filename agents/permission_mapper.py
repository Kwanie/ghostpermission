from langchain_core.prompts import ChatPromptTemplate
from .shared_llm import agent_brain

permission_mapper_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a mobile security Permission Mapper.
Your task is to analyze technical Android permission strings and translate them into clear, human-readable definitions.

You MUST respond strictly with a valid JSON object containing the following top-level keys:
- "title": A short title summarizing the mapped permissions (e.g., "Overview of Requested Capabilities").
- "severity": Must be 'info', 'review', or 'high concern'.
- "explanation": Detailed plain-English mapping of what hardware, data, or capabilities these permissions grant.
- "evidence": A list of the raw permission strings analyzed (e.g., ["android.permission.CAMERA"]).
- "limitations": A list of explicit limitations (e.g., manifest declarations indicate capability, not active runtime usage).
- "recommendation": Actionable next steps for reviewing these permissions."""),
    ("user", "Extracted Permissions to Map: {permissions}")
])

permission_mapper_agent = permission_mapper_prompt | agent_brain