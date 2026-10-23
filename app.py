"""Streamlit interface for GhostPermission.

The Android manifest is parsed locally. Only extracted permission names and the
user-entered app purpose are sent to Groq when AI analysis is enabled.
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core.manifest_parser import extract_permissions
from core.risk_rules import analyze_permissions, PERMISSIONS, PROFILES

load_dotenv()
ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "data" / "sample_manifests"
MAX_MANIFEST_BYTES = 2 * 1024 * 1024  # 2 MiB upload limit


@st.cache_resource
def get_ai_graph():
    # Lazy import means the deterministic app still runs without AI packages
    # or an API key configured.
    from main import build_app
    return build_app()


def show_agent_finding(title: str, finding):
    if not isinstance(finding, dict):
        st.write(finding)
        return
    if finding.get("status") in {"skipped", "error"}:
        st.info(f"{title}: {finding.get('reason') or finding.get('message') or finding['status']}")
        return
    with st.expander(f"{title}: {finding.get('title', 'Analysis result')}"):
        st.write(f"**Severity:** {finding.get('severity', 'not supplied')}")
        st.write(finding.get("explanation", "No explanation supplied."))
        evidence = finding.get("evidence", [])
        if evidence:
            st.write("**Evidence**")
            st.write(evidence)
        limitations = finding.get("limitations", [])
        if limitations:
            st.write("**Limitations**")
            st.write(limitations)
        recommendation = finding.get("recommendation")
        if recommendation:
            st.write("**Recommended next step:** " + str(recommendation))


st.set_page_config(page_title="GhostPermission", page_icon="🔎", layout="wide")
st.title("GhostPermission")
st.subheader("Understand what an Android app requests — and whether those requests fit its purpose.")
st.caption(
    "A manifest describes requested capabilities. It does not prove an app actively uses "
    "a permission or is malicious."
)

app_name = st.text_input("App name (optional)", value="")
category = st.selectbox(
    "What is this app supposed to be?",
    options=list(PROFILES.keys()),
    format_func=lambda key: PROFILES[key]["label"],
)
app_description = st.text_area(
    "Describe the app's purpose (used for optional AI analysis)",
    value=PROFILES[category]["label"],
    help="Do not enter personal, confidential, or sensitive information.",
)

source = st.radio("Manifest source", ["Use a sample", "Upload my own"], horizontal=True)
xml_bytes = None
if source == "Use a sample":
    sample_files = sorted(SAMPLES.glob("*.xml"))
    if sample_files:
        sample = st.selectbox("Sample manifest", sample_files, format_func=lambda p: p.name)
        xml_bytes = sample.read_bytes()
    else:
        st.error("No sample manifests were found in data/sample_manifests/.")
else:
    uploaded = st.file_uploader("Upload an Android manifest XML file", type=["xml"])
    if uploaded is not None:
        if uploaded.size > MAX_MANIFEST_BYTES:
            st.error("The manifest exceeds the 2 MiB upload limit.")
        else:
            xml_bytes = uploaded.getvalue()

if st.button("Analyze manifest", type="primary", disabled=xml_bytes is None):
    try:
        permissions = extract_permissions(xml_bytes)
    except ValueError as problem:
        st.error(str(problem))
        st.stop()

    # Person A's deterministic rules remain the primary, explainable baseline.
    result = analyze_permissions(permissions, category)
    st.header(f"Rule-based rating: {result['rating']} (score {result['score']})")
    st.caption(
        "The score and thresholds are this project's own design, not an Android standard "
        "or a definitive security verdict."
    )

    st.subheader("Permissions requested")
    if permissions:
        st.table([
            {
                "Permission": PERMISSIONS.get(p, {}).get("name", p),
                "Technical name": p,
                "Protection level": PERMISSIONS.get(p, {}).get("level", "unknown"),
                "What it may allow": PERMISSIONS.get(p, {}).get(
                    "what_it_allows", "Not yet described in the local knowledge base."
                ),
            }
            for p in permissions
        ])
    else:
        st.info("No permissions were found in the manifest.")

    st.subheader("Rule-based findings")
    if not result["findings"]:
        st.success("No unusual permissions were flagged by the current rules for this app type.")
    for finding in result["findings"]:
        with st.expander(f"{finding['title']} ({finding['severity']})"):
            st.write(finding["explanation"])
            st.write("**Evidence:** " + ", ".join(finding["evidence"]))
            st.write("**What we cannot tell:** " + " ".join(finding["limitations"]))
            st.write("**Next step:** " + finding["recommendation"])

    if os.getenv("GROQ_API_KEY", "").strip() and os.getenv("GROQ_API_KEY") != "your_groq_api_key_here":
        st.subheader("AI-assisted review")
        st.caption(
            "The manifest is parsed locally. The AI workflow receives extracted permission "
            "names and the app-purpose description, not the raw XML file. These fields are "
            "sent to Groq for processing."
        )
        try:
            with st.spinner("Running the four-agent review..."):
                graph = get_ai_graph()
                graph_result = graph.invoke({
                    "manifest_xml": xml_bytes,
                    "app_name": app_name,
                    "app_description": app_description,
                    "knowledge_base": {},
                    "errors": [],
                })
            report = graph_result.get("report", {})
            if report.get("errors"):
                st.warning("The AI workflow reported an error. The rule-based findings above are still available.")
                st.json(report["errors"])
            show_agent_finding("Permission mapper", report.get("permission_analysis"))
            show_agent_finding("Purpose analyst", report.get("purpose_analysis"))
            show_agent_finding("Combination analyst", report.get("combination_analysis"))
            show_agent_finding("Skeptical reviewer", report.get("skeptical_review"))
            st.caption(report.get("interpretation_limit", "AI findings require independent verification."))
        except Exception as exc:
            # Do not display exception text that could accidentally include sensitive config.
            st.error("AI analysis could not be completed. Check your API configuration and terminal logs.")
    else:
        st.info(
            "AI review is not enabled because GROQ_API_KEY is not configured. "
            "The local rule-based analysis above works without an API key."
        )
