import streamlit as st
import requests
import json
import re
import os
import time
import base64
import hashlib
import io
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="PreAuth.ai", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

DIFY_API_KEY      = "app-dFJIbB5xriPnkEyv7Ur5T9gs"
DIFY_BASE_URL     = "https://unsaid-flashing-wrench.ngrok-free.dev/v1"
DATA_FILE         = os.path.expanduser("~/Desktop/preauth_records.json")
REPORTS_DIR       = os.path.expanduser("~/Desktop/preauth_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
USERS_FILE        = os.path.expanduser("~/Desktop/preauth_users.json")
ANTHROPIC_API_KEY = "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"

DEFAULT_USERS = {
    "admin":    {"password": hashlib.sha256("admin123".encode()).hexdigest(),   "name": "Admin",              "role": "Administrator"},
    "drbennet": {"password": hashlib.sha256("clinic2026".encode()).hexdigest(), "name": "Dr. Alicia Bennett", "role": "Orthopedic Surgeon"},
    "maya":     {"password": hashlib.sha256("preauth2026".encode()).hexdigest(),"name": "Maya Reynolds",      "role": "PA Coordinator"},
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f: return json.load(f)
    save_users(DEFAULT_USERS); return DEFAULT_USERS

def save_users(users):
    with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)

def verify_login(username, password):
    users = load_users()
    if username in users:
        if users[username]["password"] == hashlib.sha256(password.encode()).hexdigest():
            return users[username]
    return None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
:root{--bg:#f5f3ef;--surface:#fff;--surface2:#faf9f7;--border:#e2ddd6;--border2:#ccc8c0;--ink:#1c1916;--ink2:#4a4540;--ink3:#8a847c;--navy:#1a3350;--navy-l:#e8edf4;--green:#1a4a2e;--green-l:#e6f2ec;--amber:#7a4a00;--amber-l:#fef3dc;--red:#6b1a1a;--red-l:#fdeaea;}
*{font-family:'DM Sans',sans-serif;box-sizing:border-box;}
.main{background:var(--bg)!important;}
section[data-testid="stSidebar"]{background:var(--navy)!important;border-right:none!important;}
section[data-testid="stSidebar"] *{color:#fff!important;}
.block-container{padding:2rem 2.5rem!important;max-width:1200px!important;}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
h1,h2,h3,h4,h5,h6{color:var(--ink)!important;}
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4{color:var(--ink)!important;}
p{color:var(--ink2);}
.stExpander{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:4px!important;transition:box-shadow 0.2s ease;}
.stExpander:hover{box-shadow:0 2px 8px rgba(0,0,0,0.06)!important;}
.stExpander summary{color:var(--ink)!important;}

/* animations */
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
@keyframes slideIn{from{opacity:0;transform:translateX(-8px);}to{opacity:1;transform:translateX(0);}}
@keyframes scaleIn{from{opacity:0;transform:scale(0.97);}to{opacity:1;transform:scale(1);}}
.fade-in{animation:fadeIn 0.35s ease forwards;}
.slide-in{animation:slideIn 0.3s ease forwards;}
.scale-in{animation:scaleIn 0.3s ease forwards;}
.result-card{animation:fadeIn 0.4s ease forwards;}
.stat-card{animation:scaleIn 0.3s ease forwards;transition:box-shadow 0.2s ease,transform 0.2s ease;}
.stat-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.08);transform:translateY(-1px);}
.patient-row{transition:border-color 0.15s ease,box-shadow 0.15s ease;}
.patient-row:hover{border-color:var(--navy)!important;box-shadow:0 2px 8px rgba(26,51,80,0.08);}
.badge{transition:opacity 0.15s ease;}

/* nav */
.nav-logo{font-family:'DM Serif Display',serif;font-size:1.6rem;color:#fff!important;letter-spacing:-0.02em;padding:1.5rem 1rem 0.25rem;display:block;}
.nav-tagline{font-size:0.7rem;color:rgba(255,255,255,0.5)!important;letter-spacing:0.12em;text-transform:uppercase;padding:0 1rem 1.5rem;display:block;}
.nav-divider{border:none;border-top:1px solid rgba(255,255,255,0.12);margin:0.5rem 1rem 1rem;}
.nav-section{font-size:0.65rem;color:rgba(255,255,255,0.4)!important;letter-spacing:0.14em;text-transform:uppercase;padding:0.75rem 1rem 0.4rem;display:block;}
.user-pill{background:rgba(255,255,255,0.12);border-radius:2px;padding:0.4rem 0.75rem;font-size:0.75rem;color:#fff!important;display:inline-block;margin-bottom:1rem;}

/* page */
.page-header{padding-bottom:1.5rem;margin-bottom:2rem;border-bottom:1px solid var(--border);animation:slideIn 0.3s ease forwards;}
.page-title{font-family:'DM Serif Display',serif;font-size:2rem;color:var(--ink)!important;letter-spacing:-0.03em;line-height:1.1;margin:0;}
.page-sub{font-size:0.82rem;color:var(--ink3);margin-top:0.35rem;}

/* stat cards */
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem;}
.stat-card{background:var(--surface);border:1px solid var(--border);padding:1.25rem 1.5rem;position:relative;overflow:hidden;}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--navy);transition:height 0.2s ease;}
.stat-card:hover::before{height:4px;}
.stat-card.green::before{background:var(--green);}
.stat-card.amber::before{background:#d4891a;}
.stat-card.red::before{background:#c0392b;}
.stat-number{font-family:'DM Serif Display',serif;font-size:2.25rem;color:var(--ink)!important;line-height:1;margin-bottom:0.25rem;}
.stat-label{font-size:0.72rem;color:var(--ink3);letter-spacing:0.1em;text-transform:uppercase;}

/* gauge */
.gauge-wrap{background:var(--surface);border:1px solid var(--border);padding:2rem;text-align:center;animation:scaleIn 0.4s ease forwards;}
.gauge-number{font-family:'DM Serif Display',serif;font-size:4.5rem;line-height:1;letter-spacing:-0.04em;}
.gauge-label{font-size:0.72rem;letter-spacing:0.14em;text-transform:uppercase;margin-top:0.5rem;}
.gauge-low{color:#1a4a2e;}.gauge-medium{color:#d4891a;}.gauge-high{color:#c0392b;}
.risk-bar-wrap{margin:1rem 0;}
.risk-bar-track{height:6px;background:var(--border);border-radius:3px;overflow:hidden;}
.risk-bar-fill{height:100%;border-radius:3px;transition:width 1s ease;}
.risk-bar-low{background:#1a4a2e;}.risk-bar-medium{background:#d4891a;}.risk-bar-high{background:#c0392b;}
.risk-bar-labels{display:flex;justify-content:space-between;margin-top:0.35rem;font-size:0.68rem;color:var(--ink3);}

/* result cards */
.result-card{background:var(--surface);border:1px solid var(--border);margin-bottom:1rem;overflow:hidden;}
.result-card-header{padding:0.75rem 1.25rem;background:var(--surface2);border-bottom:1px solid var(--border);font-size:0.7rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--ink2)!important;}
.result-card-body{padding:1rem 1.25rem;}
.result-item{padding:0.6rem 0;border-bottom:1px solid var(--border);font-size:0.875rem;color:var(--ink2)!important;line-height:1.55;display:flex;gap:0.75rem;animation:fadeIn 0.3s ease forwards;}
.result-item:last-child{border-bottom:none;}
.result-bullet{color:var(--border2);flex-shrink:0;}
.summary-box{background:var(--navy-l);border-left:3px solid var(--navy);padding:1rem 1.25rem;font-size:0.875rem;color:var(--ink)!important;line-height:1.7;margin-bottom:1.5rem;animation:slideIn 0.3s ease forwards;}

/* badges */
.badge{display:inline-block;padding:0.2rem 0.7rem;font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;border-radius:2px;}
.badge-low{background:var(--green-l);color:var(--green)!important;}
.badge-medium{background:var(--amber-l);color:var(--amber)!important;}
.badge-high{background:var(--red-l);color:var(--red)!important;}

/* patient table */
.patient-row{background:var(--surface);border:1px solid var(--border);padding:1rem 1.25rem;margin-bottom:0.5rem;display:grid;grid-template-columns:2fr 1.5fr 1fr 1fr 1fr;align-items:center;gap:1rem;animation:fadeIn 0.3s ease forwards;}
.patient-name-cell{font-weight:500;font-size:0.9rem;color:var(--ink)!important;}
.patient-id-cell{font-family:'DM Mono',monospace;font-size:0.78rem;color:var(--ink3)!important;}
.table-header{display:grid;grid-template-columns:2fr 1.5fr 1fr 1fr 1fr;gap:1rem;padding:0.5rem 1.25rem;font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--ink3)!important;font-weight:600;margin-bottom:0.5rem;}

/* form */
.form-section-label{font-size:0.7rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--ink3);padding-bottom:0.5rem;border-bottom:1px solid var(--border);margin-bottom:1rem;display:block;}
div[data-testid="stForm"]{background:var(--surface)!important;border:1px solid var(--border)!important;padding:1.75rem!important;border-radius:0!important;transition:box-shadow 0.2s ease;}

/* buttons */
.stButton>button{background:var(--navy)!important;color:#ffffff!important;border:none!important;border-radius:2px!important;font-family:'DM Sans',sans-serif!important;font-size:0.78rem!important;font-weight:600!important;letter-spacing:0.1em!important;padding:0.6rem 1.75rem!important;text-transform:uppercase!important;transition:opacity 0.2s ease,transform 0.15s ease!important;}
.stButton>button:hover{opacity:0.88!important;transform:translateY(-1px)!important;}
.stFormSubmitButton>button{background:var(--navy)!important;color:#ffffff!important;border:none!important;border-radius:2px!important;font-family:'DM Sans',sans-serif!important;font-size:0.78rem!important;font-weight:600!important;letter-spacing:0.1em!important;padding:0.6rem 1.75rem!important;text-transform:uppercase!important;transition:opacity 0.2s ease!important;}
.stFormSubmitButton>button:hover{opacity:0.88!important;}
.stDownloadButton>button{background:#1a4a2e!important;color:#ffffff!important;border:none!important;border-radius:2px!important;font-family:'DM Sans',sans-serif!important;font-size:0.82rem!important;font-weight:600!important;letter-spacing:0.08em!important;padding:0.75rem 2rem!important;text-transform:uppercase!important;transition:opacity 0.2s ease,transform 0.15s ease!important;width:100%!important;}
.stDownloadButton>button:hover{opacity:0.88!important;transform:translateY(-1px)!important;}

/* inputs */
.stTextInput>div>div>input{border:1px solid var(--border)!important;border-radius:2px!important;background:var(--surface)!important;font-size:0.875rem!important;color:var(--ink)!important;transition:border-color 0.2s ease!important;}
.stTextInput>div>div>input:focus{border-color:var(--navy)!important;box-shadow:0 0 0 2px rgba(26,51,80,0.08)!important;}
label{font-size:0.75rem!important;font-weight:600!important;letter-spacing:0.08em!important;text-transform:uppercase!important;color:var(--ink2)!important;}
.stFileUploader{border:1px dashed var(--border2)!important;background:var(--surface2)!important;border-radius:2px!important;transition:border-color 0.2s ease!important;}
.stFileUploader:hover{border-color:var(--navy)!important;}
.stFileUploader *{color:#1c1916!important;}

/* empty state */
.empty-state{text-align:center;padding:4rem 2rem;background:var(--surface);border:1px dashed var(--border2);animation:fadeIn 0.4s ease forwards;}
.empty-state-icon{font-size:2.5rem;margin-bottom:1rem;}
.empty-state-title{font-family:'DM Serif Display',serif;font-size:1.25rem;color:var(--ink)!important;margin-bottom:0.5rem;}
.empty-state-sub{font-size:0.82rem;color:var(--ink3)!important;}

/* export page */
.export-card{background:var(--surface);border:1px solid var(--border);padding:2rem;margin-bottom:1rem;transition:box-shadow 0.2s ease,transform 0.2s ease;animation:fadeIn 0.35s ease forwards;}
.export-card:hover{box-shadow:0 4px 16px rgba(0,0,0,0.06);transform:translateY(-1px);}
.export-card-title{font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--ink);margin-bottom:0.4rem;}
.export-card-meta{font-size:0.75rem;color:var(--ink3);margin-bottom:1rem;}

/* login */
.login-wrap{max-width:420px;margin:6rem auto;animation:fadeIn 0.4s ease forwards;}
.login-card{background:var(--surface);border:1px solid var(--border);padding:2.5rem;}
.stSpinner>div{border-top-color:var(--navy)!important;}
</style>
""", unsafe_allow_html=True)

# ── DATA LAYER ────────────────────────────────────────────────────────────────

def load_records():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r") as f: return json.load(f)
    return {}

def save_records(records):
    with open(DATA_FILE,"w") as f: json.dump(records,f,indent=2)

# ── REPORT CACHE ─────────────────────────────────────────────────────────────

def get_report_path(submission_id):
    return os.path.join(REPORTS_DIR, f"{submission_id}.pdf")

def get_letter_path(submission_id):
    return os.path.join(REPORTS_DIR, f"{submission_id}_letter.txt")

def save_report_cache(submission_id, pdf_bytes, appeal_letter):
    """Save generated PDF and letter to disk so we never regenerate."""
    with open(get_report_path(submission_id), "wb") as f:
        f.write(pdf_bytes)
    with open(get_letter_path(submission_id), "w") as f:
        f.write(appeal_letter)

def load_report_cache(submission_id):
    """Load cached PDF and letter if they exist. Returns (pdf_bytes, letter) or (None, None)."""
    pdf_path    = get_report_path(submission_id)
    letter_path = get_letter_path(submission_id)
    if os.path.exists(pdf_path) and os.path.exists(letter_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        with open(letter_path, "r") as f:
            letter = f.read()
        return pdf_bytes, letter
    return None, None

def add_submission(member_id, patient_name, procedure, risk_score, risk_level, result_json, submitted_by=""):
    records = load_records()
    if member_id not in records:
        records[member_id] = {"patient_name":patient_name,"member_id":member_id,"submissions":[]}
    records[member_id]["submissions"].append({
        "id":f"PA-{int(time.time())}","date":datetime.now().strftime("%b %d, %Y"),
        "timestamp":datetime.now().isoformat(),"procedure":procedure,
        "risk_score":risk_score,"risk_level":risk_level,"result":result_json,"submitted_by":submitted_by
    })
    records[member_id]["patient_name"] = patient_name
    save_records(records)

# ── CLAUDE EXTRACTION ─────────────────────────────────────────────────────────

def extract_fields_from_pdf(uploaded_file):
    if not ANTHROPIC_AVAILABLE:
        st.error("anthropic not installed. Run: pip install anthropic"); return {}
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        pdf_data = base64.standard_b64encode(uploaded_file.getvalue()).decode("utf-8")
        response = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1500,
            messages=[{"role":"user","content":[
                {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":pdf_data}},
                {"type":"text","text":"""Read this entire prior authorization document across ALL pages and extract fields.
Return ONLY valid JSON, no markdown, no explanation.
{"patient_name":"","insurance_id":"","group_number":"","drug_name":"","diagnosis_code":"","provider_npi":"","provider_name":"","facility_name":"","date_of_service":"","cpt_code":"","insurance_plan":"","clinical_summary":""}
For drug_name: use procedure name and CPT code if no drug. For clinical_summary: 2-3 sentences covering diagnosis, procedures, conservative treatments, functional scores, imaging. Read ALL pages."""}
            ]}]
        )
        return json.loads(re.sub(r'```json|```','',response.content[0].text.strip()).strip())
    except Exception as e:
        st.error(f"Extraction error: {str(e)}"); return {}

# ── APPEAL LETTER ─────────────────────────────────────────────────────────────

def generate_appeal_letter(patient_data, result_data):
    if not ANTHROPIC_AVAILABLE: return "Appeal letter generation unavailable."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2000,
            messages=[{"role":"user","content":f"""Write a formal prior authorization appeal letter to UnitedHealthcare Medical Review Department.
Patient: {patient_data.get('patient_name','Unknown')} | Member ID: {patient_data.get('insurance_id','Unknown')}
Procedure: {patient_data.get('drug_name','Unknown')} | Diagnosis: {patient_data.get('diagnosis_code','Unknown')}
Provider NPI: {patient_data.get('provider_npi','Unknown')}
Clinical context: {patient_data.get('clinical_summary','')}
Denial risk factors: {chr(10).join(result_data.get('denial_reasons',[]))}
Missing documentation: {chr(10).join(result_data.get('missing_documentation',[]))}
Recommended fixes: {chr(10).join(result_data.get('recommended_fixes',[]))}
Write a complete professional appeal letter. Date: {datetime.now().strftime('%B %d, %Y')}
Include: formal appeal statement, clinical necessity, rebuttal of each denial reason, documentation list, formal overturn request, provider signature block."""}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Could not generate appeal letter: {str(e)}"

# ── PDF GENERATION ────────────────────────────────────────────────────────────

def generate_report_pdf(patient_data, result_data, appeal_letter_text, submitted_by=""):
    if not REPORTLAB_AVAILABLE: return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.85*inch, rightMargin=0.85*inch, topMargin=0.85*inch, bottomMargin=0.85*inch)
    styles = getSampleStyleSheet()
    title_s  = ParagraphStyle('T',parent=styles['Normal'],fontSize=16,fontName='Helvetica-Bold',spaceAfter=4,alignment=TA_CENTER)
    sub_s    = ParagraphStyle('S',parent=styles['Normal'],fontSize=9,fontName='Helvetica',spaceAfter=2,alignment=TA_CENTER,textColor=colors.HexColor('#555555'))
    h1_s     = ParagraphStyle('H1',parent=styles['Normal'],fontSize=10,fontName='Helvetica-Bold',spaceBefore=12,spaceAfter=4,textColor=colors.HexColor('#1a3350'))
    body_s   = ParagraphStyle('B',parent=styles['Normal'],fontSize=8.5,fontName='Helvetica',spaceAfter=3,leading=13)
    notice_s = ParagraphStyle('N',parent=styles['Normal'],fontSize=7.5,fontName='Helvetica-Oblique',textColor=colors.HexColor('#888888'),alignment=TA_CENTER)

    def section(title):
        return [Spacer(1,6),HRFlowable(width="100%",thickness=0.5,color=colors.HexColor('#1a3350')),Paragraph(title,h1_s)]
    def kv(label,value):
        return Paragraph(f"<b>{label}:</b> {value}",body_s)

    story = []
    story.append(Paragraph("PreAuth.ai - Prior Authorization Analysis Report",title_s))
    story.append(Paragraph(f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Submitted by: {submitted_by}",sub_s))
    story.append(Spacer(1,8))

    score = result_data.get("risk_score",0)
    level = result_data.get("risk_level","unknown").upper()
    score_color = {"LOW":"#1a4a2e","MEDIUM":"#d4891a","HIGH":"#c0392b"}.get(level,"#1a3350")
    t = Table([["DENIAL RISK SCORE","RISK LEVEL","PATIENT","MEMBER ID"],[str(score),level,patient_data.get("patient_name",""),patient_data.get("insurance_id","")]],colWidths=[1.5*inch,1.5*inch,2.5*inch,1.3*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1a3350')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BACKGROUND',(0,1),(0,1),colors.HexColor(score_color)),('TEXTCOLOR',(0,1),(0,1),colors.white),('FONTNAME',(0,1),(0,1),'Helvetica-Bold'),('FONTSIZE',(0,1),(0,1),18),('BACKGROUND',(1,1),(1,1),colors.HexColor(score_color+"33")),('FONTNAME',(1,1),(1,1),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cccccc')),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(t)

    if result_data.get("summary"):
        story += section("EXECUTIVE SUMMARY")
        story.append(Paragraph(result_data["summary"],body_s))

    story += section("PATIENT AND REQUEST DETAILS")
    for label,key in [("Patient Name","patient_name"),("Insurance Member ID","insurance_id"),("Drug / Procedure","drug_name"),("Diagnosis Code","diagnosis_code"),("Provider NPI","provider_npi"),("Clinical Context","clinical_summary")]:
        if patient_data.get(key): story.append(kv(label,patient_data[key]))

    for section_title, data_key in [("DENIAL RISK FACTORS","denial_reasons"),("MISSING DOCUMENTATION","missing_documentation"),("RECOMMENDED FIXES","recommended_fixes")]:
        items = result_data.get(data_key,[])
        if items:
            story += section(section_title)
            for i,item in enumerate(items,1): story.append(Paragraph(f"{i}. {item}",body_s))

    if appeal_letter_text:
        story += section("APPEAL LETTER - READY TO SEND TO UHC MEDICAL REVIEW")
        story.append(Paragraph("Auto-generated based on denial risk analysis. Review and sign before sending to UnitedHealthcare Medical Review Department.",ParagraphStyle('note',parent=styles['Normal'],fontSize=8,fontName='Helvetica-Oblique',textColor=colors.HexColor('#888888'),spaceAfter=8)))
        story.append(HRFlowable(width="100%",thickness=0.3,color=colors.HexColor('#cccccc')))
        story.append(Spacer(1,6))
        for line in appeal_letter_text.split('\n'):
            if line.strip(): story.append(Paragraph(re.sub(r'#{1,6}\s*','',line),body_s))
            else: story.append(Spacer(1,6))

    story.append(Spacer(1,16))
    story.append(Paragraph("Generated by PreAuth.ai - For clinical use only - Review before payer submission",notice_s))
    doc.build(story)
    buffer.seek(0)
    return buffer

# ── DIFY API ──────────────────────────────────────────────────────────────────

def upload_file_to_dify(uploaded_file):
    url = f"{DIFY_BASE_URL}/files/upload"
    headers = {"Authorization":f"Bearer {DIFY_API_KEY}"}
    r = requests.post(url,headers=headers,files={"file":(uploaded_file.name,uploaded_file.getvalue(),"application/pdf")},data={"user":"preauth-ui-user"},timeout=60)
    if r.status_code in (200,201): return r.json().get("id")
    return None

def call_dify(inputs, uploaded_file=None):
    url = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "PreAuthApp/1.0"
    }
    wi = {k:inputs.get(k,"") for k in ["patient_name","insurance_id","drug_name","diagnosis_code","provider_npi"]}
    files_payload = []
    if uploaded_file:
        fid = upload_file_to_dify(uploaded_file)
        if fid:
            files_payload = [{"type":"document","transfer_method":"local_file","upload_file_id":fid}]
            wi["uploaded_docs"] = [{"type":"document","transfer_method":"local_file","upload_file_id":fid}]
    r = requests.post(url,headers=headers,json={"inputs":wi,"query":"analyze this prior authorization request","response_mode":"blocking","user":"preauth-ui-user","files":files_payload},timeout=180)
    print("DIFY STATUS:", r.status_code)
    print("DIFY RESPONSE:", r.text[:300])
    return r.json()

# ── HELPERS ───────────────────────────────────────────────────────────────────

def parse_result(answer):
    try: return json.loads(re.sub(r'```json|```','',answer).strip())
    except: return None

def risk_class(score):
    if score < 40: return "low"
    if score < 70: return "medium"
    return "high"

def render_gauge(score):
    level = risk_class(score)
    c = {"low":"#1a4a2e","medium":"#d4891a","high":"#c0392b"}[level]
    st.markdown(f"""<div class="gauge-wrap">
        <div class="gauge-number gauge-{level}">{score}</div>
        <div class="gauge-label" style="color:{c}">Denial Risk Score</div>
        <div class="risk-bar-wrap"><div class="risk-bar-track"><div class="risk-bar-fill risk-bar-{level}" style="width:{score}%"></div></div>
        <div class="risk-bar-labels"><span>0 - Low</span><span>50 - Medium</span><span>100 - High</span></div></div>
        <br><span class="badge badge-{level}">{level} risk</span></div>""", unsafe_allow_html=True)

def render_result_card(title, icon, items):
    if not items: return
    items_html = "".join([f'<div class="result-item"><span class="result-bullet">-</span><span>{i}</span></div>' for i in items])
    st.markdown(f'<div class="result-card"><div class="result-card-header">{icon}&nbsp;{title}</div><div class="result-card-body">{items_html}</div></div>',unsafe_allow_html=True)

def render_full_result(data, answer_raw):
    if not data:
        st.markdown(f'<div class="result-card"><div class="result-card-header">Action Plan</div><div class="result-card-body" style="white-space:pre-wrap;font-size:0.875rem;line-height:1.7;color:#4a4540">{answer_raw}</div></div>',unsafe_allow_html=True)
        return
    col1,col2 = st.columns([1,2],gap="large")
    with col1: render_gauge(data.get("risk_score",0))
    with col2:
        if data.get("summary"): st.markdown(f'<div class="summary-box">{data["summary"]}</div>',unsafe_allow_html=True)
    render_result_card("Denial Reasons","Warning",data.get("denial_reasons",[]))
    render_result_card("Missing Documentation","Folder",data.get("missing_documentation",[]))
    render_result_card("Recommended Fixes","Check",data.get("recommended_fixes",[]))

# ── LOGIN ─────────────────────────────────────────────────────────────────────

def show_login():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:2.5rem;color:var(--ink);text-align:center;margin-bottom:0.25rem">PreAuth.ai</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.78rem;color:var(--ink3);text-align:center;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:2rem">UHC Prior Authorization Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown('<span class="form-section-label">Sign In</span>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="e.g. drbennet")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In")
    if submitted:
        user = verify_login(username.strip().lower(), password)
        if user:
            st.session_state.logged_in = True
            st.session_state.current_user = user
            st.session_state.username = username.strip().lower()
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.markdown('<div style="margin-top:1.5rem;padding-top:1.5rem;border-top:1px solid var(--border);font-size:0.75rem;color:var(--ink3)"><b style="color:var(--ink2)">Demo accounts:</b><br>admin / admin123 &nbsp; drbennet / clinic2026 &nbsp; maya / preauth2026</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── SESSION INIT ──────────────────────────────────────────────────────────────

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = {}

if not st.session_state.logged_in:
    show_login(); st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<span class="nav-logo">PreAuth.ai</span>', unsafe_allow_html=True)
    st.markdown('<span class="nav-tagline">UHC Prior Authorization</span>', unsafe_allow_html=True)
    user = st.session_state.current_user
    st.markdown(f'<div class="user-pill">{user.get("name","User")} &nbsp;|&nbsp; {user.get("role","")}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.markdown('<span class="nav-section">Navigation</span>', unsafe_allow_html=True)
    page = st.radio("", ["Dashboard","New Submission","Patient Lookup","Export & Reports"], label_visibility="collapsed")
    st.markdown('<hr class="nav-divider" style="margin-top:1.5rem">', unsafe_allow_html=True)
    st.markdown('<span class="nav-section">System</span>', unsafe_allow_html=True)
    records = load_records()
    total = sum(len(v["submissions"]) for v in records.values())
    st.markdown(f'<div style="padding:0 0.5rem;font-size:0.78rem;color:rgba(255,255,255,0.55);line-height:2"><div>Patients on file: <b style="color:white">{len(records)}</b></div><div>Total submissions: <b style="color:white">{total}</b></div><div>Knowledge base: <b style="color:white">245 docs</b></div></div>', unsafe_allow_html=True)
    st.markdown('<hr class="nav-divider" style="margin-top:1.5rem">', unsafe_allow_html=True)
    if st.button("Sign Out"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ── PAGE: DASHBOARD ───────────────────────────────────────────────────────────

if page == "Dashboard":
    st.markdown('<div class="page-header"><h1 class="page-title">Todays Priority Queue</h1><p class="page-sub">Cases that need your attention - UnitedHealthcare Community Plan</p></div>', unsafe_allow_html=True)
    records  = load_records()
    all_subs = [(mid,s) for mid,v in records.items() for s in v["submissions"]]
    all_subs.sort(key=lambda x: x[1]["timestamp"], reverse=True)
    high_risk   = [(mid,s) for mid,s in all_subs if s["risk_level"]=="high"]
    medium_only = [(mid,s) for mid,s in all_subs if s["risk_level"]=="medium"]
    ready       = [(mid,s) for mid,s in all_subs if s["risk_level"]=="low"]
    today = datetime.now().strftime("%A, %B %d, %Y")
    st.markdown(f'<p style="font-size:0.78rem;color:var(--ink3);margin-bottom:1.5rem">{today}</p>', unsafe_allow_html=True)
    st.markdown(f"""<div class="stat-grid">
        <div class="stat-card red"><div class="stat-number" style="color:#c0392b">{len(high_risk)}</div><div class="stat-label">Needs Immediate Review</div></div>
        <div class="stat-card amber"><div class="stat-number" style="color:#d4891a">{len(medium_only)}</div><div class="stat-label">Action Required</div></div>
        <div class="stat-card green"><div class="stat-number" style="color:var(--green)">{len(ready)}</div><div class="stat-label">Ready to Submit</div></div>
        <div class="stat-card"><div class="stat-number">{len(records)}</div><div class="stat-label">Patients on File</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;margin-top:0.5rem"><div style="width:10px;height:10px;border-radius:50%;background:#c0392b;flex-shrink:0"></div><span style="font-size:0.72rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#c0392b">Needs Immediate Review</span></div>', unsafe_allow_html=True)
    if not high_risk:
        st.markdown('<div style="background:var(--surface);border:1px solid var(--border);padding:1.25rem 1.5rem;font-size:0.82rem;color:var(--ink3);margin-bottom:1.5rem">No high risk cases. All clear.</div>', unsafe_allow_html=True)
    else:
        for mid,sub in high_risk[:5]:
            patient = records[mid]["patient_name"]
            score = sub["risk_score"]
            reasons = sub.get("result",{}).get("denial_reasons",[])
            top_reason = reasons[0][:90] if reasons else "-"
            st.markdown(f"""<div style="background:var(--surface);border:1px solid #f0c0c0;border-left:3px solid #c0392b;padding:1.1rem 1.25rem;margin-bottom:0.6rem;animation:fadeIn 0.3s ease forwards">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem">
                    <div><span style="font-weight:600;font-size:0.9rem;color:var(--ink)">{patient}</span>
                    <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:var(--ink3);margin-left:0.75rem">{mid}</span></div>
                    <span class="badge badge-high">{score} - High</span>
                </div>
                <div style="font-size:0.82rem;color:var(--ink2);margin-bottom:0.4rem">{sub["procedure"][:65]}</div>
                <div style="font-size:0.78rem;color:var(--ink3)">{len(reasons)} denial reason{"s" if len(reasons)!=1 else ""} - {top_reason}{"..." if len(top_reason)==90 else ""}</div>
                <div style="font-size:0.72rem;color:var(--ink3);margin-top:0.4rem">Submitted {sub["date"]} by {sub.get("submitted_by","Unknown")}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem"><div style="width:10px;height:10px;border-radius:50%;background:#d4891a;flex-shrink:0"></div><span style="font-size:0.72rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#d4891a">Action Required</span></div>', unsafe_allow_html=True)
    if not medium_only:
        st.markdown('<div style="background:var(--surface);border:1px solid var(--border);padding:1.25rem 1.5rem;font-size:0.82rem;color:var(--ink3);margin-bottom:1.5rem">No medium risk cases.</div>', unsafe_allow_html=True)
    else:
        for mid,sub in medium_only[:5]:
            patient = records[mid]["patient_name"]
            score = sub["risk_score"]
            fixes = sub.get("result",{}).get("recommended_fixes",[])
            st.markdown(f"""<div style="background:var(--surface);border:1px solid #f0dfa0;border-left:3px solid #d4891a;padding:1.1rem 1.25rem;margin-bottom:0.6rem;animation:fadeIn 0.3s ease forwards">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem">
                    <div><span style="font-weight:600;font-size:0.9rem;color:var(--ink)">{patient}</span>
                    <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:var(--ink3);margin-left:0.75rem">{mid}</span></div>
                    <span class="badge badge-medium">{score} - Medium</span>
                </div>
                <div style="font-size:0.82rem;color:var(--ink2);margin-bottom:0.35rem">{sub["procedure"][:65]}</div>
                <div style="font-size:0.78rem;color:var(--ink3)">{len(fixes)} fix{"es" if len(fixes)!=1 else ""} recommended - {sub["date"]}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left_col,right_col = st.columns([1,1],gap="large")
    with left_col:
        st.markdown('<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem"><div style="width:10px;height:10px;border-radius:50%;background:#1a4a2e;flex-shrink:0"></div><span style="font-size:0.72rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#1a4a2e">Ready to Submit</span></div>', unsafe_allow_html=True)
        if not ready:
            st.markdown('<div style="background:var(--surface);border:1px solid var(--border);padding:1.25rem;font-size:0.82rem;color:var(--ink3)">No low risk submissions yet.</div>', unsafe_allow_html=True)
        else:
            for mid,sub in ready[:5]:
                patient = records[mid]["patient_name"]
                score = sub["risk_score"]
                st.markdown(f"""<div style="background:var(--surface);border:1px solid #c0e8d0;border-left:3px solid #1a4a2e;padding:0.9rem 1.1rem;margin-bottom:0.5rem;animation:fadeIn 0.3s ease forwards">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div><span style="font-weight:500;font-size:0.875rem;color:var(--ink)">{patient}</span>
                        <div style="font-size:0.75rem;color:var(--ink3);margin-top:0.2rem">{sub["procedure"][:50]}</div></div>
                        <span class="badge badge-low">{score}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
    with right_col:
        st.markdown('<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem"><div style="width:10px;height:10px;border-radius:50%;background:var(--navy);flex-shrink:0"></div><span style="font-size:0.72rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--navy)">Recent Activity</span></div>', unsafe_allow_html=True)
        if not all_subs:
            st.markdown('<div style="background:var(--surface);border:1px solid var(--border);padding:1.25rem;font-size:0.82rem;color:var(--ink3)">No activity yet.</div>', unsafe_allow_html=True)
        else:
            for mid,sub in all_subs[:6]:
                patient = records[mid]["patient_name"]
                level = sub["risk_level"]
                score = sub["risk_score"]
                dot_color = {"low":"#1a4a2e","medium":"#d4891a","high":"#c0392b"}.get(level,"#888")
                st.markdown(f"""<div style="display:flex;gap:0.75rem;padding:0.65rem 0;border-bottom:1px solid var(--border);align-items:flex-start;animation:fadeIn 0.3s ease forwards">
                    <div style="width:8px;height:8px;border-radius:50%;background:{dot_color};margin-top:0.4rem;flex-shrink:0"></div>
                    <div><div style="font-size:0.82rem;font-weight:500;color:var(--ink)">{patient}</div>
                    <div style="font-size:0.75rem;color:var(--ink3)">{sub["procedure"][:45]} - {sub["date"]}</div></div>
                    <span class="badge badge-{level}" style="margin-left:auto;flex-shrink:0">{score}</span>
                </div>""", unsafe_allow_html=True)

# ── PAGE: NEW SUBMISSION ──────────────────────────────────────────────────────

elif page == "New Submission":
    st.markdown('<div class="page-header"><h1 class="page-title">New Submission</h1><p class="page-sub">Upload a prior authorization packet - fields auto-fill from the document</p></div>', unsafe_allow_html=True)

    for key,default in [("result_data",None),("result_raw",None),("extracted",{}),("uploaded_file_obj",None),("step",1),("appeal_letter",None),("pdf_bytes",None),("pdf_filename",None)]:
        if key not in st.session_state: st.session_state[key] = default

    if st.session_state.step == 1:
        left,right = st.columns([1,1],gap="large")
        with left:
            st.markdown('<span class="form-section-label">Step 1 of 2 - Upload Document or Enter Details</span>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Prior Authorization Packet (PDF)", type=["pdf"])
            st.markdown('<div style="text-align:center;padding:0.75rem 0;font-size:0.75rem;color:var(--ink3);letter-spacing:0.08em">OR FILL IN MANUALLY</div>', unsafe_allow_html=True)
            with st.form("step1_form"):
                patient_name   = st.text_input("Patient Name",            placeholder="e.g. Jordan Ellis",           value=st.session_state.extracted.get("patient_name",""))
                insurance_id   = st.text_input("Insurance Member ID",     placeholder="e.g. 92746158300",            value=st.session_state.extracted.get("insurance_id",""))
                drug_name      = st.text_input("Drug or Procedure",       placeholder="e.g. Right Knee Arthroscopy", value=st.session_state.extracted.get("drug_name",""))
                diagnosis_code = st.text_input("Diagnosis Code (ICD-10)", placeholder="e.g. M23.221",                value=st.session_state.extracted.get("diagnosis_code",""))
                provider_npi   = st.text_input("Provider NPI",            placeholder="e.g. 1686526231",             value=st.session_state.extracted.get("provider_npi",""))
                go = st.form_submit_button("Continue to Review")

            if uploaded_file and uploaded_file.name != (st.session_state.uploaded_file_obj.name if st.session_state.uploaded_file_obj else ""):
                st.session_state.uploaded_file_obj = uploaded_file
                with st.spinner("Reading document and extracting fields..."):
                    extracted = extract_fields_from_pdf(uploaded_file)
                if extracted and any(extracted.values()):
                    st.session_state.extracted = extracted
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.warning("Could not extract fields. Fill in manually and click Continue.")

            if go:
                st.session_state.extracted = {"patient_name":patient_name,"insurance_id":insurance_id,"drug_name":drug_name,"diagnosis_code":diagnosis_code,"provider_npi":provider_npi}
                st.session_state.step = 2
                st.rerun()

        with right:
            st.markdown('<span class="form-section-label">How it works</span>', unsafe_allow_html=True)
            st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);padding:1.5rem;animation:fadeIn 0.4s ease forwards">
                <div style="margin-bottom:1.25rem"><div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--navy);margin-bottom:0.4rem">1. Upload PDF</div>
                <div style="font-size:0.82rem;color:var(--ink2);line-height:1.6">Upload the PA packet. Claude reads all pages and auto-fills every field including clinical details, MRI findings, and functional scores.</div></div>
                <div style="margin-bottom:1.25rem"><div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--navy);margin-bottom:0.4rem">2. Review and Confirm</div>
                <div style="font-size:0.82rem;color:var(--ink2);line-height:1.6">Check the auto-filled fields and clinical summary. Correct anything that looks wrong.</div></div>
                <div><div style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--navy);margin-bottom:0.4rem">3. Run Analysis + Export</div>
                <div style="font-size:0.82rem;color:var(--ink2);line-height:1.6">Claude cross-checks against 245 UHC payer policies, scores denial risk, then head to Export & Reports to download the full PDF report with appeal letter.</div></div>
            </div>""", unsafe_allow_html=True)

    elif st.session_state.step == 2:
        left,right = st.columns([1,1],gap="large")
        with left:
            st.markdown('<span class="form-section-label">Step 2 of 2 - Review Extracted Fields</span>', unsafe_allow_html=True)
            if st.session_state.uploaded_file_obj:
                fname = st.session_state.uploaded_file_obj.name
                st.markdown(f'<div style="background:var(--navy-l);border:1px solid #b8cde0;padding:0.7rem 1rem;font-size:0.78rem;color:var(--navy);margin-bottom:0.5rem;animation:slideIn 0.3s ease forwards">Document uploaded: <b>{fname}</b> - fields auto-filled from all pages.</div>', unsafe_allow_html=True)
                clinical_summary = st.session_state.extracted.get("clinical_summary","")
                if clinical_summary:
                    st.markdown(f'<div style="background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--navy);padding:0.75rem 1rem;font-size:0.78rem;color:var(--ink2);line-height:1.6;margin-bottom:1rem;animation:slideIn 0.3s ease forwards"><b>Clinical summary:</b> {clinical_summary}</div>', unsafe_allow_html=True)

            with st.form("step2_form"):
                e = st.session_state.extracted
                patient_name   = st.text_input("Patient Name",            value=e.get("patient_name",""))
                insurance_id   = st.text_input("Insurance Member ID",     value=e.get("insurance_id",""))
                drug_name      = st.text_input("Drug or Procedure",       value=e.get("drug_name","") or e.get("cpt_code",""))
                diagnosis_code = st.text_input("Diagnosis Code (ICD-10)", value=e.get("diagnosis_code",""))
                provider_npi   = st.text_input("Provider NPI",            value=e.get("provider_npi",""))
                c1,c2 = st.columns([1,1])
                with c1: analyze = st.form_submit_button("Run Prior Auth Analysis")
                with c2: go_back = st.form_submit_button("Back")

            if go_back:
                st.session_state.step = 1
                st.session_state.result_data = None
                st.session_state.result_raw  = None
                st.rerun()

            if analyze:
                with st.spinner("Analyzing against UHC payer guidelines..."):
                    try:
                        inputs = {"patient_name":patient_name,"insurance_id":insurance_id,"drug_name":drug_name,"diagnosis_code":diagnosis_code,"provider_npi":provider_npi}
                        result = call_dify(inputs,st.session_state.uploaded_file_obj)
                        answer = result.get("answer","")
                        if answer:
                            data = parse_result(answer)
                            st.session_state.result_data = data
                            st.session_state.result_raw  = answer
                            st.session_state.extracted.update(inputs)
                            st.session_state.pdf_bytes = None
                            st.session_state.appeal_letter = None
                            if data:
                                pname = data.get("patient_name") or patient_name or "Unknown Patient"
                                mid   = data.get("insurance_id")  or insurance_id  or "UNKNOWN"
                                proc  = data.get("requested_service") or drug_name or "Unknown Procedure"
                                score = data.get("risk_score",0)
                                add_submission(mid,pname,proc,score,risk_class(score),data,st.session_state.current_user.get("name",""))
                        else:
                            st.error(f"No response from workflow. {result}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to Dify. Make sure Docker is running.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with right:
            st.markdown('<span class="form-section-label">Analysis Results</span>', unsafe_allow_html=True)
            if st.session_state.result_data or st.session_state.result_raw:
                render_full_result(st.session_state.result_data,st.session_state.result_raw)
                st.markdown('<div style="margin-top:1rem;padding:0.75rem 1rem;background:var(--navy-l);border:1px solid #b8cde0;font-size:0.78rem;color:var(--navy)">Analysis complete. Go to <b>Export & Reports</b> in the sidebar to download the full PDF report with appeal letter.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-title">Ready to analyze</div><div class="empty-state-sub">Click <b>Run Prior Auth Analysis</b><br>to see the denial risk assessment here.</div></div>', unsafe_allow_html=True)

        if st.session_state.result_data or st.session_state.result_raw:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Start New Submission", key="new_sub"):
                for key in ["step","result_data","result_raw","extracted","uploaded_file_obj","appeal_letter","pdf_bytes","pdf_filename"]:
                    st.session_state[key] = 1 if key=="step" else (None if key in ["result_data","result_raw","uploaded_file_obj","appeal_letter","pdf_bytes","pdf_filename"] else {})
                st.rerun()

# ── PAGE: PATIENT LOOKUP ──────────────────────────────────────────────────────

elif page == "Patient Lookup":
    st.markdown('<div class="page-header"><h1 class="page-title">Patient Lookup</h1><p class="page-sub">Search by patient name or insurance member ID</p></div>', unsafe_allow_html=True)

    records = load_records()

    # search bar
    col_s1, col_s2 = st.columns([1,1], gap="large")
    with col_s1:
        search_name = st.text_input("Search by Patient Name", placeholder="e.g. Jordan Ellis")
    with col_s2:
        search_id = st.text_input("Search by Member ID", placeholder="e.g. 92746158300")

    # find matches
    matched = {}
    if search_name:
        for mid,v in records.items():
            if search_name.lower() in v["patient_name"].lower():
                matched[mid] = v
    elif search_id:
        if search_id in records:
            matched[search_id] = records[search_id]
    else:
        matched = records

    if search_name or search_id:
        if not matched:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">🔎</div><div class="empty-state-title">No patient found</div><div class="empty-state-sub">No submissions match your search.</div></div>', unsafe_allow_html=True)
        else:
            for mid,v in matched.items():
                subs = sorted(v["submissions"],key=lambda x:x["timestamp"],reverse=True)
                latest = subs[0] if subs else None
                level  = latest["risk_level"] if latest else "low"
                score  = latest["risk_score"]  if latest else "-"
                st.markdown(f"""<div style="background:var(--surface);border:1px solid var(--border);padding:1.5rem;margin-bottom:1rem;animation:fadeIn 0.3s ease forwards">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start">
                        <div>
                            <div style="font-family:'DM Serif Display',serif;font-size:1.3rem;color:var(--ink);margin-bottom:0.2rem">{v["patient_name"]}</div>
                            <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:var(--ink3)">Member ID: {mid}</div>
                            <div style="font-size:0.75rem;color:var(--ink3);margin-top:0.25rem">{len(subs)} submission{"s" if len(subs)!=1 else ""} on file</div>
                        </div>
                        <span class="badge badge-{level}">{score} - {level}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                for sub in subs:
                    with st.expander(f"{sub['date']} - {sub['procedure'][:55]} - Score: {sub['risk_score']} ({sub['risk_level'].upper()}) - by {sub.get('submitted_by','Unknown')}"):
                        if sub.get("result"):
                            render_full_result(sub["result"],"")
                        else:
                            st.write("No detailed result stored.")
                        st.markdown("<br>", unsafe_allow_html=True)
                        sub_id = sub["id"]
                        name_safe = re.sub(r'[^a-zA-Z0-9]','_',v["patient_name"])
                        fname = f"PreAuth_{name_safe}_{sub['date'].replace(' ','_')}.pdf"
                        cached_pdf_l, _ = load_report_cache(sub_id)
                        if cached_pdf_l:
                            st.markdown('<div style="font-size:0.75rem;color:var(--green);margin-bottom:0.5rem">Report cached</div>', unsafe_allow_html=True)
                            st.download_button(label="Download PDF Report",data=cached_pdf_l,file_name=fname,mime="application/pdf",key=f"lu_dl_{sub_id}")
                        else:
                            cache_key = f"lu_pdf_{sub_id}"
                            if st.session_state.get(cache_key):
                                st.download_button(label="Download PDF Report",data=st.session_state[cache_key],file_name=fname,mime="application/pdf",key=f"lu_dl_{sub_id}")
                            else:
                                if st.button("Generate PDF Report", key=f"lu_gen_{sub_id}"):
                                    with st.spinner("Generating - cached for future use..."):
                                        pat_data = {"patient_name":v["patient_name"],"insurance_id":mid,"drug_name":sub["procedure"],"diagnosis_code":"","provider_npi":"","clinical_summary":""}
                                        appeal = generate_appeal_letter(pat_data, sub.get("result",{}))
                                        pdf_buf = generate_report_pdf(pat_data, sub.get("result",{}), appeal, sub.get("submitted_by",""))
                                        if pdf_buf:
                                            pdf_bytes = pdf_buf.getvalue()
                                            save_report_cache(sub_id, pdf_bytes, appeal)
                                            st.session_state[cache_key] = pdf_bytes
                                    st.rerun()
    else:
        if records:
            st.markdown('<h4 style="color:var(--ink);font-family:DM Serif Display,serif;margin-bottom:1rem">All Patients on File</h4>', unsafe_allow_html=True)
            for mid,v in records.items():
                subs   = v["submissions"]
                latest = sorted(subs,key=lambda x:x["timestamp"],reverse=True)[0] if subs else None
                level  = latest["risk_level"] if latest else "low"
                score  = latest["risk_score"]  if latest else "-"
                with st.expander(f"{v['patient_name']} - {mid} - {len(subs)} submission{'s' if len(subs)!=1 else ''} - Latest: {score} ({level.upper()})"):
                    for sub in subs:
                        with st.expander(f"{sub['date']} - {sub['procedure'][:50]} - Score: {sub['risk_score']} ({sub['risk_level'].upper()})", expanded=False):
                            if sub.get("result"):
                                render_full_result(sub["result"],"")
                                st.markdown("<br>", unsafe_allow_html=True)
                                sub_id = sub["id"]
                                name_safe = re.sub(r'[^a-zA-Z0-9]','_',v["patient_name"])
                                fname = f"PreAuth_{name_safe}_{sub['date'].replace(' ','_')}.pdf"
                                cached_pdf_t, _ = load_report_cache(sub_id)
                                sess_key_t = f"tbl_pdf_{sub_id}"
                                dl_data_t = cached_pdf_t or st.session_state.get(sess_key_t)
                                if dl_data_t:
                                    st.download_button("Download PDF Report",data=dl_data_t,file_name=fname,mime="application/pdf",key=f"tbl_dl_{sub_id}")
                                else:
                                    if st.button("Generate PDF Report", key=f"tbl_gen_{sub_id}"):
                                        with st.spinner("Generating..."):
                                            pat_data = {"patient_name":v["patient_name"],"insurance_id":mid,"drug_name":sub["procedure"],"diagnosis_code":"","provider_npi":"","clinical_summary":""}
                                            appeal = generate_appeal_letter(pat_data, sub.get("result",{}))
                                            pdf_buf = generate_report_pdf(pat_data, sub.get("result",{}), appeal, sub.get("submitted_by",""))
                                            if pdf_buf:
                                                pdf_bytes = pdf_buf.getvalue()
                                                save_report_cache(sub_id, pdf_bytes, appeal)
                                                st.session_state[sess_key_t] = pdf_bytes
                                        st.rerun()
                            else:
                                st.write("No detailed result stored.")
        else:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">👥</div><div class="empty-state-title">No patients yet</div><div class="empty-state-sub">Submit a prior authorization request to create your first patient record.</div></div>', unsafe_allow_html=True)

# ── PAGE: EXPORT & REPORTS ────────────────────────────────────────────────────

elif page == "Export & Reports":
    st.markdown('<div class="page-header"><h1 class="page-title">Export & Reports</h1><p class="page-sub">Generate and download prior authorization reports with appeal letters</p></div>', unsafe_allow_html=True)

    records = load_records()
    all_subs = [(mid,s,records[mid]["patient_name"]) for mid,v in records.items() for s in v["submissions"]]
    all_subs.sort(key=lambda x: x[1]["timestamp"], reverse=True)

    if not all_subs:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">📄</div><div class="empty-state-title">No reports yet</div><div class="empty-state-sub">Run a prior authorization analysis first, then come here to export the PDF report.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="font-size:0.82rem;color:var(--ink3);margin-bottom:1.5rem">{len(all_subs)} submission{"s" if len(all_subs)!=1 else ""} available for export</p>', unsafe_allow_html=True)

        # current session result at top if available
        if st.session_state.get("result_data"):
            st.markdown('<span class="form-section-label">Current Session</span>', unsafe_allow_html=True)
            data = st.session_state.result_data
            score = data.get("risk_score",0)
            level = risk_class(score)
            pname = st.session_state.extracted.get("patient_name","Unknown Patient")
            proc  = st.session_state.extracted.get("drug_name","Unknown Procedure")
            st.markdown(f"""<div class="export-card" style="border-left:3px solid var(--navy)">
                <div class="export-card-title">{pname}</div>
                <div class="export-card-meta">{proc} &nbsp;|&nbsp; Risk Score: <b>{score}</b> &nbsp;|&nbsp; <span class="badge badge-{level}">{level}</span></div>
                <div style="font-size:0.78rem;color:var(--ink3);margin-bottom:1rem">{data.get("summary","")[:150]}...</div>
            </div>""", unsafe_allow_html=True)

            # find submission id for current session
            current_sub_id = None
            cur_mid = st.session_state.extracted.get("insurance_id","UNKNOWN")
            if cur_mid in records:
                subs_sorted = sorted(records[cur_mid]["submissions"],key=lambda x:x["timestamp"],reverse=True)
                if subs_sorted: current_sub_id = subs_sorted[0]["id"]

            # check cache first
            cached_pdf, cached_letter = (None, None)
            if current_sub_id:
                cached_pdf, cached_letter = load_report_cache(current_sub_id)

            # always check cache + session for download availability
            dl_bytes = cached_pdf or st.session_state.get("pdf_bytes")
            name_safe = re.sub(r'[^a-zA-Z0-9]','_',pname)

            if not dl_bytes:
                if st.button("Generate Report + Appeal Letter", key="gen_current"):
                    with st.spinner("Writing appeal letter and building PDF..."):
                        appeal = generate_appeal_letter(st.session_state.extracted, data)
                        st.session_state.appeal_letter = appeal
                        pdf_buf = generate_report_pdf(st.session_state.extracted, data, appeal, st.session_state.current_user.get("name",""))
                        if pdf_buf:
                            pdf_bytes = pdf_buf.getvalue()
                            st.session_state.pdf_bytes = pdf_bytes
                            st.session_state.pdf_filename = f"PreAuth_{name_safe}_{datetime.now().strftime('%Y%m%d')}.pdf"
                            if current_sub_id:
                                save_report_cache(current_sub_id, pdf_bytes, appeal)
                    st.rerun()
            else:
                st.markdown('<div style="font-size:0.75rem;color:var(--green);margin-bottom:0.5rem">Report ready to download</div>', unsafe_allow_html=True)
                st.download_button(
                    label="Download Full Report PDF",
                    data=dl_bytes,
                    file_name=st.session_state.get("pdf_filename", f"PreAuth_{name_safe}.pdf"),
                    mime="application/pdf",
                    key="dl_current"
                )

            # show cached letter if available
            if cached_letter and not st.session_state.get("appeal_letter"):
                st.session_state.appeal_letter = cached_letter

            if st.session_state.get("appeal_letter"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<span class="form-section-label">Appeal Letter Preview</span>', unsafe_allow_html=True)
                clean = re.sub(r'#{1,6}\s*','',st.session_state.appeal_letter)
                st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);padding:3rem 4rem;font-size:0.88rem;color:var(--ink2);line-height:2;white-space:pre-wrap;font-family:Georgia,serif;max-height:600px;overflow-y:auto;box-shadow:0 2px 8px rgba(0,0,0,0.04)">{clean}</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border:none;border-top:1px solid var(--border);margin:2rem 0">', unsafe_allow_html=True)

        # all past submissions
        st.markdown('<span class="form-section-label">All Past Submissions</span>', unsafe_allow_html=True)
        for i,(mid,sub,pname) in enumerate(all_subs[:20]):
            level = sub["risk_level"]
            score = sub["risk_score"]
            with st.expander(f"{pname} - {sub['procedure'][:50]} - {sub['date']} - Score: {score} ({level.upper()})"):
                render_full_result(sub.get("result"),"")
                st.markdown("<br>", unsafe_allow_html=True)
                sub_id = sub["id"]
                cached_pdf_p, cached_letter_p = load_report_cache(sub_id)
                name_safe = re.sub(r'[^a-zA-Z0-9]','_',pname)
                fname = f"PreAuth_{name_safe}_{sub['date'].replace(' ','_')}.pdf"

                sess_key = f"exp_pdf_{sub_id}"
                dl_data = cached_pdf_p or st.session_state.get(sess_key)
                if dl_data:
                    st.markdown('<div style="font-size:0.75rem;color:var(--green);margin-bottom:0.5rem">Report ready</div>', unsafe_allow_html=True)
                    st.download_button(label="Download PDF Report",data=dl_data,file_name=fname,mime="application/pdf",key=f"dl_{i}_{sub_id}")
                else:
                    if st.button(f"Generate PDF Report", key=f"gen_{i}_{sub_id}"):
                        with st.spinner("Generating - will be cached for future use..."):
                            pat_data = {"patient_name":pname,"insurance_id":mid,"drug_name":sub["procedure"],"diagnosis_code":"","provider_npi":"","clinical_summary":""}
                            appeal = generate_appeal_letter(pat_data, sub.get("result",{}))
                            pdf_buf = generate_report_pdf(pat_data, sub.get("result",{}), appeal, sub.get("submitted_by",""))
                            if pdf_buf:
                                pdf_bytes = pdf_buf.getvalue()
                                save_report_cache(sub_id, pdf_bytes, appeal)
                                st.session_state[sess_key] = pdf_bytes
                        st.rerun()
