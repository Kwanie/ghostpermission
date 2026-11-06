"""Small helper for reading what an app description really says.

It matches whole words (so "map" does not match "bitmap") and ignores words that are
negated (so "No location needed" does NOT count as the app using location).
"""
import re

NEGATING_WORDS = {"no", "not", "without", "never", "dont", "don't", "doesnt", "doesn't",
                  "nothing", "zero", "cannot", "can't", "cant", "won't", "wont", "wouldn't", "shouldn't"}

# A negation does not reach past these words: "we do not sell X but we share Y".
STOP_WORDS = {"and", "but", "or", "however", "except", "unless", "although", "though", "while", "whereas", "yet"}

# "will not hesitate to sell" means the OPPOSITE of "will not sell": the negation cancels itself out.
# "Nothing in this policy prevents us from selling ..." also means the OPPOSITE of a denial: it grants permission.
_CANCELLED = re.compile(
    r"\b(?:not|never|no|\w+n't)\s+(?:hesitate|fail|refrain|neglect|cease|stop)\w*(?:\s+(?:to|from))?"
    r"|\b(?:nothing|no)\b[^.;:!?,\n]*?\b(?:prevent|prohibit|stop|restrict|limit|bar)\w*")

# e.g. "location is not needed", "contacts are never used", "tracking is unnecessary"
_NEGATED_AFTER = re.compile(
    r"^(?:(?:is|are) )?(?:not|never|isn't|aren't) (?:needed|required|used|collected|necessary)"
    r"|^(?:is|are) unnecessary"
)


def _is_negated(text, start, end, window=3):
    """True if the word at text[start:end] is switched off by words around it.

    window=3 looks at the three words before it (used for short app descriptions). A larger window
    (used for policies) looks further back, but never past a word like "but" or "except"."""
    before_clause = re.split(r"[.;:!?,\n]", text[:start])[-1].replace("not only", "")
    before_clause = _CANCELLED.sub(" ", before_clause)
    words = re.findall(r"[a-z']+", before_clause)
    if window > 3:
        for i in range(len(words) - 1, -1, -1):
            if words[i] in STOP_WORDS:
                words = words[i + 1:]
                break
    nearby_words = words[-window:]
    if any(word in NEGATING_WORDS for word in nearby_words):
        return True
    after_clause = re.split(r"[.;:!?\n]", text[end:])[0]
    after_words = " ".join(re.findall(r"[a-z']+", after_clause)[:5])
    return bool(_NEGATED_AFTER.match(after_words))


def mentions(text, terms):
    """True if any term appears as a whole word (a trailing 's' is allowed) and is not negated."""
    lowered = (text or "").lower()
    for term in terms:
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"s?(?![a-z0-9])")
        for match in pattern.finditer(lowered):
            if not _is_negated(lowered, match.start(), match.end()):
                return True
    return False


def find_mentions(text, terms, prefix=False, window=3):
    """
    Every place a term appears, as a list of (start, end, negated).
    prefix=True also matches longer words that start with the term ("sell" finds "selling").
    window: how many words back a negation can reach (see _is_negated).
    """
    lowered = (text or "").lower()
    found = []
    for term in terms:
        tail = r"\w*" if prefix else r"s?(?![a-z0-9])"
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(term.lower()) + tail)
        for match in pattern.finditer(lowered):
            found.append((match.start(), match.end(), _is_negated(lowered, match.start(), match.end(), window)))
    return sorted(found)
