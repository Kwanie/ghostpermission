# GhostPermission 🛡️

GhostPermission is an AI-powered security and privacy auditor that analyzes Android app permissions, terms and conditions, and privacy policies before installation[cite: 10, 13].

It evaluates potential privacy exposures, identifies dangerous permission combinations, audits legal documents, and filters out false positives using a specialized multi-agent workflow[cite: 1, 10, 13].

---

## 🌟 Key Features & Ingestion Pathways

GhostPermission supports 5 input methods to audit any Android app:

1. **🔍 Play Store Search / Direct URL**: Search for any app dynamically or paste a direct Google Play Store URL. Includes built-in guidance if an official app is hard to find.
2. **✍️ Manual Selection Entry**: Manually choose common Android permissions or input custom permission strings alongside app purpose descriptions.
3. **📦 Off-Store APK Unpacking**: Upload `.apk` packages to extract manifest permissions directly using `androguard`[cite: 13].
4. **📄 Manifest XML Parsing**: Upload raw `AndroidManifest.xml` files for local parsing[cite: 13].

---

## 🤖 Core AI Engine & Audit Deliverables

* **Multi-Agent Pipeline**: Combines Permission Mapper, Purpose Analyst, Combination Analyst, Privacy Investigator, and Skeptical Reviewer agents to prevent false alarms[cite: 1, 10, 13].
* **📜 Terms & Privacy Policy Analysis**: Extracts critical legal clauses (data sales, broad content licenses, binding arbitration, continuous location tracking) alongside side-by-side original quotes[cite: 10, 13].
* **🕸️ Permission Exposure Relationship Map**: Interactive NetworkX & Plotly node map visually connecting `App` $\rightarrow$ `Permissions` $\rightarrow$ `Exposed Data Types`[cite: 13].
* **💡 Executive Decision Verdicts**: Generates clear installation recommendations (`🟢 SAFE / RECOMMENDED`, `🟡 PROCEED WITH CAUTION`, or `🔴 HIGH PRIVACY RISK`)[cite: 13].
* **📥 UTF-8 Audit Reports**: Download complete Markdown reports formatted with Windows UTF-8 compatibility[cite: 11, 13].

---

## 📋 Requirements & Setup

### 1. Environment Setup

Python 3.11 or newer is recommended[cite: 13].

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS / Linux:
source .venv/bin/activate

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1