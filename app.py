import html
import json
import os
import re
import streamlit as st
import plotly.graph_objects as go

# --- REAL BACKEND IMPORTS ---
from core.store_scraper import search_play_store_apps, lookup_play_store_app
from core.manifest_parser import extract_permissions_from_xml, extract_permissions_from_apk
from core.provenance import describe_source
from research_agent import find_privacy_policy_url, scrape_policy_text
from agents.privacy_investigator import analyze_privacy_policy_and_terms
from core.policy_view import render_policy_box
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
    "info": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>""",
    
    # Section & Matrix SVG Icons
    "breakdown": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>""",
    "core": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>""",
    "optional": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>""",
    "matrix": """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M16 16v1a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v1"></path><path d="M18 8l4 4-4 4"></path><path d="M22 12H9"></path></svg>""",
    
    # Table Header SVG Badges
    "why_ask": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d2ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>""",
    "risk_allow": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>""",
    "if_deny": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>"""
}

def get_status_svg(icon_type: str, color: str) -> str:
    """Returns clean inline SVG icons for verdict banners and cards."""
    if icon_type == "reasonable":
        return f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 11 12 14 22 4"/></svg>'''
    elif icon_type == "care":
        return f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'''
    elif icon_type == "think_twice":
        return f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'''
    else:
        return f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'''

@st.cache_data
def load_permission_kb():
    """Loads friendly permission metadata from data/permissions.json."""
    kb_path = os.path.join(os.path.dirname(__file__), "data", "permissions.json")
    if os.path.exists(kb_path):
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

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
    app_title = st.session_state.payload.get("app_name", "App")
    safe_title = html.escape(str(app_title))      # anything typed or read from a file is escaped before it goes into HTML
    file_stem = re.sub(r"[^a-z0-9_-]+", "_", str(app_title).lower()).strip("_") or "app"
    raw_status = str(verdict.get("safety_status", "NOT ENOUGH INFORMATION")).upper()
    all_perms = st.session_state.payload.get("permissions", [])
    perm_kb = load_permission_kb()

    # =========================================================================
    # 1. THE FRIENDLY INSTALL DECISION CARD (Phase 1 & Phase 6 - SVG Icons)
    # =========================================================================
    if not all_perms or "NOT ENOUGH" in raw_status or "UNKNOWN" in raw_status:
        bg_color, border_color = "#6b728015", "#6b7280"
        svg_icon = get_status_svg("info", "#9ca3af")
        card_title = "NOT ENOUGH INFORMATION"
        if not all_perms:
            card_desc = f"No declared permissions found for {safe_title}. We cannot verify its access requirements without a valid manifest."
        else:
            card_desc = html.escape(str(verdict.get("summary") or "We do not have enough information to judge this app."))
    elif "HIGH" in raw_status or "THINK TWICE" in raw_status or "RISK" in raw_status:
        bg_color, border_color = "#ef444415", "#ef4444"
        svg_icon = get_status_svg("think_twice", "#ef4444")
        card_title = "THINK TWICE"
        card_desc = f"{safe_title} requests unexpected permission combinations or invasive access that goes beyond its primary features."
    elif "CARE" in raw_status or "CAUTION" in raw_status:
        bg_color, border_color = "#f59e0b15", "#f59e0b"
        svg_icon = get_status_svg("care", "#f59e0b")
        card_title = "INSTALL WITH CARE"
        card_desc = f"{safe_title} requires optional tracking or sensitive access permissions. Review settings after installing."
    else:  # REASONABLE / SAFE
        bg_color, border_color = "#10b98115", "#10b981"
        svg_icon = get_status_svg("reasonable", "#10b981")
        card_title = "LOOKS REASONABLE"
        card_desc = f"The permissions requested by {safe_title} align with standard expectations for this type of application."

    st.markdown(f"""
        <div style="background-color: {bg_color}; border-left: 6px solid {border_color}; padding: 20px 24px; border-radius: 8px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                {svg_icon}
                <h2 style="margin: 0; color: #ffffff; font-size: 1.5rem;">{card_title}</h2>
            </div>
            <p style="margin: 10px 0 0 0; color: #d1d5db; font-size: 1.05rem; line-height: 1.5;">{card_desc}</p>
            <p style="margin: 12px 0 0 0; color: #9ca3af; font-size: 0.82rem; font-style: italic;">
                ⚠️ <strong>Disclaimer:</strong> This verdict evaluates declared permission scopes and policy disclosures. It is an automated risk assessment, not a guarantee of absolute safety.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 2. PERMISSION BREAKDOWN GRID (Core vs. Optional vs. Overreach)
    # =========================================================================
    source_label, source_caveat = describe_source(st.session_state.payload_source, st.session_state.payload)
    st.caption(f"Permissions come from {source_label}. {source_caveat}")
    st.markdown(f"### {SVG_ICONS['breakdown']} Permission Breakdown", unsafe_allow_html=True)
    
    findings = results.get("findings") or results.get("final_findings") or []
    
    flagged_perms = set()
    for f in findings:
        if isinstance(f, dict):
            ev = f.get('evidence') or f.get('raw_evidence') or []
            flagged_perms.update(ev)

    core_perms = [p for p in all_perms if p not in flagged_perms]
    optional_perms = [p for p in all_perms if p in flagged_perms]

    col_core, col_opt = st.columns(2)
    
    with col_core:
        with st.container(border=True):
            st.markdown(f"#### {SVG_ICONS['core']} Core Capabilities", unsafe_allow_html=True)
            st.caption("Standard permissions essential for primary features.")
            if core_perms:
                for p in core_perms:
                    clean = html.escape(p.replace("android.permission.", "")).replace("`", "")
                    kb_info = perm_kb.get(p, {})
                    why = kb_info.get("why_apps_ask", "Required for primary app utility.")
                    st.markdown(f"• **`{clean}`** — <span style='color: #9ca3af; font-size: 0.88rem;'>{why}</span>", unsafe_allow_html=True)
            else:
                st.info("No standard core permissions listed.")

    with col_opt:
        with st.container(border=True):
            st.markdown(f"#### {SVG_ICONS['optional']} Optional / Overreach Access", unsafe_allow_html=True)
            st.caption("Non-essential rights or permissions flagged for review.")
            if optional_perms:
                for p in optional_perms:
                    clean = html.escape(p.replace("android.permission.", "")).replace("`", "")
                    kb_info = perm_kb.get(p, {})
                    risk = kb_info.get("risk_if_allowed", "Presents background access or data privacy trade-offs.")
                    st.markdown(f"• <strong style='color: #f59e0b;'>`{clean}`</strong> — <span style='color: #d1d5db; font-size: 0.88rem;'>{risk}</span>", unsafe_allow_html=True)
            else:
                st.success("No overreaching or optional permissions flagged!")

    st.write("") # Spacer

    # =========================================================================
    # 3. PERMISSION TRADE-OFF MATRIX (Risk vs. Reward - Clean HTML rendering)
    # =========================================================================
    if all_perms:
        st.markdown(f"### {SVG_ICONS['matrix']} Permission Trade-Off Matrix", unsafe_allow_html=True)
        st.caption("What happens if you allow vs. deny access:")

        matrix_rows = []
        for p in all_perms[:6]:  # Limit top 6 for clean matrix view
            clean_name = html.escape(p.replace("android.permission.", ""))
            kb_entry = perm_kb.get(p, {})
            
            why_ask = kb_entry.get("why_apps_ask", "Enables specific feature capability")
            risk_allow = kb_entry.get("risk_if_allowed", "Potential background or data profiling access")
            if_denied = kb_entry.get("if_denied", "Feature degrades gracefully or prompts when clicked")
            
            # Single-line unindented row HTML to prevent Markdown code-block escaping
            row_str = f'<tr style="border-bottom: 1px solid #374151;"><td style="padding: 12px; font-weight: 600; color: #00d2ff;">{clean_name}</td><td style="padding: 12px; color: #d1d5db;">{why_ask}</td><td style="padding: 12px; color: #ef4444;">{risk_allow}</td><td style="padding: 12px; color: #10b981;">{if_denied}</td></tr>'
            matrix_rows.append(row_str)

        matrix_body = "".join(matrix_rows)
        
        # Completely unindented template string ensures zero plain-text leaks
        matrix_html = f"""<div style="overflow-x: auto; margin-bottom: 24px;"><table style="width:100%; text-align:left; border-collapse: collapse; background-color: #111827; border-radius: 8px;"><thead><tr style="border-bottom: 2px solid #4b5563; color: #ffffff; background-color: #1f2937;"><th style="padding: 12px;">Permission</th><th style="padding: 12px;">{SVG_ICONS['why_ask']} Why Apps Ask</th><th style="padding: 12px;">{SVG_ICONS['risk_allow']} Risk If Allowed</th><th style="padding: 12px;">{SVG_ICONS['if_deny']} If You Deny It</th></tr></thead><tbody>{matrix_body}</tbody></table></div>"""
        
        st.markdown(matrix_html, unsafe_allow_html=True)

    # =========================================================================
    # 4. EXPANDABLE TECHNICAL DEEP-DIVE ("Understand deeper with metrics")
    # =========================================================================
    with st.expander("📊 Understand deeper with metrics", expanded=False):
        
        # Download Action Bar
        col_dl1, col_dl2, _ = st.columns([1, 1, 2])
        with col_dl1:
            st.download_button(
                "📄 Download Markdown (.md)", 
                data=report_md.encode("utf-8-sig"), 
                file_name=f"{file_stem}_audit_report.md", 
                mime="text/markdown; charset=utf-8", 
                use_container_width=True
            )
        with col_dl2:
            pdf_bytes = generate_pdf_report(st.session_state.payload, results)
            st.download_button(
                "📥 Download PDF (.pdf)", 
                data=pdf_bytes, 
                file_name=f"{file_stem}_audit_report.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )

        st.write("")

        # Metric Score Cards
        m1, m2, m3 = st.columns(3)
        with m1:
            with st.container(border=True):
                st.metric("Install guidance", raw_status.title(), delta_color="off")
        with m2:
            with st.container(border=True):
                st.metric("Permissions found", len(all_perms))
        with m3:
            with st.container(border=True):
                flagged_count = verdict.get("critical_findings_count", len(findings))
                st.metric("Findings to review", flagged_count)

        # Plotly Data Flow Graph & Policy Analysis
        mid1, mid2 = st.columns([2, 1])
        with mid1:
            with st.container(border=True):
                st.markdown("**PERMISSION DATA FLOW**")
                st.markdown("#### Where access leads")
                try:
                    fig = build_permission_graph(st.session_state.payload, findings)
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
                render_policy_box(st.session_state.payload) 

        # Detailed Itemized Findings List
        st.markdown("---")
        st.markdown("**ITEMIZED AUDIT FINDINGS**")
        st.markdown("#### Detailed Security & Discrepancy Breakdown")
        
        if findings:
            for idx, finding in enumerate(findings, 1):
                if isinstance(finding, dict):
                    ftitle = finding.get('title', f'Discrepancy #{idx}')
                    fseverity = str(finding.get('severity', 'CAUTION')).upper()
                    fdescription = finding.get('reason') or finding.get('description', '')
                    raw_ev = finding.get('evidence') or finding.get('raw_evidence', [])
                    action = finding.get('recommendation') or finding.get('recommended_action')
                else:
                    ftitle = f"Finding #{idx}"
                    fdescription = str(finding)
                    fseverity = "HIGH RISK" if "high" in fdescription.lower() else "CAUTION"
                    raw_ev = []
                    action = None

                s_badge = "finding-badge-high" if "HIGH" in fseverity else "finding-badge-caution"
                
                with st.expander(f"{idx}. {ftitle}", expanded=(idx == 1)):
                    st.markdown(f"<span class='{s_badge}'>{fseverity}</span>", unsafe_allow_html=True)
                    st.markdown(fdescription)
                    
                    if raw_ev:
                        chips_html = " ".join([f"<span class='evidence-chip'>{html.escape(str(p))}</span>" for p in raw_ev])
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
                details = lookup_play_store_app(query)
            if details.get("error"):
                st.error(details["error"])
            else:
                st.session_state.payload = details
                st.session_state.payload_source = "play_store"
                st.session_state.search_results = None
                st.rerun()
        else:
            with st.spinner("Searching Play Store..."):
                st.session_state.search_results = search_play_store_apps(query)
            if not st.session_state.search_results:
                st.warning("We could not find any apps for that search, or Google Play could not be reached. "
                           "Try the app's package name or its Play Store link instead.")

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
                        details = lookup_play_store_app(app['app_id'])
                    if details.get("error"):
                        st.error(details["error"])
                    else:
                        st.session_state.payload = details
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
    
    st.caption("Only the permission list is read from the file. The app is never installed or run. Files over 100 MB are refused.")
    apk_file = st.file_uploader("Upload .apk Package", type=["apk"])
    apk_purpose = st.text_area("What is this app supposed to do?", "", key="apk_purpose",
                               help="Without this we can list the permissions but cannot judge whether they fit the app.")
    if apk_file and st.button("Analyze APK"):
        st.session_state.analysis_results = None
        try:
            with st.spinner("Extracting manifest from APK..."):
                extracted = extract_permissions_from_apk(apk_file.read())
        except ValueError as problem:
            st.error(str(problem))
        else:
            st.session_state.payload = {
                "app_name": extracted.get("app_name", "Off-Store APK"),
                "description": apk_purpose,
                "summary": apk_purpose,
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
        try:
            with st.spinner("Parsing AndroidManifest.xml..."):
                perms = extract_permissions_from_xml(xml_file.read())
        except ValueError as problem:
            st.error(str(problem))
        else:
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

