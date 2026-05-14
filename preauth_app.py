import streamlit as st
import requests
import json
import time

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PreAuth.ai",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
DIFY_API_KEY = "app-m5IsSXtmAidl4hOxSJjLnKkO"  # your app key
DIFY_BASE_URL = "http://localhost/v1"

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --white: #ffffff;
    --off-white: #f8f7f4;
    --light-gray: #f0eeea;
    --mid-gray: #c8c4bc;
    --text-dark: #1a1917;
    --text-mid: #4a4844;
    --text-light: #8a8680;
    --accent: #1a3a5c;
    --accent-light: #e8f0f8;
    --success: #1a5c3a;
    --success-light: #e8f8f0;
    --warning: #5c3a1a;
    --warning-light: #f8f0e8;
    --danger: #5c1a1a;
    --danger-light: #f8e8e8;
    --border: #e4e1db;
}

* { font-family: 'DM Sans', sans-serif; }

.main { background-color: var(--off-white); }
.block-container { padding: 2rem 3rem; max-width: 1100px; }

/* hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── HEADER ── */
.header-wrap {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2.5rem;
}
.header-logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: -0.02em;
}
.header-sub {
    font-size: 0.8rem;
    color: var(--text-light);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* ── SECTION LABELS ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* ── UPLOAD ZONE ── */
.upload-hint {
    font-size: 0.82rem;
    color: var(--text-light);
    margin-top: 0.4rem;
    line-height: 1.5;
}

/* ── RISK BADGE ── */
.risk-badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.risk-low { background: var(--success-light); color: var(--success); }
.risk-medium { background: var(--warning-light); color: var(--warning); }
.risk-high { background: var(--danger-light); color: var(--danger); }

/* ── SCORE DISPLAY ── */
.score-block {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.score-number {
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    font-weight: 400;
    color: var(--accent);
    line-height: 1;
}
.score-label {
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-top: 0.3rem;
}

/* ── RESULT SECTIONS ── */
.result-section {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.result-section-title {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-bottom: 0.75rem;
}
.result-item {
    font-size: 0.88rem;
    color: var(--text-mid);
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--light-gray);
    line-height: 1.5;
}
.result-item:last-child { border-bottom: none; }
.result-item::before {
    content: "—";
    color: var(--mid-gray);
    margin-right: 0.6rem;
    font-size: 0.75rem;
}

/* ── SUMMARY BOX ── */
.summary-box {
    background: var(--accent-light);
    border-left: 3px solid var(--accent);
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    font-size: 0.88rem;
    color: var(--text-dark);
    line-height: 1.65;
}

/* ── GAP FIX BOX ── */
.gap-fix-box {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 1.5rem;
    font-size: 0.88rem;
    color: var(--text-mid);
    line-height: 1.75;
    white-space: pre-wrap;
}

/* ── DIVIDER ── */
.thin-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 2rem 0;
}

/* ── STREAMLIT OVERRIDES ── */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    padding: 0.6rem 2rem !important;
    text-transform: uppercase !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

.stTextInput > div > div > input {
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    background: var(--white) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    color: var(--text-dark) !important;
    padding: 0.5rem 0.75rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: none !important;
}

.stFileUploader {
    border: 1px dashed var(--mid-gray) !important;
    border-radius: 2px !important;
    background: var(--white) !important;
    padding: 0.5rem !important;
}

div[data-testid="stForm"] {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 1.75rem;
    border-radius: 0;
}

.stSelectbox > div > div {
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    background: var(--white) !important;
}

label {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: var(--text-mid) !important;
}

.stSpinner > div {
    border-top-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def upload_file_to_dify(uploaded_file) -> str | None:
    """Upload a file to Dify and return the file_id."""
    url = f"{DIFY_BASE_URL}/files/upload"
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    data = {"user": "preauth-ui-user"}
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    if response.status_code in (200, 201):
        return response.json().get("id")
    return None


def call_dify_workflow(inputs: dict, uploaded_file=None) -> dict:
    """Call the Dify chatflow API and return parsed response."""
    url = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    workflow_inputs = {
        "patient_name": inputs.get("patient_name", ""),
        "insurance_id": inputs.get("insurance_id", ""),
        "drug_name": inputs.get("drug_name", ""),
        "diagnosis_code": inputs.get("diagnosis_code", ""),
        "provider_npi": inputs.get("provider_npi", ""),
    }

    # handle file upload
    files_payload = []
    if uploaded_file is not None:
        file_id = upload_file_to_dify(uploaded_file)
        if file_id:
            files_payload = [{
                "type": "document",
                "transfer_method": "local_file",
                "upload_file_id": file_id
            }]
            workflow_inputs["uploaded_docs"] = [{
                "type": "document",
                "transfer_method": "local_file",
                "upload_file_id": file_id
            }]

    payload = {
        "inputs": workflow_inputs,
        "query": "analyze this prior authorization request",
        "response_mode": "blocking",
        "user": "preauth-ui-user",
        "files": files_payload
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    return response.json()


def parse_risk_level(score: int) -> str:
    if score < 40:
        return "low"
    elif score < 70:
        return "medium"
    else:
        return "high"


def render_result(answer: str):
    """Try to parse JSON result and render it nicely, fallback to plain text."""
    import re
    cleaned = re.sub(r'```json|```', '', answer).strip()

    try:
        data = json.loads(cleaned)
        score = data.get("risk_score", 0)
        level = data.get("risk_level", parse_risk_level(score)).lower()
        summary = data.get("summary", "")
        denial_reasons = data.get("denial_reasons", [])
        missing_docs = data.get("missing_documentation", [])
        fixes = data.get("recommended_fixes", [])

        # score + badge
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"""
            <div class="score-block">
                <div class="score-number">{score}</div>
                <div class="score-label">Denial Risk Score</div>
                <br>
                <span class="risk-badge risk-{level}">{level} risk</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if summary:
                st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

        # denial reasons
        if denial_reasons:
            items_html = "".join([f'<div class="result-item">{r}</div>' for r in denial_reasons])
            st.markdown(f"""
            <div class="result-section">
                <div class="result-section-title">Denial Reasons</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        # missing documentation
        if missing_docs:
            items_html = "".join([f'<div class="result-item">{r}</div>' for r in missing_docs])
            st.markdown(f"""
            <div class="result-section">
                <div class="result-section-title">Missing Documentation</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        # recommended fixes
        if fixes:
            items_html = "".join([f'<div class="result-item">{r}</div>' for r in fixes])
            st.markdown(f"""
            <div class="result-section">
                <div class="result-section-title">Recommended Fixes</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

    except (json.JSONDecodeError, KeyError):
        # fallback — gap fixer plain text output
        st.markdown(f"""
        <div class="result-section">
            <div class="result-section-title">Action Plan</div>
            <div class="gap-fix-box">{answer}</div>
        </div>
        """, unsafe_allow_html=True)


# ── LAYOUT ────────────────────────────────────────────────────────────────────

# header
st.markdown("""
<div class="header-wrap">
    <div class="header-logo">PreAuth.ai</div>
    <div class="header-sub">Prior Authorization Review System &nbsp;·&nbsp; UnitedHealthcare</div>
</div>
""", unsafe_allow_html=True)

# two column layout
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="section-label">Patient & Request Details</div>', unsafe_allow_html=True)

    with st.form("prior_auth_form"):
        patient_name   = st.text_input("Patient Name", placeholder="e.g. John Smith")
        insurance_id   = st.text_input("Insurance Member ID", placeholder="e.g. UHC123456789")
        drug_name      = st.text_input("Drug or Procedure", placeholder="e.g. Dupixent or Right Knee Arthroscopy")
        diagnosis_code = st.text_input("Diagnosis Code (ICD-10)", placeholder="e.g. J45.50")
        provider_npi   = st.text_input("Provider NPI", placeholder="e.g. 1558734291")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Upload Documents</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Prescription, referral, or insurance card",
            type=["pdf"],
            help="PDF only. Max 15MB."
        )
        st.markdown('<div class="upload-hint">Upload the patient\'s prescription or prior auth packet. The system will extract details automatically.</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Run Prior Auth Review")

with right:
    st.markdown('<div class="section-label">Review Analysis</div>', unsafe_allow_html=True)

    if submitted:
        if not any([patient_name, insurance_id, drug_name, diagnosis_code, uploaded_file]):
            st.warning("Please fill in at least one field or upload a document.")
        else:
            with st.spinner("Analyzing request against UHC payer guidelines..."):
                try:
                    inputs = {
                        "patient_name": patient_name,
                        "insurance_id": insurance_id,
                        "drug_name": drug_name,
                        "diagnosis_code": diagnosis_code,
                        "provider_npi": provider_npi,
                    }
                    result = call_dify_workflow(inputs, uploaded_file)
                    answer = result.get("answer", "")

                    if answer:
                        render_result(answer)
                    else:
                        st.error(f"No response from workflow. Raw: {result}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to Dify. Make sure Docker is running and Dify is up at http://localhost")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.markdown("""
        <div style="
            border: 1px dashed #c8c4bc;
            padding: 3rem 2rem;
            text-align: center;
            background: #ffffff;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">📋</div>
            <div style="font-size: 0.82rem; color: #8a8680; line-height: 1.6;">
                Fill in patient details on the left<br>and click <strong>Run Prior Auth Review</strong><br>to see the denial risk analysis here.
            </div>
        </div>
        """, unsafe_allow_html=True)