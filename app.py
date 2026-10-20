import streamlit as st
from pathlib import Path

from core.manifest_parser import extract_permissions
from core.risk_rules import analyze_permissions, PERMISSIONS, PROFILES

SAMPLES = Path(__file__).parent / "data" / "sample_manifests"

st.set_page_config(page_title="GhostPermissions", page_icon="🔎", layout="wide")
st.title("GhostPermissions")
st.subheader("Find out what an app can reach, and whether it needs to")

app_name = st.text_input("App name", value="")
category = st.selectbox(
    "What is this app supposed to be?",
    options=list(PROFILES.keys()),
    format_func=lambda key: PROFILES[key]["label"],
)

source = st.radio("Which manifest do you want to check?", ["Use a sample", "Upload my own"])
xml_bytes = None
if source == "Use a sample":
    sample = st.selectbox("Sample", sorted(p.name for p in SAMPLES.glob("*.xml")))
    xml_bytes = (SAMPLES / sample).read_bytes()
else:
    uploaded = st.file_uploader("Upload an Android manifest (.xml)", type=["xml"])
    if uploaded is not None:
        xml_bytes = uploaded.read()

if st.button("Analyze"):
    if xml_bytes is None:
        st.warning("Please choose or upload a manifest first.")
    else:
        try:
            permissions = extract_permissions(xml_bytes)
        except ValueError as problem:
            st.error(str(problem))
        else:
            result = analyze_permissions(permissions, category)

            st.header(f"Risk rating: {result['rating']}  (score {result['score']})")
            st.caption("The score and its thresholds are our own team's design, not an Android standard.")

            st.subheader("Permissions this app asks for")
            st.table([
                {"Permission": PERMISSIONS.get(p, {}).get("name", p),
                 "Level": PERMISSIONS.get(p, {}).get("level", "unknown"),
                 "What it allows": PERMISSIONS.get(p, {}).get("what_it_allows", "Not in our knowledge base yet.")}
                for p in permissions
            ])

            st.subheader("Findings")
            if not result["findings"]:
                st.success("Nothing unusual found for this type of app.")
            for finding in result["findings"]:
                with st.expander(f"{finding['title']}  ({finding['severity']})"):
                    st.write(finding["explanation"])
                    st.write("**Evidence:** " + ", ".join(finding["evidence"]))
                    st.write("**What we cannot tell:** " + " ".join(finding["limitations"]))
                    st.write("**Next step:** " + finding["recommendation"])
