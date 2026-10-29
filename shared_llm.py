import os
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Returns an initialized LLM instance or None if no API key is set."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
        
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    except Exception:
        return None