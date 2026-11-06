"""Run this to check your computer is ready:   python check_setup.py
Add --online to test that your API key is accepted:    python check_setup.py --online
Add --ai-test to ask the model one tiny question:       python check_setup.py --ai-test
It never prints your keys."""
import importlib.util
import os
import sys
import urllib.error
import urllib.request

from core.config import ENV_FILE, KEY_NAMES, ROOT, clean, explain_http_status, key_problems

PROBLEMS = []


def ok(message):
    print("  OK       " + message)


def bad(message, fix):
    print("  PROBLEM  " + message)
    print("           Fix: " + fix)
    PROBLEMS.append(message)


def check_python_and_packages():
    print("1. Python and packages")
    if sys.version_info >= (3, 10):
        ok("Python " + sys.version.split()[0])
    else:
        bad("Python is older than 3.10", "Install a newer Python from python.org")
    if sys.prefix != sys.base_prefix:
        ok("Running inside a virtual environment")
    else:
        bad("Not running inside the virtual environment", "Activate it, or open a NEW terminal in VS Code")
    for package, pip_name in [("streamlit", "streamlit"), ("defusedxml", "defusedxml"), ("pydantic", "pydantic"),
                              ("dotenv", "python-dotenv"), ("pytest", "pytest"), ("fpdf", "fpdf2"),
                              ("langchain_groq", "langchain-groq"), ("langgraph", "langgraph")]:
        if importlib.util.find_spec(package):
            ok(package + " is installed")
        else:
            bad(package + " is missing", "python -m pip install -r requirements.txt")


def check_files():
    print("2. Project files")
    for relative in ["app.py", "core/manifest_parser.py", "core/risk_rules.py", "core/orchestrator.py",
                     "agents/shared_llm.py", "data/permissions.json"]:
        if (ROOT / relative).exists():
            ok(relative)
        else:
            bad(relative + " is missing", "Copy the whole project folder again, including core, agents and data")


def check_env_file():
    print("3. The .env file and keys")
    if ENV_FILE.exists():
        ok(".env found")
    else:
        wrong = [p.name for p in ROOT.glob(".env*") if p.name not in (".env", ".env.example")]
        if wrong:
            bad("Found " + wrong[0] + " but not .env",
                "Windows may hide file endings. Rename it to exactly  .env  (View > File name extensions)")
        else:
            bad(".env not found", "Copy .env.example to a new file named .env in the project folder, then add your key")
    found_any = False
    for name in KEY_NAMES:
        raw = os.getenv(name)
        if not raw:
            print("  --       " + name + " is not set (you only need one provider)")
            continue
        found_any = True
        problems = key_problems(name, raw)
        if problems:
            for problem in problems:
                bad(name + ": " + problem, "Fix the line in .env, save, and restart")
        else:
            ok(name + " is set and looks well formed (hidden)")
    if not found_any:
        bad("No API key is set yet", "Add GROQ_API_KEY=... to .env (the app still works without AI, using its rules)")


ENDPOINTS = {
    "GROQ_API_KEY": ("Groq", "https://api.groq.com/openai/v1/models", lambda key: {"Authorization": "Bearer " + key}),
    "OPENAI_API_KEY": ("OpenAI", "https://api.openai.com/v1/models", lambda key: {"Authorization": "Bearer " + key}),
}


def ask_provider(url, headers):
    """Return the HTTP status code, or None if the internet could not be reached."""
    headers = dict(headers, **{"User-Agent": "ghostpermission-setup-check/1.0"})
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except (urllib.error.URLError, TimeoutError):
        return None


def check_online():
    print("4. Does the provider accept your key? (needs internet)")
    for name, (label, url, make_headers) in ENDPOINTS.items():
        key = clean(os.getenv(name))
        if not key:
            continue
        status = ask_provider(url, make_headers(key))
        if status is None:
            bad(label + ": could not reach the internet", "Check your connection, VPN or data, then try again")
        elif status == 200:
            ok(label + " accepted the key")
        else:
            bad(label + ": " + explain_http_status(status), "See the message on the left")


def check_ai_answer():
    print("5. Ask the model one tiny question")
    from pydantic import BaseModel
    from agents.llm_helper import ask_structured
    from agents.shared_llm import get_llm, llm_status

    class Pong(BaseModel):
        ok: bool

    print("  --       " + llm_status())
    llm = get_llm()
    if llm is None:
        bad("No model could be started", "Fix the key problems above first")
        return
    result, error = ask_structured(llm, Pong, "Answer with ok set to true.", "Are you working?")
    if result is not None and result.ok:
        ok("The model answered and its answer matched the expected format")
    else:
        bad("The model did not give a usable answer: " + str(error),
            "If it mentions the model name, set GHOST_LLM_MODEL in .env to another model your provider offers")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check_python_and_packages()
    check_files()
    check_env_file()
    if "--online" in argv:
        check_online()
    if "--ai-test" in argv:
        check_ai_answer()
    print()
    if PROBLEMS:
        print(str(len(PROBLEMS)) + " problem(s) found. Fix them in order, then run this again.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
