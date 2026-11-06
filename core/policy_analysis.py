"""Reads a privacy policy or terms text and finds the sentences that matter.

Everything shown to the user is a REAL sentence copied from the document. Nothing is invented.
This is keyword based, so it can miss things, and it says so."""
import re

from core.text_match import find_mentions

MAX_CHARS = 600_000
MIN_CHARS = 400
MAX_QUOTE = 500
PER_TOPIC = 2
MAX_CLAUSES = 14
NEGATION_WINDOW = 8        # in a policy, "we do not sell your information to third parties" is ONE denial

# A denial followed by one of these is not a clean promise: "we do not sell your data UNLESS ..."
EXCEPTION_WORDS = re.compile(
    r"\b(?:unless|except|other than|apart from|aside from|save for|provided that|as long as|only if|only when|however)\b",
    re.IGNORECASE)
CONDITIONAL_SUMMARY = ("The document says it does not do this, but adds conditions or exceptions. "
                       "Read the exact words below.")

# kind "concern": worth reading. "right": gives you a right. "info": good to know.
TOPICS = [
    {"name": "Selling or renting your data", "kind": "concern", "risk": "High",
     "triggers": ["sell", "sold", "rent", "monetiz", "monetis"],
     "needs": ["data", "information", "personal", "profile", "details"],
     "concern": "Mentions selling or renting data. Check who gets it and whether you can opt out.",
     "reassuring": "Says it does not sell your data. This is the document's claim, not something we verified."},
    {"name": "Sharing with other companies", "kind": "concern", "risk": "Medium",
     "triggers": ["share", "disclos", "third part", "third-part", "advertis", "affiliat", "data broker"],
     # Naming a third party inside a denial of something else ("we do not SELL your data to third parties")
     # must not count as a statement about sharing.
     "weak_triggers": ["third part", "third-part", "advertis", "affiliat", "data broker"],
     "needs": ["data", "information", "personal", "details", "profile", "location", "contacts", "activity"],
     "concern": "Mentions passing your information to other companies. Check who and why.",
     "reassuring": "Says it does not share your information with others. This is the document's claim, not verified."},
    {"name": "Collecting your location", "kind": "concern", "risk": "Medium",
     "triggers": ["location", "gps", "geolocation"],
     "needs": ["collect", "track", "use", "store", "precise", "background", "access", "gather"],
     "high_if": ["background", "continuous", "continuously", "precise"],
     "concern": "Mentions collecting your location. Check whether it is only while you use the app.",
     "reassuring": "Says it does not collect your location. This is the document's claim, not verified."},
    {"name": "Your contacts", "kind": "concern", "risk": "Medium",
     "triggers": ["contacts", "address book", "contact list", "phonebook"],
     "needs": ["collect", "access", "upload", "sync", "read", "import", "store"],
     "concern": "Mentions reading or copying your contacts. The people in your list did not agree to this.",
     "reassuring": "Says it does not collect your contacts. This is the document's claim, not verified."},
    {"name": "Advertising and tracking", "kind": "concern", "risk": "Medium",
     "triggers": ["advertising id", "advertising identifier", "tracking", "tracker", "pixel", "profiling", "fingerprint"],
     "concern": "Mentions tracking or building a profile of you for advertising.",
     "reassuring": "Says it does not track you. This is the document's claim, not verified."},
    {"name": "Giving up legal rights", "kind": "concern", "risk": "Medium",
     "triggers": ["arbitration", "class action", "class-action", "waive", "jury trial"],
     "concern": "Mentions arbitration or giving up the right to sue. This can limit what you can do if something goes wrong.",
     "reassuring": "Says it does not force arbitration or waive your rights. This is the document's claim."},
    {"name": "Changes without notice", "kind": "concern", "risk": "Medium",
     "triggers": ["without notice", "without prior notice", "sole discretion"],
     "concern": "Says the rules can change without telling you.",
     "reassuring": "Says it will tell you before changing the rules. This is the document's claim."},
    {"name": "Broad rights over what you post", "kind": "concern", "risk": "Medium",
     "triggers": ["royalty-free", "perpetual", "irrevocable", "sublicens", "worldwide licen", "transferable licen"],
     "concern": "Gives the company broad, long-lasting rights over content you upload."},
    {"name": "Keeping your data", "kind": "info", "risk": "Low",
     "triggers": ["retain", "retention", "stored for", "keep your", "store your", "indefinite"],
     "high_if": ["indefinite"],
     "concern": "Describes how long your data is kept."},
    {"name": "Deleting your data", "kind": "right", "risk": "Low",
     "triggers": ["delete", "deletion", "erase", "opt out", "opt-out"],
     "concern": "May limit your ability to delete your data.",
     "reassuring": "Describes a way to delete your data or opt out. Check that it is easy to use."},
    {"name": "Children", "kind": "info", "risk": "Low",
     "triggers": ["children", "under 13", "under 16", "under 18", "minors"],
     "concern": "Says something about children's data."},
    {"name": "Security measures", "kind": "info", "risk": "Low",
     "triggers": ["encrypt", "security measures", "safeguard"],
     "concern": "Describes how data is protected. This is a claim, not proof."},
]

