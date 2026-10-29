import streamlit as st
import plotly.graph_objects as go

# --- REAL BACKEND IMPORTS ---
from core.store_scraper import search_play_store_apps, fetch_play_store_details
from core.manifest_parser import extract_permissions_from_xml, extract_permissions_from_apk
from research_agent import find_privacy_policy_url, scrape_policy_text
from agents.privacy_investigator import analyze_privacy_policy_and_terms
from core.integration import analyze_app_data
from core.graph_builder import build_permission_graph
from core.report_generator import generate_markdown_report, get_executive_verdict, generate_pdf_report

# --- 1. SVG & BRANDING DEFINITIONS ---
SHIELD_SVG = """<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>"""

FAVICON_SVG = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2300d2ff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/></svg>"

SVG_ICONS = {
    "search": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>""",
    
    "manual": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>""",
    
    "apk": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>""",
    
    "xml": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><polyline points="10 13 8 15 10 17"></polyline><polyline points="14 13 16 15 14 17"></polyline></svg>""",

    "info": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>"""
}

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GhostPermission",
    page_icon=FAVICON_SVG, 
    layout="wide"
)

# --- 3. CUSTOM CSS ---
st.markdown("""
<style>
    .hero-title { text-align: center; font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--text-color); }
    .hero-highlight { color: var(--primary-color); }
    .hero-subtitle { text-align: center; font-size: 1.1rem; color: gray; margin-bottom: 3rem; }
    .finding-badge-high { background-color: #ef444420; color: #ef4444; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; border: 1px solid #ef444450; }
    .finding-badge-caution { background-color: #f59e0b20; color: #f59e0b; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; border: 1px solid #f59e0b50; }
    .finding-badge-safe { background-color: #10b98120; color: #10b981; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; border: 1px solid #10b98150; }
    .evidence-chip { background-color: var(--secondary-background-color); padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; margin-right: 8px; border: 1px solid #88888840; }
</style>
""", unsafe_allow_html=True)

# --- 4. BRAND HEADER ---
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
        {SHIELD_SVG}
        <div>
            <h2 style="margin: 0; padding: 0; color: #ffffff; line-height: 1.2;">GhostPermission</h2>
            <span style="color: #888888; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px;">
                AUTONOMOUS ANDROID PRIVACY & RISK ENGINE
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 5. SESSION STATE INITIALIZATION ---
if "payload" not in st.session_state:
    st.session_state.payload = None
if "payload_source" not in st.session_state:
    st.session_state.payload_source = None
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# --- 6. HERO SECTION ---
st.markdown("<p style='text-align: center; color: var(--primary-color); font-weight: 600; letter-spacing: 1px; margin-top: 2rem;'>— PERMISSION INTELLIGENCE —</p>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Know what your app is <span class='hero-highlight'>really</span> asking for.</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Upload, paste, or select permissions. GhostPermission turns complex Android access requests into a clear privacy verdict.</div>", unsafe_allow_html=True)

# --- 7. HELPER: RENDER DASHBOARD RESULTS ---
def render_audit_dashboard():
    if not st.session_state.payload:
        return

    if st.session_state.analysis_results is None:
        with st.spinner("🤖 Running AI Agent Swarm & Deterministic Risk Evaluation..."):
            st.session_state.analysis_results = analyze_app_data(st.session_state.payload)

    results = st.session_state.analysis_results
    if not results:
        return

    st.divider()
    
    verdict = get_executive_verdict(results)
    report_md = generate_markdown_report(st.session_state.payload, results)
    
    safety_status = verdict.get("safety_status", "CAUTION").upper()
    if "HIGH" in safety_status or "RISK" in safety_status:
        badge_class = "finding-badge-high"
    elif "SAFE" in safety_status:
        badge_class = "finding-badge-safe"
    else:
        badge_class = "finding-badge-caution"

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        app_title = st.session_state.payload.get("app_name", "App")
        st.markdown(f"<h3 style='margin-bottom: 0;'>Privacy audit results <span class='{badge_class}' style='margin-left: 10px;'>{safety_status}</span></h3>", unsafe_allow_html=True)
        st.caption(f"{app_title} analyzed just now")

    with header_col2:
        st.download_button(
            "📄 Download Markdown (.md)", 
            data=report_md.encode("utf-8-sig"), 
            file_name=f"{app_title.lower().replace(' ', '_')}_audit_report.md", 
            mime="text/markdown; charset=utf-8", 
            use_container_width=True
        )
        pdf_bytes = generate_pdf_report(st.session_state.payload, results)
        st.download_button(
            "📥 Download PDF (.pdf)", 
            data=pdf_bytes, 
            file_name=f"{app_title.lower().replace(' ', '_')}_audit_report.pdf", 
            mime="application/pdf", 
            use_container_width=True
        )
        
    st.write("")

    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            score = verdict.get("overall_risk_score", 0)
            st.metric("Privacy safety score", f"{score} /100", f"{safety_status}", delta_color="normal")
    with m2:
        with st.container(border=True):
            total_perms = len(st.session_state.payload.get("permissions", []))
            st.metric("Permissions found", total_perms, f"{verdict.get('expected_permissions_count', total_perms)} expected", delta_color="off")
    with m3:
        with st.container(border=True):
            flagged_count = verdict.get("critical_findings_count", len(results.get("findings", [])))
            st.metric("Critical findings", flagged_count, "Needs review", delta_color="inverse")

    mid1, mid2 = st.columns([2, 1])
    with mid1:
        with st.container(border=True):
            st.markdown("**PERMISSION DATA FLOW**")
            st.markdown("#### Where access leads")
            try:
                fig = build_permission_graph(st.session_state.payload)
                if isinstance(fig, go.Figure):
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Interactive permission graph rendered.")
            except Exception as e:
                st.warning(f"Unable to render node graph: {e}")
            
    with mid2:
        with st.container(border=True):
            st.markdown("**PRIVACY & TERMS**")
            st.markdown("#### Policy research")
            
            policy_text = st.session_state.payload.get("privacy_policy_text", "")
            if policy_text:
                clauses = analyze_privacy_policy_and_terms(policy_text)
                if isinstance(clauses, list):
                    for c in clauses:
                        flag_icon = "🔴" if c.get('risk_flag') == "High" else "🟡" if c.get('risk_flag') == "Medium" else "🟢"
                        st.markdown(f"**{flag_icon} {c.get('topic', 'Clause')}**")
                        st.markdown(c.get('summary', ''))
                        with st.expander("View Original Quote"):
                            st.caption(f"\"{c.get('original_text', '')}\"")
                elif isinstance(clauses, dict):
                    transparency = clauses.get("transparency_score", "Unknown")
                    st.markdown(f"### <span style='color: #f59e0b;'>{transparency}</span> Transparency", unsafe_allow_html=True)
                    for item in clauses.get("bullet_points", []):
                        st.markdown(item)
            else:
                st.caption("No public privacy policy available for this input mode.")
                st.markdown("⚠️ Transparency score unverified")

    st.markdown("---")
    st.markdown("**RISK FINDINGS**")
    st.markdown("#### What needs your attention")
    
    findings = results.get("findings") or results.get("final_findings") or []
    if findings:
        for idx, finding in enumerate(findings, 1):
            if isinstance(finding, dict):
                title = finding.get('title', f'Discrepancy #{idx}')
                severity = str(finding.get('severity', 'CAUTION')).upper()
                description = finding.get('reason') or finding.get('description', '')
                raw_ev = finding.get('evidence') or finding.get('raw_evidence', [])
                action = finding.get('recommendation') or finding.get('recommended_action')
            else:
                title = f"Finding #{idx}"
                description = str(finding)
                severity = "HIGH RISK" if "high" in description.lower() else "CAUTION"
                raw_ev = []
                action = None

            s_badge = "finding-badge-high" if "HIGH" in severity else "finding-badge-caution"
            
            with st.expander(f"{idx}. {title}", expanded=(idx == 1)):
                st.markdown(f"<span class='{s_badge}'>{severity}</span>", unsafe_allow_html=True)
                st.markdown(description)
                
                if raw_ev:
                    chips_html = " ".join([f"<span class='evidence-chip'>{p}</span>" for p in raw_ev])
                    st.markdown(f"**RAW EVIDENCE:** {chips_html}", unsafe_allow_html=True)
                    
                if action:
                    st.success(f"**RECOMMENDED ACTION:**\n\n{action}", icon="✅")
    else:
        st.success("No critical permission discrepancies or toxic combinations detected.")

# --- 8. INGESTION PATHWAYS ---
with st.container(border=True):
    st.markdown("**01 &nbsp; CHOOSE APP SOURCE**")

tab1, tab2, tab3, tab4 = st.tabs([
    "Play Store Search",
    "Manual Selection",
    "Upload APK",
    "Manifest XML"
])

# --- TAB 1: PLAY STORE ---
with tab1:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {SVG_ICONS['search']}
            <h3 style="margin: 0; color: #ffffff;">Play Store Search & Link Analyzer</h3>
        </div>
    """, unsafe_allow_html=True)
    
    query = st.text_input("Enter App Name or Direct Play Store Link", placeholder="e.g. Among Us or https://play.google.com/store/apps/details?id=com.innersloth.spacemafia")
    if st.button("Search Play Store"):
        st.session_state.analysis_results = None
        if "details?id=" in query or ("." in query and " " not in query):
            with st.spinner("Fetching Play Store details..."):
                st.session_state.payload = fetch_play_store_details(query)
                st.session_state.payload_source = "play_store"
                st.session_state.search_results = None
                st.rerun()
        else:
            with st.spinner("Searching Play Store..."):
                st.session_state.search_results = search_play_store_apps(query)

    if st.session_state.search_results:
        st.write("### Select an App to Audit:")
        for idx, app in enumerate(st.session_state.search_results):
            col_icon, col_btn = st.columns([1, 6])
            with col_icon:
                if app.get("icon"):
                    try:
                        st.image(app["icon"], width=40)
                    except Exception:
                        st.write("📱")
                else:
                    st.write("📱")
            with col_btn:
                if st.button(f"{app['title']} — {app.get('developer', 'Developer')}", key=f"select_{app.get('app_id', idx)}"):
                    with st.spinner(f"Loading details for {app['title']}..."):
                        st.session_state.payload = fetch_play_store_details(app['app_id'])
                        st.session_state.payload_source = "play_store"
                        st.session_state.search_results = None
                        st.rerun()

    with st.expander("❓ Can't find the app you are looking for in the suggestions?"):
        st.markdown(f"""
        <div style="font-size: 0.9rem; color: #d1d5db; line-height: 1.6;">
            <strong style="color: #ffffff;">How to copy and paste the direct Play Store link:</strong>
            <ol style="margin-top: 8px; margin-bottom: 16px; padding-left: 20px;">
                <li>Open the <strong>Google Play Store</strong> app on your phone (or play.google.com in browser).</li>
                <li>Search for the app and open its main page.</li>
                <li>Tap the <strong>three dots menu (⋮)</strong> in the upper-right corner of the app screen.</li>
                <li>Tap <strong>Share</strong> and select <strong>Copy Link</strong>.</li>
                <li>Paste the copied link into the search box above and click <strong>Search Play Store</strong>.</li>
            </ol>
        </div>

        <hr style="border: 0; border-top: 1px solid #374151; margin: 16px 0;" />

        <div style="display: flex; align-items: flex-start; gap: 10px; background-color: #111827; padding: 12px 16px; border-radius: 8px; border-left: 3px solid #00d2ff;">
            <div>{SVG_ICONS['info']}</div>
            <div style="font-size: 0.88rem; color: #9ca3af; line-height: 1.5;">
                <strong style="color: #ffffff;">Didn't download from the Google Play Store?</strong><br/>
                If you installed an off-store app or have an installation file, click on the 
                <span style="color: #00d2ff; font-weight: 600;">{SVG_ICONS['apk']} Upload APK</span> or 
                <span style="color: #00d2ff; font-weight: 600;">{SVG_ICONS['manual']} Manual Selection</span> 
                tab above to inspect and audit your app directly!
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.payload_source == "play_store":
        render_audit_dashboard()


# --- TAB 2: MANUAL SELECTION ENTRY ---
with tab2:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {SVG_ICONS['manual']}
            <h3 style="margin: 0; color: #ffffff;">Manual Permission Selection</h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Manual App Entry & Permission Selector")
    manual_name = st.text_input("App Name", "Custom Utility App")
    manual_desc = st.text_area("App Purpose / Main Features", "A basic flashlight and torch utility.")

    selected_common_perms = st.multiselect(
        "Select App Permissions:",
        options=[
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.ACCESS_COARSE_LOCATION",
            "android.permission.READ_CONTACTS",
            "android.permission.RECORD_AUDIO",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.READ_SMS",
            "android.permission.INTERNET"
        ]
    )

    other_perms_raw = st.text_area("Other Permission Names (optional, one per line):", placeholder="android.permission.SYSTEM_ALERT_WINDOW")

    if st.button("Audit Manual Input"):
        st.session_state.analysis_results = None
        extra_list = [p.strip() for p in other_perms_raw.splitlines() if p.strip()]
        all_manual_perms = sorted(list(set(selected_common_perms + extra_list)))

        st.session_state.payload = {
            "app_name": manual_name,
            "description": manual_desc,
            "summary": manual_desc,
            "permissions": all_manual_perms
        }
        st.session_state.payload_source = "manual"
        st.rerun()

    if st.session_state.payload_source == "manual":
        render_audit_dashboard()


# --- TAB 3: APK UPLOAD ---
with tab3:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {SVG_ICONS['apk']}
            <h3 style="margin: 0; color: #ffffff;">Off-Store APK File Unpacker</h3>
        </div>
    """, unsafe_allow_html=True)
    
    apk_file = st.file_uploader("Upload .apk Package", type=["apk"])
    if apk_file and st.button("Analyze APK"):
        st.session_state.analysis_results = None
        with st.spinner("Extracting manifest from APK..."):
            extracted = extract_permissions_from_apk(apk_file.read())
        st.session_state.payload = {
            "app_name": extracted.get("app_name", "Off-Store APK"),
            "description": "Uploaded off-store APK file.",
            "summary": "Directly extracted Android application package.",
            "permissions": extracted.get("permissions", [])
        }
        st.session_state.payload_source = "apk"
        st.rerun()

    if st.session_state.payload_source == "apk":
        render_audit_dashboard()


# --- TAB 4: MANIFEST XML UPLOAD ---
with tab4:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {SVG_ICONS['xml']}
            <h3 style="margin: 0; color: #ffffff;">AndroidManifest.xml Parser</h3>
        </div>
    """, unsafe_allow_html=True)
    
    xml_file = st.file_uploader("Upload AndroidManifest.xml", type=["xml"])
    xml_app_name = st.text_input("Target App Name", "Sample App")
    xml_app_desc = st.text_area("Stated Purpose", "A simple utility.")
    if xml_file and st.button("Parse Manifest XML"):
        st.session_state.analysis_results = None
        with st.spinner("Parsing AndroidManifest.xml..."):
            perms = extract_permissions_from_xml(xml_file.read())
        st.session_state.payload = {
            "app_name": xml_app_name,
            "description": xml_app_desc,
            "summary": xml_app_desc,
            "permissions": perms
        }
        st.session_state.payload_source = "xml"
        st.rerun()

    if st.session_state.payload_source == "xml":
        render_audit_dashboard()