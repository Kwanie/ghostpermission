"""Chooses the language model. Free Groq first, OpenAI as a second choice.
get_llm() never raises: with no key (or a missing package) it returns None and the app
keeps working with its rule-based checks."""
import os

from core.config import clean   # importing this also loads the .env file

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"     # the model used in the Agentathon class notebooks
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _build():
    """Return (model_or_None, plain-language status)."""
    groq_key = clean(os.getenv("GROQ_API_KEY"))
    openai_key = clean(os.getenv("OPENAI_API_KEY"))

    if groq_key:
        model_name = clean(os.getenv("GHOST_LLM_MODEL")) or DEFAULT_GROQ_MODEL
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model=model_name, temperature=0, api_key=groq_key, timeout=30, max_retries=1)
            return llm, f"AI review on (Groq, {model_name})"
        except ImportError:
            return None, "AI review off: run  python -m pip install langchain-groq  then restart"
        except Exception as error:
            return None, f"AI review off: could not start Groq ({type(error).__name__})"

    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=DEFAULT_OPENAI_MODEL, temperature=0, api_key=openai_key, timeout=30, max_retries=1)
            return llm, f"AI review on (OpenAI, {DEFAULT_OPENAI_MODEL})"
        except ImportError:
            return None, "AI review off: run  python -m pip install langchain-openai  then restart"
        except Exception as error:
            return None, f"AI review off: could not start OpenAI ({type(error).__name__})"

    return None, "AI review off: no API key found in the .env file (rule-based results are still shown)"


def get_llm():
    """Returns an initialised chat model, or None if there is no key or package."""
    return _build()[0]


def llm_status():
    """One plain sentence saying whether AI review is on, and why not if it is off."""
    return _build()[1]
