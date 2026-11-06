"""Run this BEFORE you share the project:   python check_before_sharing.py

It looks for things that must never be shared (API keys inside code, .env files) and tells you what to do.
It never prints a key."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "node_modules", "shareable", "tests"}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip"}

# The lookbehind stops ordinary words like "risk-based-analysis" or "task-management" from matching "sk-...".
KEY_PATTERNS = [
    ("a Groq key", re.compile(r"(?<![A-Za-z0-9_])gsk_[A-Za-z0-9]{20,}")),
    ("an OpenAI key", re.compile(r"(?<![A-Za-z0-9_\-])sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("a Google API key", re.compile(r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z_\-]{30,}")),
]


def is_secret_env_file(path):
    return path.name.startswith(".env") and path.name != ".env.example"


def walk(root):
    for path in Path(root).rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        if path.is_file():
            yield path


def find_env_files(root=ROOT):
    return [p.relative_to(root).as_posix() for p in walk(root) if is_secret_env_file(p)]


def find_keys_in_code(root=ROOT):
    """Files (other than .env) containing something shaped like a real key. Returns [(file, kind)]."""
    problems = []
    for path in walk(root):
        if is_secret_env_file(path) or path.name == ".env.example" or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for kind, pattern in KEY_PATTERNS:
            if pattern.search(text):
                problems.append((path.relative_to(root).as_posix(), kind))
    return problems


def main(root=ROOT):
    print("Checking before sharing...")
    env_files = find_env_files(root)
    keys = find_keys_in_code(root)
    if env_files:
        print("  NOTE     Found key file(s): " + ", ".join(env_files))
        print("           Never share these. make_clean_zip.py leaves them out automatically.")
    for name, kind in keys:
        print(f"  PROBLEM  {name} contains what looks like {kind}.")
        print("           Fix: delete the key from that file, put it in .env, and make a NEW key at the provider "
              "(the old one is exposed).")
    if not keys:
        print("  OK       No keys found inside the code files.")
        print("  TIP      Share with:  python make_clean_zip.py")
    return 1 if keys else 0


if __name__ == "__main__":
    sys.exit(main())