LIMITATIONS = [
    "We only look for a fixed set of topics by keyword, so we can miss things and can misread a sentence.",
    "A policy can say one thing while an app does another. Policies show what a company says, not what it does.",
]

_ORDER = {("concern", "High"): 0, ("concern", "Medium"): 1, ("concern", "Low"): 2, ("info", "Low"): 3,
          ("reassuring", "Low"): 4}


def split_sentences(text):
    """Real sentences. Line breaks (headings, bullets) are boundaries; long sentences are kept whole."""
    sentences = []
    for block in re.split(r"\n+", text or ""):
        block = block.strip(" \t\u2022-*\u2013\u00b7")
        if not block:
            continue
        for piece in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"\u201c(])", block):
            piece = " ".join(piece.split())
            if len(piece) >= 15:
                sentences.append(piece)
    return sentences


def _match(sentence, topic):
    """Return (kind, risk, keyword) if this sentence is about the topic, else None."""
    hits = find_mentions(sentence, topic["triggers"], prefix=True, window=NEGATION_WINDOW)
    if not hits:
        return None
    needs = topic.get("needs")
    if needs and not find_mentions(sentence, needs, prefix=True):
        return None
    lowered = sentence.lower()
    positive = [h for h in hits if not h[2]]
    keyword = lowered[hits[0][0]:hits[0][1]]
    base_kind = topic["kind"]

    if base_kind == "right":
        if positive:
            return "reassuring", "Low", keyword, None
        return "concern", "Medium", keyword, None    # e.g. "we cannot delete your data"
    if not positive:                                   # every mention is negated: "we do not sell ..."
        weak = topic.get("weak_triggers", [])
        if weak and all(any(lowered[h[0]:h[1]].startswith(w) for w in weak) for h in hits):
            return None                                # only a side mention of a third party: say nothing
        if topic.get("reassuring"):
            if EXCEPTION_WORDS.search(sentence):       # "we do not sell your data unless ..." is NOT a clean promise
                return "concern", "Medium", keyword, "conditional"
            return "reassuring", "Low", keyword, None
        return None
    risk = topic["risk"]
    if any(find_mentions(sentence, topic.get("high_if", []), prefix=True)):
        risk = "High" if base_kind == "concern" else "Medium"
    kind = "info" if base_kind == "info" and risk == "Low" else "concern"
    return kind, risk, keyword, None


def analyze_policy(text, topics=None, truncated=False, min_chars=MIN_CHARS):
    """Returns a report dictionary. Never raises, never invents text."""
    topics = topics or TOPICS
    text = (text or "")[:MAX_CHARS]
    clean = text.strip()
    report = {
        "status": "ok", "headline": "", "clauses": [], "limitations": list(LIMITATIONS),
        "coverage": {"characters_read": len(clean), "sentences_read": 0, "topics_checked": len(topics),
                     "truncated": bool(truncated or len(text) >= MAX_CHARS)},
        "ai_used": False, "ai_notes": [],
    }
    if len(clean) < min_chars:
        report["status"] = "too_short"
        report["headline"] = (f"We could only read {len(clean)} characters, which is not enough to say anything "
                              f"about this document.")
        return report

    sentences = split_sentences(clean)
    report["coverage"]["sentences_read"] = len(sentences)
    found, seen = [], set()
    for position, sentence in enumerate(sentences):
        for topic in topics:
            match = _match(sentence, topic)
            if match is None or (topic["name"], sentence) in seen:
                continue
            seen.add((topic["name"], sentence))
            kind, risk, keyword, note = match
            summary = topic.get("reassuring") if kind == "reassuring" else topic.get("concern")
            if note == "conditional":
                summary = CONDITIONAL_SUMMARY
            quote = sentence if len(sentence) <= MAX_QUOTE else sentence[:MAX_QUOTE].rsplit(" ", 1)[0] + " ..."
            found.append({
                "topic": topic["name"], "keyword": keyword, "kind": kind, "risk_flag": risk,
                "summary": summary or topic["name"], "summary_by": "rules",
                "original_text": quote, "quote_truncated": quote != sentence, "position": position,
            })

    counts, kept = {}, []
    for clause in sorted(found, key=lambda c: (_ORDER.get((c["kind"], c["risk_flag"]), 5), c["position"])):
        counts[clause["topic"]] = counts.get(clause["topic"], 0) + 1
        if counts[clause["topic"]] <= PER_TOPIC:
            kept.append(clause)
    report["clauses"] = kept[:MAX_CLAUSES]

    concerns = [c for c in report["clauses"] if c["kind"] == "concern"]
    if concerns:
        word = "point" if len(concerns) == 1 else "points"
        report["headline"] = f"{len(concerns)} {word} worth reading closely."
    else:
        report["headline"] = ("No concerning clause found among the topics we look for. "
                              "This is not a guarantee, and we may have missed something.")
    if report["coverage"]["truncated"]:
        report["headline"] += " Only the first part of a very long document was read."
    return report
