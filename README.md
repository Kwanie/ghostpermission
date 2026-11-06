# GhostPermission 🛡️

GhostPermission is an AI-powered security and privacy auditor that analyzes Android app permissions, terms and conditions, and privacy policies before installation.

It evaluates potential privacy exposures, identifies dangerous permission combinations, audits legal documents, and filters out false positives using a specialized multi-agent workflow.

---

## Key Features & Ingestion Pathways

GhostPermission supports 4 input methods to audit any Android app:

1. **Play Store Search / Direct URL**: Search for any app dynamically or paste a direct Google Play Store URL. Includes built-in guidance if an official app is hard to find.
2. **Manual Selection Entry**: Manually choose common Android permissions or input custom permission strings alongside app purpose descriptions.
3. **Off-Store APK Unpacking**: Upload `.apk` packages to extract manifest permissions directly using `androguard`.
4. **Manifest XML Parsing**: Upload raw `AndroidManifest.xml` files for local parsing.

---

## Core AI Engine & Audit Deliverables

- **Multi-Agent Pipeline**: Combines Permission Mapper, Purpose Analyst, Combination Analyst, Privacy Investigator, and Skeptical Reviewer agents to prevent false alarms.
- **Terms & Privacy Policy Analysis**: Extracts critical legal clauses (data sales, broad content licenses, binding arbitration, continuous location tracking) alongside side-by-side original quotes.
- **Permission Exposure Topology Map**: Color-blind accessible Plotly node map visually connecting `App` $\rightarrow$ `Permissions` $\rightarrow$ `Exposed Data Types`.
- **Careful Install Guidance**: Gives one of four careful verdicts: `🟢 LOOKS REASONABLE`, `🟡 INSTALL WITH CARE`, `🔴 THINK TWICE` or `⚪ NOT ENOUGH INFORMATION`. It never says an app is "safe", because a manifest and a policy only show what an app *may* do.
- **Audit Reports**: Download complete Markdown (`.md`) and PDF (`.pdf`) reports formatted with Windows UTF-8 compatibility.

---

## Requirements & Setup

### 1. Environment Setup

Python 3.11 or newer is recommended.

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS / Linux:
source .venv/bin/activate

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
