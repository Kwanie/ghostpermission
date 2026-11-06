from fpdf import FPDF
from typing import Dict, Any, List, Union

def get_executive_verdict(data: Union[List[Any], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Install guidance for ordinary users.
    It never says an app is "safe": we can only describe what we were able to check.
    """
    permissions = None  # None means "we were only given findings"
    purpose_known = True
    if isinstance(data, dict):
        purpose_known = data.get("purpose_known", True)
        findings = data.get("findings") or data.get("final_findings") or []
        if "permissions" in data:
            permissions = data.get("permissions") or []
    elif isinstance(data, list):
        findings = data
    else:
        findings = []

    high_count = 0
    review_count = 0
    for f in findings:
        sev = str(f.get("severity", "")).lower() if isinstance(f, dict) else str(f).lower()
        if "high" in sev:
            high_count += 1
        elif "review" in sev or "caution" in sev or "warning" in sev:
            review_count += 1
    flagged = high_count + review_count

    if permissions is not None and len(permissions) == 0:
        status = "⚪ NOT ENOUGH INFORMATION"
        safety_status = "NOT ENOUGH INFORMATION"
        action = "We can't give install advice yet"
        summary = "We could not get this app's permissions, so there is nothing to judge. Upload its manifest or choose another way to add the permissions."
        color = "gray"
    elif not purpose_known and high_count == 0:
        # Risky COMBINATIONS still raise the alarm without a purpose. What we cannot do is judge whether
        # the permissions FIT the app, so we ask for the purpose instead of guessing.
        status = "⚪ NOT ENOUGH INFORMATION"
        safety_status = "NOT ENOUGH INFORMATION"
        action = "Tell us what this app is for"
        summary = ("We do not know what this app is supposed to do, so we cannot judge whether its permissions fit. "
                   "Enter what the app is for and run the check again.")
        color = "gray"
    elif high_count >= 1:
        status = "🔴 THINK TWICE"
        safety_status = "HIGH RISK"
        action = "Think twice before installing"
        summary = ("This app asks for more than its purpose seems to need, or for a risky combination. "
                   "We cannot see what it actually does with this access. If you install it, deny the permissions flagged below.")
        color = "red"
    elif review_count >= 1:
        status = "🟡 INSTALL WITH CARE"
        safety_status = "CAUTION"
        action = "Review the flagged permissions before you install"
        summary = "Some permissions need a closer look. Where Android allows it, choose 'Only while using the app' or deny the ones you do not need."
        color = "orange"
    else:
        status = "🟢 LOOKS REASONABLE"
        safety_status = "LOOKS REASONABLE"
        action = "No concerns found in what we could check"
        summary = ("The permissions we could see fit what the app says it does. This is not a guarantee: "
                   "we cannot see what the app actually does with them.")
        color = "green"

    return {
        "status": status,
        "safety_status": safety_status,
        "action": action,
        "summary": summary,
        "color": color,
        "overall_risk_score": None,       # we no longer invent a score
        "critical_findings_count": flagged,
        "expected_permissions_count": None,
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
        md += "No concerns found in what we could check. This is not a guarantee: we cannot see what the app actually does with its access.\n"

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
    status_clean = verdict['status']
    for emoji in ("🔴", "🟡", "🟢", "⚪"):
        status_clean = status_clean.replace(emoji, "")
    status_clean = status_clean.strip()
    
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
        pdf.multi_cell(pdf.epw, 8, clean("No concerns found in what we could check. This is not a guarantee: we cannot see what the app actually does with its access."))

    out = pdf.output()
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)