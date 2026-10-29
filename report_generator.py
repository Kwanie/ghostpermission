from fpdf import FPDF
from typing import Dict, Any, List, Union

def get_executive_verdict(data: Union[List[Any], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates final install/usage recommendation badge, risk score, and summary.
    Safely handles if 'data' is passed as a list of findings or as a result dictionary.
    """
    # Extract findings list whether passed directly or inside a dictionary
    if isinstance(data, dict):
        findings = data.get("findings") or data.get("final_findings") or []
    elif isinstance(data, list):
        findings = data
    else:
        findings = []

    high_count = 0
    review_count = 0

    for f in findings:
        if isinstance(f, dict):
            sev = str(f.get("severity", "")).lower()
        elif isinstance(f, str):
            sev = f.lower()
        else:
            sev = ""

        if "high" in sev:
            high_count += 1
        elif "review" in sev or "caution" in sev or "warning" in sev:
            review_count += 1

    total_findings = len(findings)

    if high_count >= 1:
        status = "🔴 HIGH PRIVACY RISK"
        safety_status = "HIGH RISK"
        action = "Not Recommended for Installation"
        summary = "This app requests high-exposure permission combinations or sensitive data access that exceeds its core purpose."
        color = "red"
        score = max(10, 100 - (high_count * 25 + review_count * 10))
    elif review_count >= 1:
        status = "🟡 PROCEED WITH CAUTION"
        safety_status = "CAUTION"
        action = "Conditional Use / Permissions Audit Advised"
        summary = "This app requests permissions that require manual review. Restrict access to 'Only While Using App' in Android settings."
        color = "orange"
        score = max(50, 100 - (review_count * 10))
    else:
        status = "🟢 SAFE / RECOMMENDED"
        safety_status = "SAFE"
        action = "Safe to Download & Use"
        summary = "Permissions requested align cleanly with the app's declared operational features."
        color = "green"
        score = 95

    return {
        "status": status,
        "safety_status": safety_status,
        "action": action,
        "summary": summary,
        "color": color,
        "overall_risk_score": score,
        "critical_findings_count": total_findings,
        "expected_permissions_count": 3
    }


def generate_markdown_report(payload: Dict[str, Any], results: Dict[str, Any] = None) -> str:
    """Generates a downloadable UTF-8 Markdown audit report."""
    if results is None and isinstance(payload, dict):
        state_dict = payload
        app_name = state_dict.get("app_name", "App")
        findings = state_dict.get("findings") or state_dict.get("final_findings") or []
        verdict = get_executive_verdict(state_dict)
    else:
        app_name = payload.get("app_name", "App") if isinstance(payload, dict) else "App"
        results_dict = results if isinstance(results, dict) else {}
        findings = results_dict.get("findings") or results_dict.get("final_findings") or []
        verdict = get_executive_verdict(results_dict)

    # \ufeff is the UTF-8 Byte Order Mark (BOM) so Windows reads emojis correctly
    md = "\ufeff# GhostPermission Security & Privacy Audit\n"
    md += f"**App:** {app_name}\n\n"
    md += "## Executive Recommendation\n"
    md += f"**Verdict:** {verdict['status']}\n"
    md += f"**Action:** {verdict['action']}\n"
    md += f"**Summary:** {verdict['summary']}\n\n"
    
    md += "## Audited Findings\n"
    if findings:
        for f in findings:
            if isinstance(f, dict):
                sev = str(f.get('severity', 'info')).upper()
                title = f.get('title') or f.get('description', 'Finding')
                reason = f.get('reason') or f.get('description', 'N/A')
                ev = f.get('evidence') or f.get('raw_evidence') or []
                ev_str = ', '.join(ev) if isinstance(ev, list) else str(ev)
            else:
                sev = "HIGH" if "high" in str(f).lower() else "INFO"
                title = "Discrepancy Detected"
                reason = str(f)
                ev_str = "N/A"

            md += f"### {sev}: {title}\n"
            md += f"- **Reason:** {reason}\n"
            md += f"- **Evidence:** `{ev_str}`\n\n"
    else:
        md += "No critical findings or toxic permission combinations detected.\n"

    return md

def generate_pdf_report(payload: Dict[str, Any], results: Dict[str, Any] = None) -> bytes:
    """Generates a downloadable PDF audit report."""
    from fpdf import FPDF
    
    if results is None and isinstance(payload, dict):
        state_dict = payload
        app_name = state_dict.get("app_name", "App")
        findings = state_dict.get("findings") or state_dict.get("final_findings") or []
        verdict = get_executive_verdict(state_dict)
    else:
        app_name = payload.get("app_name", "App") if isinstance(payload, dict) else "App"
        results_dict = results if isinstance(results, dict) else {}
        findings = results_dict.get("findings") or results_dict.get("final_findings") or []
        verdict = get_executive_verdict(results_dict)

    class PDF(FPDF):
        def header(self):
            self.set_font("helvetica", "B", 15)
            self.set_x(self.l_margin)
            self.cell(self.epw, 10, "GhostPermission Security & Privacy Audit", align="C")
            self.ln(15)
            
        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_x(self.l_margin)
            self.cell(self.epw, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def clean(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    # App Name
    pdf.set_font("helvetica", "B", 12)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw if hasattr(pdf, 'epw') else 190, 10, clean(f"App: {app_name}"))
    pdf.ln(10)
    
    # Executive Recommendation
    pdf.set_font("helvetica", "B", 14)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 10, clean("Executive Recommendation"))
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 11)
    status_clean = verdict['status'].replace("🔴", "[HIGH RISK]").replace("🟡", "[CAUTION]").replace("🟢", "[SAFE]")
    
    # Force X-cursor resets and use effective page width (epw) to prevent spacing crashes
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 8, clean(f"Verdict: {status_clean}"))
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 8, clean(f"Action: {verdict['action']}"))
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 8, clean(f"Summary: {verdict['summary']}"))
    pdf.ln(5)

    # Findings Section
    pdf.set_font("helvetica", "B", 14)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf.epw, 10, clean("Audited Findings"))
    pdf.ln(10)
    
    if findings:
        for idx, f in enumerate(findings, 1):
            if isinstance(f, dict):
                sev = str(f.get('severity', 'info')).upper()
                title = f.get('title') or f.get('description', 'Finding')
                reason = f.get('reason') or f.get('description', 'N/A')
                ev = f.get('evidence') or f.get('raw_evidence') or []
                ev_str = ', '.join(ev) if isinstance(ev, list) else str(ev)
            else:
                sev = "HIGH" if "high" in str(f).lower() else "INFO"
                title = "Discrepancy Detected"
                reason = str(f)
                ev_str = "N/A"
            
            pdf.set_font("helvetica", "B", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 8, clean(f"{idx}. {sev}: {title}"))
            
            pdf.set_font("helvetica", "", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 8, clean(f"Reason: {reason}"))
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 8, clean(f"Evidence: {ev_str}"))
            pdf.ln(3)
    else:
        pdf.set_font("helvetica", "", 11)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 8, clean("No critical findings or toxic permission combinations detected."))

    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)