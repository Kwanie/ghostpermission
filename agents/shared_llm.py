from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq

load_dotenv()

# 1. Shared Pydantic Schema
class PermissionFinding(BaseModel):
    title: str = Field(description="A short, clear title for the finding.")
    severity: str = Field(description="Must be 'info', 'review', or 'high concern'.")
    explanation: str = Field(description="Detailed explanation of the privacy risk.")
    evidence: List[str] = Field(description="The specific raw permissions involved.")
    limitations: List[str] = Field(description="What cannot be proven from the manifest alone.")
    recommendation: str = Field(description="Actionable steps for the user.")

# 2. Shared LLM Setup
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
agent_brain = llm.with_structured_output(PermissionFinding, method="json_mode")