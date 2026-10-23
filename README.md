# GhostPermission

GhostPermission is a prototype that analyses permissions declared in an Android `AndroidManifest.xml`. It combines:
- **Person A:** safe XML parsing, a local permission knowledge base, app profiles, and deterministic rules.
- **Person B:** four structured-output AI agents for permission mapping, purpose analysis, combination analysis, and skeptical review.
- **Person C:** LangGraph orchestration that connects the parser, rules, and agents into one workflow.

## Important limitation

A manifest indicates what an app declares or requests. It does **not** prove that a permission is granted, actively used, or abused. Results are review signals, not a malware verdict. Rule scores and thresholds are project-defined, not Android standards.

## 1. Requirements

Use Python 3.11 or newer if possible. From the project root (the folder containing `app.py`):

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

Install all dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Configure the optional AI agents

The rule-based Streamlit app can run without an AI API key. To enable AI-assisted review:

1. Copy `.env.example` to `.env`.
2. Open `.env` and replace `your_groq_api_key_here` with your own Groq API key.
3. Keep `.env` private. Never commit it to Git or share it in screenshots or chat.

Person B's `agents/shared_llm.py` uses Groq (`ChatGroq`). The integrated app keeps that provider rather than silently changing providers.

The AI workflow sends the extracted permission names and the app-purpose description to Groq. It does not intentionally send the raw XML manifest. Do not enter personal or confidential information in the app-purpose field.

## 3. Run the web app

```bash
streamlit run app.py
```

Use one of the included sample manifests or upload an XML manifest. The app first displays Person A's deterministic analysis. If `GROQ_API_KEY` is configured, it then runs the four-agent LangGraph review.

## 4. Run the CLI workflow

The command-line interface is useful for a JSON report:

```bash
python main.py data/sample_manifests/flashlight.xml \
  --app-name "Example flashlight" \
  --app-description "A flashlight app that uses the camera flash"
```

The default output is `ghostpermission-report.json`. You can specify another location with `--output path/to/report.json`.

## 5. Run tests

```bash
python -m pytest -q
```

Tests cover the parser, Person A's deterministic rules, Person C's graph rules, adapters, and workflow structure. The graph tests use fake agents, so they do not require API calls. A passing mock-agent test does not establish the accuracy of a live AI provider.

## How the files connect

1. `core/manifest_parser.py` parses the XML locally using `defusedxml`.
2. `core/risk_rules.py` (Person A) compares permissions against the app profile and returns transparent rule-based findings.
3. `core/graph_risk_rules.py` (Person C) supplies additional deterministic findings to the LangGraph report. It uses an adapter to translate Person A's permission database fields into the schema it expects.
4. `agents/*.py` (Person B) define the four existing structured-output agents.
5. `core/integration.py` adapts Person A's parser signature and Person B's runnable agent interfaces without rewriting their prompts.
6. `core/orchestrator.py` runs the ordered LangGraph workflow and assembles a report.
7. `main.py` loads the real parser, knowledge base, and agents for the CLI and Streamlit AI feature.
8. `app.py` provides the Streamlit user interface and displays deterministic and optional AI findings separately.

## Privacy and safety

- XML is parsed locally before AI analysis.
- The AI provider receives extracted permission names and the user-entered app purpose, not the raw XML file.
- API keys belong in `.env`, which is ignored by Git.
- Uploaded manifests are limited to 2 MiB in the web interface.
- Findings explicitly distinguish requested capability from proven runtime behaviour.
- Do not upload manifests that contain confidential internal package information unless you are authorised to do so.
