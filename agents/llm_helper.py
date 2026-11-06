"""One safe way to ask the model a question and get a checked, structured answer."""
import json
import re

from pydantic import BaseModel


class AIReport:
    """Collects, for one analysis run, whether AI helped and any problems along the way."""

    def __init__(self):
        self.used = False
        self.notes = []


def _extract_json(text):
    text = str(text).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _text_of(reply):
    content = getattr(reply, "content", reply)
    if isinstance(content, list):
        content = "".join(part if isinstance(part, str) else str(part.get("text", "")) for part in content)
    return content


def ask_structured(llm, schema, system, user, retries=1):
    """
    Ask the model and check its answer against a Pydantic schema.
    Returns (result, None) on success or (None, short_error_message) on failure.
    It never raises, so one bad AI answer cannot crash the app.
    """
    schema_text = json.dumps(schema.model_json_schema())
    messages = [
        ("system", system + "\nReply with ONE JSON object only, no other text, matching this JSON schema:\n" + schema_text),
        ("human", user),
    ]
    last_error = None
    for attempt in range(retries + 1):
        try:
            reply = llm.invoke(messages)
            return schema.model_validate(_extract_json(_text_of(reply))), None
        except Exception as error:   # network problem, rejected key, bad JSON, wrong shape
            last_error = f"{type(error).__name__}: {str(error)[:140]}"
            if attempt < retries:
                messages = messages + [("human", "That was not valid. Reply again with ONE valid JSON object that matches the schema.")]
    return None, last_error


def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[\"'\u201c\u201d\u2018\u2019]", "", str(text or "").lower())).strip()


def quote_is_in(quote, source):
    """True if the quote really appears in the source text (so the AI cannot invent evidence)."""
    q = normalize(quote)
    return len(q) >= 4 and q in normalize(source)
