"""Loads API keys safely from the .env file and explains problems in plain words.
It never prints a key."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent      # the project folder (the one with app.py)
ENV_FILE = ROOT / ".env"

# override=True means the key in .env wins over an old key set elsewhere on the computer.
load_dotenv(ENV_FILE, override=True)

KEY_NAMES = ["GROQ_API_KEY", "OPENAI_API_KEY"]


class MissingKeyError(RuntimeError):
    """Raised when a key is not set. The message never contains the key itself."""


def clean(value):
    """Remove spaces, line breaks and quote marks that sneak in when pasting a key."""
    return (value or "").strip().strip('"').strip("'").strip()


def get_key(name):
    value = clean(os.getenv(name))
    if not value:
        raise MissingKeyError(
            f"{name} is missing. Add a line like {name}=your_key_here to the file named .env "
            f"in the project folder ({ENV_FILE}), save it, then restart the app."
        )
    return value


def key_problems(name, raw_value):
    """Plain-language problems with a pasted key (empty list = looks fine)."""
    problems = []
    raw = raw_value or ""
    value = clean(raw)
    if not value:
        return ["The key is empty."]
    if raw != raw.strip() or "\n" in raw or "\r" in raw:
        problems.append("There are spaces or a line break around the key. Remove them.")
    if raw.strip()[:1] in ("'", '"'):
        problems.append("The key is wrapped in quote marks. Remove the quotes.")
    if " " in value:
        problems.append("There is a space inside the key. Copy it again carefully.")
    if len(value) < 20:
        problems.append("The key looks too short. Copy the whole key.")
    if name == "GROQ_API_KEY" and not value.startswith("gsk_"):
        problems.append("Groq keys normally start with gsk_ . Check you copied the Groq key.")
    if name == "OPENAI_API_KEY" and not value.startswith("sk-"):
        problems.append("OpenAI keys normally start with sk- . Check you copied the OpenAI key.")
    return problems


def explain_http_status(status):
    """Turn the provider's answer code into advice."""
    if status in (401, 403):
        return ("The provider REJECTED the key. Create a new key, paste it into .env with no spaces or quotes, "
                "and restart. Also check it belongs to the right provider.")
    if status == 429:
        return "Too many requests, or the free limit is used up. Wait a few minutes and try again."
    if status == 404:
        return "The provider could not find what we asked for (wrong address or model name)."
    if status == 400:
        return "The provider did not understand the request (often a wrong model name)."
    if status is not None and status >= 500:
        return "The provider's service is having trouble. Try again later."
    return "Unexpected answer from the provider (code " + str(status) + ")."
