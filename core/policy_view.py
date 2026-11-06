"""The 'Privacy & Terms' box on the results page.

Flow: show the policy link from the app's listing (or nothing), let the user read it with one click
or paste the text, then show an honest report with the exact sentences from the document."""
import hashlib

import streamlit as st

from agents.privacy_investigator import analyze_policy_report
from agents.shared_llm import get_llm
from core.policy_fetch import fetch_policy_text

MIN_USEFUL_CHARS = 50

ICON = {("concern", "High"): "🔴", ("concern", "Medium"): "🟡", ("concern", "Low"): "🟡",
        ("info", "Low"): "⚪", ("reassuring", "Low"): "🟢"}
LABEL = {"concern": "Worth reading closely", "info": "Good to know",
         "reassuring": "What the document says (not verified)"}


def _set_policy(payload, text, source, truncated=False):
    payload["privacy_policy_text"] = text
    payload["privacy_policy_source"] = source
    payload["privacy_policy_truncated"] = truncated
    st.session_state.pop("policy_report_cache", None)


def _render_get_policy(payload, url):
    if url:
        st.caption("Privacy policy link from the app's store listing. Check that it belongs to the right company:")
        st.code(str(url), language=None)
        if st.button("Read this policy", key="read_policy_button"):
            with st.spinner("Reading the policy..."):
                result = fetch_policy_text(str(url))
            if result["ok"] and len(result["text"].strip()) >= MIN_USEFUL_CHARS:
                _set_policy(payload, result["text"], result["final_url"], result["truncated"])
                st.rerun()
            elif result["ok"]:
                st.warning("That page had almost no readable text. You can paste the policy text below instead.")
            else:
                st.warning(result["error"] + " You can paste the policy text below instead.")
    else:
        st.caption("This app's listing does not include a privacy policy link, so we have nothing to read yet.")

    with st.expander("Paste a privacy policy or terms text instead"):
        pasted = st.text_area("Policy or terms text", key="policy_paste_box", height=160)
        if st.button("Check this text", key="check_pasted_policy"):
            if len(pasted.strip()) < MIN_USEFUL_CHARS:
                st.warning("Please paste more text.")
            else:
                _set_policy(payload, pasted, "pasted by you")
                st.rerun()


def _report_for(text, truncated):
    key = hashlib.sha256((text + str(truncated)).encode("utf-8")).hexdigest()
    cached = st.session_state.get("policy_report_cache")
    if cached and cached["key"] == key:
        return cached["report"]
    with st.spinner("Checking the policy..."):
        report = analyze_policy_report(text, llm=get_llm(), truncated=truncated)
    st.session_state["policy_report_cache"] = {"key": key, "report": report}
    return report


def _render_report(payload, text):
    report = _report_for(text, bool(payload.get("privacy_policy_truncated")))
    coverage = report["coverage"]
    st.markdown("**" + report["headline"] + "**")
    st.caption(f"Source: {payload.get('privacy_policy_source') or 'unknown'}. "
               f"We read {coverage['characters_read']:,} characters and {coverage['sentences_read']} sentences "
               f"and checked {coverage['topics_checked']} topics.")
    for note in report["ai_notes"]:
        st.caption("Note: " + note)

    for clause in report["clauses"]:
        icon = ICON.get((clause["kind"], clause["risk_flag"]), "⚪")
        st.markdown(f"**{icon} {clause['topic']}**")
        st.caption(LABEL.get(clause["kind"], ""))
        st.write(clause["summary"])
        if clause.get("summary_by") == "AI":
            st.caption("Summary written by AI. The exact words are below.")
        with st.expander("Exact words from the document"):
            st.text(clause["original_text"])

    with st.expander("What we cannot tell"):
        for line in report["limitations"]:
            st.write("- " + line)

    if st.button("Use a different policy", key="reset_policy_button"):
        for key in ("privacy_policy_text", "privacy_policy_source", "privacy_policy_truncated"):
            payload.pop(key, None)
        st.session_state.pop("policy_report_cache", None)
        st.rerun()


def render_policy_box(payload):
    text = payload.get("privacy_policy_text") or ""
    url = payload.get("privacy_policy_url") or payload.get("privacy_policy") or ""
    if len(text.strip()) >= MIN_USEFUL_CHARS:
        _render_report(payload, text)
    else:
        _render_get_policy(payload, url)
