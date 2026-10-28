import streamlit as st
import pandas as pd
import json
import sqlite3
from pathlib import Path
from datetime import date, datetime
from io import BytesIO

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = APP_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "lynnewaters.db"

TABLES = {
    "interviews": ["id", "title", "person", "position", "org", "purpose", "date", "status"],
    "findings": ["id", "finding", "description", "priority", "source", "date"],
    "requirements": ["id", "requirement", "category", "description", "priority", "date"],
    "risks": ["id", "risk", "severity", "mitigation", "owner", "status"],
    "opportunities": ["id", "opportunity", "impact", "effort", "estimated_value", "description", "status"],
    "actions": ["id", "action", "owner", "due_date", "priority", "status"],
    "audit_log": ["id", "timestamp", "event", "record_type", "record_id", "details", "actor"],
    "employees": ["id", "employee_number", "full_name", "email", "phone", "department", "job_title", "manager", "employment_type", "start_date", "probation_end", "employment_status", "location", "notes", "created_at"],
    "candidates": ["id", "full_name", "email", "phone", "position", "source", "stage", "interview_date", "score", "notes", "created_at"],
    "vacancies": ["id", "job_title", "department", "hiring_manager", "employment_type", "location", "headcount", "status", "opened_date", "closing_date", "notes"],
    "onboarding": ["id", "employee_name", "job_title", "department", "start_date", "manager", "checklist", "status", "notes"],
    "training": ["id", "employee_name", "department", "course", "provider", "due_date", "completion_date", "status", "notes"],
    "leave_requests": ["id", "employee_name", "leave_type", "start_date", "end_date", "days", "manager", "status", "notes"],
    "document_register": ["id", "filename", "document_type", "related_person", "related_id", "document_date", "expiry_date", "confidentiality", "notes", "uploaded_at", "uploaded_by"],
    "meeting_minutes": ["id", "meeting_date", "meeting_title", "meeting_type", "chairperson", "attendees", "apologies", "agenda", "discussion_notes", "decisions", "action_items", "next_meeting_date", "confidentiality", "created_at"],
    "performance_reviews": ["id", "employee_name", "employee_number", "department", "review_period", "review_date", "reviewer", "goal_progress", "strengths", "development_needs", "overall_rating", "agreed_goals", "follow_up_date", "status", "created_at"],
    "employee_relations": ["id", "case_reference", "opened_date", "case_type", "employee_name", "department", "case_owner", "priority", "status", "next_review_date", "summary", "resolution", "confidentiality", "created_at"],
    "attendance": ["id", "employee_name", "employee_number", "department", "work_date", "attendance_status", "hours", "manager", "notes", "created_at"],
    "offboarding": ["id", "employee_name", "employee_number", "department", "job_title", "last_working_day", "reason_category", "manager", "equipment_return", "system_access_removed", "exit_interview", "final_documents", "status", "notes", "created_at"],
    "hr_policies": ["id", "policy_title", "policy_category", "version", "owner", "effective_date", "review_date", "status", "summary", "acknowledgement_required", "created_at"],
}

def db_connect():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with db_connect() as conn:
        for table, cols in TABLES.items():
            definitions = []
            for col in cols:
                if col == "id":
                    definitions.append('"id" TEXT PRIMARY KEY')
                else:
                    definitions.append(f'"{col}" TEXT')
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(definitions)})')

def load_records(table):
    with db_connect() as conn:
        rows = conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid DESC').fetchall()
        names = [d[0] for d in conn.execute(f'SELECT * FROM "{table}" LIMIT 0').description]
    return [dict(zip(names, row)) for row in rows]

def save_record(table, record):
    cols = TABLES[table]
    values = [str(record.get(c, "")) for c in cols]
    placeholders = ", ".join(["?"] * len(cols))
    quoted_cols = ", ".join([f'"{c}"' for c in cols])
    with db_connect() as conn:
        conn.execute(f'INSERT OR REPLACE INTO "{table}" ({quoted_cols}) VALUES ({placeholders})', values)

def delete_record(table, record_id):
    with db_connect() as conn:
        conn.execute(f'DELETE FROM "{table}" WHERE id = ?', (record_id,))

def update_record(table, record_id, field, value):
    if field not in TABLES[table]:
        return
    with db_connect() as conn:
        conn.execute(f'UPDATE "{table}" SET "{field}" = ? WHERE id = ?', (str(value), record_id))

def log_audit(event, record_type="workspace", record_id="", details="", actor="Workspace user"):
    """Append an audit event. Audit entries are append-only through the application UI."""
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": str(event),
        "record_type": str(record_type),
        "record_id": str(record_id),
        "details": str(details)[:1000],
        "actor": str(actor),
    }
    with db_connect() as conn:
        conn.execute(
            'INSERT INTO "audit_log" ("id","timestamp","event","record_type","record_id","details","actor") VALUES (?,?,?,?,?,?,?)',
            [entry.get(c, "") for c in TABLES["audit_log"]]
        )

init_db()

st.set_page_config(
    page_title="Lynnewaters HR Management Console",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; --navy:#050d1b; --panel:rgba(10,27,51,.72); --line:rgba(49,190,255,.25); --cyan:#35d9ff; --blue:#3986ff; --muted:#8aa8c5; }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
.stApp { background: radial-gradient(ellipse at 78% 0%,rgba(0,154,255,.14),transparent 35%), radial-gradient(ellipse at 8% 75%,rgba(0,82,255,.10),transparent 32%), linear-gradient(145deg,#030916 0%,#071429 55%,#050d1b 100%); color:#eaf6ff; }
.stApp:before { content:""; position:fixed; inset:0; pointer-events:none; background-image:linear-gradient(rgba(67,155,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(67,155,255,.025) 1px,transparent 1px); background-size:38px 38px; mask-image:linear-gradient(to bottom,black,transparent 85%); }
[data-testid="stHeader"] { background:rgba(3,9,22,.68); backdrop-filter:blur(18px); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,rgba(5,17,36,.97),rgba(4,12,27,.94)); border-right:1px solid rgba(53,217,255,.22); box-shadow:8px 0 40px rgba(0,0,0,.18); }
[data-testid="stSidebar"] > div:first-child { background:transparent; }
[data-testid="stSidebar"] h2 { color:#eaf8ff!important; letter-spacing:.08em; text-shadow:0 0 20px rgba(53,217,255,.22); }
[data-testid="stSidebar"] [data-testid="stRadio"] label { color:#a4bfd7; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label { padding:8px 10px; margin:2px 0; border:1px solid transparent; border-radius:10px; transition:all .2s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover { background:rgba(27,132,255,.12); border-color:rgba(53,217,255,.18); color:#fff; }
h1,h2,h3,h4 { color:#f2f9ff!important; letter-spacing:-.025em; }
.eyebrow { color:var(--cyan); font-size:.72rem; letter-spacing:.18em; font-weight:800; text-transform:uppercase; text-shadow:0 0 16px rgba(53,217,255,.24); }
.hero-title { font-size:clamp(1.8rem,3vw,2.5rem); font-weight:800; margin:.15rem 0 1.2rem; color:#f5fbff; letter-spacing:-.045em; text-shadow:0 0 32px rgba(45,153,255,.13); }
.metric-card { position:relative; overflow:hidden; background:linear-gradient(135deg,rgba(14,43,76,.78),rgba(5,18,38,.76)); border:1px solid rgba(53,196,255,.28); border-radius:17px; padding:18px 20px; min-height:112px; box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 12px 35px rgba(0,0,0,.18),0 0 22px rgba(0,155,255,.055); backdrop-filter:blur(18px); transition:transform .2s,border-color .2s,box-shadow .2s; }
.metric-card:before { content:""; position:absolute; top:0; left:18px; right:18px; height:1px; background:linear-gradient(90deg,transparent,rgba(53,217,255,.65),transparent); }
.metric-card:hover { transform:translateY(-2px); border-color:rgba(53,217,255,.5); box-shadow:inset 0 1px 0 rgba(255,255,255,.09),0 14px 40px rgba(0,0,0,.22),0 0 28px rgba(0,155,255,.12); }
.metric-label { color:#91b2cf; font-size:.69rem; letter-spacing:.12em; font-weight:700; }
.metric-value { color:#f5fbff; font-size:1.9rem; font-weight:800; margin-top:7px; text-shadow:0 0 22px rgba(53,217,255,.12); }
.panel, div[data-testid="stForm"], div[data-testid="stExpander"] { background:linear-gradient(145deg,rgba(10,29,53,.78),rgba(5,17,35,.72)); border:1px solid rgba(53,190,255,.22); border-radius:17px; padding:18px 20px; margin-bottom:14px; box-shadow:inset 0 1px rgba(255,255,255,.035),0 12px 32px rgba(0,0,0,.14); backdrop-filter:blur(14px); }
div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(12,38,68,.76),rgba(5,18,38,.76)); padding:15px; border:1px solid rgba(53,190,255,.24); border-radius:14px; box-shadow:inset 0 1px rgba(255,255,255,.05),0 0 18px rgba(0,150,255,.04); }
div[data-testid="stMetric"] label { color:#91b2cf!important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#f3fbff; }
div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button { position:relative; overflow:hidden; border-radius:12px; border:1px solid rgba(53,217,255,.5); background:linear-gradient(120deg,rgba(0,111,225,.92),rgba(0,190,226,.86)); color:#fff; font-weight:750; min-height:2.65rem; box-shadow:0 0 18px rgba(0,160,255,.15),inset 0 1px rgba(255,255,255,.15); transition:transform .18s,box-shadow .18s,border-color .18s,filter .18s; }
div.stButton > button:hover, div.stDownloadButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { border-color:#8aeeff; color:#fff; filter:brightness(1.12); transform:translateY(-1px); box-shadow:0 0 24px rgba(0,190,255,.28),inset 0 1px rgba(255,255,255,.2); }
div.stButton > button:focus, div.stDownloadButton > button:focus { outline:2px solid rgba(53,217,255,.5); outline-offset:2px; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div, [data-testid="stMultiSelect"] div[data-baseweb="select"] > div { background:rgba(3,15,32,.78); border-color:rgba(74,177,232,.27); border-radius:10px; color:#eef9ff; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color:var(--cyan); box-shadow:0 0 0 1px rgba(53,217,255,.35),0 0 16px rgba(0,160,255,.1); }
[data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid rgba(53,190,255,.18); border-radius:12px; overflow:hidden; }
[data-testid="stTabs"] button { color:#8faec8; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#52ddff; border-bottom-color:#35d9ff; text-shadow:0 0 15px rgba(53,217,255,.18); }
[data-testid="stAlert"] { background:rgba(10,36,61,.78); border:1px solid rgba(53,190,255,.22); border-radius:12px; }
hr { border-color:rgba(53,190,255,.16); }
small,.stCaption,[data-testid="stCaptionContainer"] { color:#8aa8c5!important; }
#MainMenu, footer { visibility:hidden; }
@media (max-width:800px) { .metric-card { padding:15px; } .metric-value { font-size:1.55rem; } }
@media (prefers-reduced-motion:reduce) { *,*:before,*:after { transition:none!important; animation:none!important; scroll-behavior:auto!important; } }
</style>
""", unsafe_allow_html=True)

for collection in TABLES:
    if collection not in st.session_state:
        st.session_state[collection] = load_records(collection)

def header(section, subtitle=None):
    st.markdown('<div class="eyebrow">LYNNEWATERS · HUMAN RESOURCES MANAGEMENT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-title">{section}</div>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)

def metric_card(label, value):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True
    )

def as_df(rows, columns=None):
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns or [])

def export_csv(rows, filename, columns=None):
    df = as_df(rows, columns)
    if st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=f"download_{filename}",
    ):
        log_audit("EXPORT", "report", filename, f"Exported {len(rows)} rows to CSV")

def go_to_page(page_name):
    st.session_state.main_navigation = page_name

def add_record(collection_key, record):
    if not record.get("id"):
        record["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    save_record(collection_key, record)
    log_audit("CREATE", collection_key, record.get("id", ""), "Created record")
    st.session_state[collection_key] = load_records(collection_key)

with st.sidebar:
    st.markdown("## ◈ LYNNEWATERS")
    st.caption("HR MANAGEMENT CONSOLE")
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        [
            "HR Dashboard", "Employee Directory", "Recruitment Pipeline", "Vacancy Planning",
            "Interview Scorecards", "Onboarding Checklist", "Leave & Absence", "Attendance Register",
            "Performance & Reviews", "Training & Development", "Employee Relations", "Offboarding",
            "HR Policies", "HR Documents", "Meeting Minutes", "HR Action Tracker", "HR Reports", "Audit Log", "Settings"
        ],
        label_visibility="collapsed",
        key="main_navigation",
    )
    st.markdown("---")
    st.caption("Workspace status")
    st.success("Console ready")
    st.caption("Local prototype · Data is stored with this app")

if page == "HR Dashboard":
    header("HR Command Centre", "A practical control panel for the employee lifecycle: hiring, onboarding, attendance, leave, performance, employee relations and exits.")
    interviews = st.session_state.interviews
    findings = st.session_state.findings
    requirements = st.session_state.requirements
    risks = st.session_state.risks
    opportunities = st.session_state.opportunities
    actions = st.session_state.actions
    candidates = st.session_state.candidates
    vacancies = st.session_state.vacancies
    onboarding = st.session_state.onboarding
    training = st.session_state.training
    leave_requests = st.session_state.leave_requests
    employees = st.session_state.employees
    performance_reviews = load_records("performance_reviews")
    employee_relations = load_records("employee_relations")
    offboarding = load_records("offboarding")
    policies = load_records("hr_policies")
    cols = st.columns(6)
    with cols[0]: metric_card("EMPLOYEES", len([e for e in employees if e.get("employment_status") == "Active"]))
    with cols[1]: metric_card("CANDIDATES", len(candidates))
    with cols[2]: metric_card("OPEN VACANCIES", sum(v.get("status") == "Open" for v in vacancies))
    with cols[3]: metric_card("ONBOARDING", sum(o.get("status") != "Complete" for o in onboarding))
    with cols[4]: metric_card("TRAINING DUE", sum(t.get("status") != "Complete" for t in training))
    with cols[5]: metric_card("LEAVE REQUESTS", sum(l.get("status") == "Pending" for l in leave_requests))
    st.write("")
    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Recent Candidates")
        if candidates:
            df = pd.DataFrame(candidates)
            show_cols = [c for c in ["full_name", "position", "stage", "interview_date", "score"] if c in df.columns]
            st.dataframe(df[show_cols].head(6), use_container_width=True, hide_index=True)
        else:
            st.info("No candidates yet. Open Candidates to add your first applicant.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("HR Snapshot")
        st.write(f"**Employees in onboarding:** {sum(o.get('status') != 'Complete' for o in onboarding)}")
        st.write(f"**Pending leave requests:** {sum(l.get('status') == 'Pending' for l in leave_requests)}")
        st.write(f"**Training items in progress:** {sum(t.get('status') != 'Complete' for t in training)}")
        st.write(f"**HR actions outstanding:** {sum(a.get('status') != 'Complete' for a in actions)}")
        st.write(f"**HR documents stored:** {len(list(UPLOAD_DIR.iterdir()))}")
        st.write(f"**Performance reviews:** {len(performance_reviews)}")
        st.write(f"**Open employee-relations cases:** {sum(r.get('status') not in ['Resolved', 'Closed'] for r in employee_relations)}")
        st.write(f"**Offboarding in progress:** {sum(r.get('status') != 'Complete' for r in offboarding)}")
        st.write(f"**HR policies registered:** {len(policies)}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Action Centre")
    st.caption("Jump straight into common HR workflows. Counts above are calculated from records currently in this workspace.")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.button("＋ Start recruitment", use_container_width=True, on_click=go_to_page, args=("Recruitment Pipeline",))
    with q2:
        st.button("✓ Review leave", use_container_width=True, on_click=go_to_page, args=("Leave & Absence",))
    with q3:
        st.button("▦ Employee reviews", use_container_width=True, on_click=go_to_page, args=("Performance & Reviews",))
    with q4:
        st.button("＋ New HR action", use_container_width=True, on_click=go_to_page, args=("HR Action Tracker",))
    st.markdown("</div>", unsafe_allow_html=True)
    st.subheader("Priority Work Queue")
    work_items = []
    work_items.extend([{ "Area": "Leave", "Item": f"{r.get('employee_name','Employee')} · {r.get('leave_type','Leave')}", "Due / date": r.get('start_date',''), "Status": "Pending approval", "Priority": "Review" } for r in leave_requests if r.get("status") == "Pending"])
    work_items.extend([{ "Area": "Onboarding", "Item": r.get('employee_name','New starter'), "Due / date": r.get('start_date',''), "Status": r.get('status',''), "Priority": "Follow up" } for r in onboarding if r.get("status") != "Complete"])
    work_items.extend([{ "Area": "Training", "Item": f"{r.get('employee_name','Employee')} · {r.get('course','Course')}", "Due / date": r.get('due_date',''), "Status": r.get('status',''), "Priority": "Follow up" } for r in st.session_state.training if r.get("status") not in ["Complete", "Cancelled"]])
    work_items.extend([{ "Area": "Employee relations", "Item": r.get('case_reference','Case'), "Due / date": r.get('next_review_date',''), "Status": r.get('status',''), "Priority": r.get('priority','Routine') } for r in employee_relations if r.get("status") not in ["Resolved", "Closed"]])
    work_items.extend([{ "Area": "Performance", "Item": r.get('employee_name','Employee'), "Due / date": r.get('follow_up_date',''), "Status": r.get('status',''), "Priority": "Follow up" } for r in performance_reviews if r.get("status") not in ["Closed"]])
    if work_items:
        st.dataframe(pd.DataFrame(work_items).head(15), use_container_width=True, hide_index=True)
    else:
        st.success("No outstanding workflow items are recorded. Add HR activities to build your work queue.")

elif page in ["Employee Records", "Employee Directory"]:
    header("Employee Directory", "A central register for employee details, employment status and key HR dates. Collect only information needed for HR administration.")
    with st.form("employee_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        employee_number = c1.text_input("Employee number *", placeholder="LW-0001")
        full_name = c2.text_input("Full name *")
        email = c1.text_input("Work email")
        phone = c2.text_input("Contact number")
        department = c1.text_input("Department")
        job_title = c2.text_input("Job title")
        manager = c1.text_input("Line manager")
        employment_type = c2.selectbox("Employment type", ["Permanent", "Fixed-term", "Contract", "Temporary", "Internship", "Part-time"])
        start_date = c1.date_input("Employment start date", value=date.today())
        probation_end = c2.date_input("Probation end date (if applicable)", value=date.today())
        employment_status = c1.selectbox("Employment status", ["Active", "On leave", "Probation", "Suspended", "Terminated", "Resigned"])
        location = c2.text_input("Work location")
        notes = st.text_area("HR administration notes", help="Do not enter passwords, bank details, medical information or other unnecessary sensitive data.")
        submitted = st.form_submit_button("Add Employee Record")
        if submitted:
            if not employee_number.strip() or not full_name.strip():
                st.error("Employee number and full name are required.")
            elif any(e.get("employee_number", "").strip().lower() == employee_number.strip().lower() for e in st.session_state.employees):
                st.error("That employee number already exists. Use a unique employee number.")
            else:
                add_record("employees", {
                    "employee_number": employee_number.strip(), "full_name": full_name.strip(),
                    "email": email.strip(), "phone": phone.strip(), "department": department.strip(),
                    "job_title": job_title.strip(), "manager": manager.strip(), "employment_type": employment_type,
                    "start_date": start_date.isoformat(), "probation_end": probation_end.isoformat() if employment_type in ["Permanent", "Fixed-term", "Contract", "Temporary"] else "",
                    "employment_status": employment_status, "location": location.strip(), "notes": notes.strip(),
                    "created_at": datetime.now().isoformat(timespec="minutes")
                })
                st.success("Employee record added and audit event recorded.")
                st.rerun()

    employees = st.session_state.employees
    st.subheader("Employee Register")
    if employees:
        df = pd.DataFrame(employees)
        visible = [c for c in ["employee_number", "full_name", "department", "job_title", "manager", "employment_type", "start_date", "probation_end", "employment_status", "location", "email", "phone"] if c in df.columns]
        search = st.text_input("Search employees", placeholder="Name, employee number, department or job title")
        if search.strip():
            mask = df[visible].fillna("").astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, regex=False)).any(axis=1)
            df = df[mask]
        st.dataframe(df[visible], use_container_width=True, hide_index=True)
        export_csv(df.to_dict(orient="records"), "lynnewaters_hr_employee_register.csv", visible)
        st.markdown("#### Update employment status")
        by_id = {f"{e.get('employee_number')} · {e.get('full_name')}": e for e in employees}
        selected_label = st.selectbox("Select employee", list(by_id.keys()), key="employee_status_select")
        selected = by_id[selected_label]
        new_status = st.selectbox("New status", ["Active", "On leave", "Probation", "Suspended", "Terminated", "Resigned"], index=["Active", "On leave", "Probation", "Suspended", "Terminated", "Resigned"].index(selected.get("employment_status", "Active")) if selected.get("employment_status", "Active") in ["Active", "On leave", "Probation", "Suspended", "Terminated", "Resigned"] else 0, key="employee_new_status")
        if st.button("Save employment status", key="save_employee_status"):
            old_status = selected.get("employment_status", "")
            if old_status != new_status:
                update_record("employees", selected["id"], "employment_status", new_status)
                log_audit("UPDATE", "employees", selected["id"], f"Employment status changed from {old_status} to {new_status}")
                st.session_state.employees = load_records("employees")
                st.success("Employment status updated and audit event recorded.")
                st.rerun()
            else:
                st.info("No change to save.")
        st.markdown("#### Remove an employee record")
        st.caption("Use only for duplicate or incorrectly created records. Retention and deletion rules should be approved by HR before production use.")
        confirm_delete = st.checkbox("I confirm this employee record should be deleted", key="confirm_employee_delete")
        if st.button("Delete selected employee", type="secondary", key="delete_employee"):
            if not confirm_delete:
                st.warning("Confirm deletion first.")
            else:
                log_audit("DELETE", "employees", selected["id"], f"Deleted employee record {selected.get('employee_number')} · {selected.get('full_name')}")
                delete_record("employees", selected["id"])
                st.session_state.employees = load_records("employees")
                st.success("Employee record deleted and audit event recorded.")
                st.rerun()
    else:
        st.info("No employee records yet. Add the first employee using the form above.")

elif page in ["Candidates", "Recruitment Pipeline"]:
    header("Recruitment Pipeline", "Manage applicants from application to hiring decision from application to hiring decision.")
    with st.form("candidate_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Candidate full name *")
        email = c2.text_input("Email address")
        phone = c1.text_input("Phone number")
        position = c2.text_input("Position applied for *")
        source = c1.selectbox("Application source", ["Company website", "Job board", "Referral", "Recruiter", "Walk-in", "Other"])
        stage = c2.selectbox("Recruitment stage", ["New", "Screening", "Shortlisted", "Interview", "Reference checks", "Offer", "Hired", "Rejected", "Withdrawn"])
        interview_date = c1.date_input("Interview date (if scheduled)", value=date.today())
        score = c2.selectbox("Interview score", ["Not assessed", "1 - Does not meet criteria", "2 - Partially meets criteria", "3 - Meets criteria", "4 - Exceeds criteria", "5 - Strongly exceeds criteria"])
        notes = st.text_area("Job-related notes / next step")
        if st.form_submit_button("Add Candidate"):
            if not full_name.strip() or not position.strip(): st.error("Candidate name and position are required.")
            else:
                add_record("candidates", {"full_name":full_name.strip(),"email":email.strip(),"phone":phone.strip(),"position":position.strip(),"source":source,"stage":stage,"interview_date":interview_date.isoformat(),"score":score,"notes":notes.strip(),"created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Candidate added."); st.rerun()
    rows=st.session_state.candidates
    if rows:
        st.dataframe(pd.DataFrame(rows).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True)
        export_csv(rows,"lynnewaters_hr_candidates.csv")
    else: st.info("No candidates recorded yet.")

elif page in ["Vacancies", "Vacancy Planning"]:
    header("Vacancy Planning", "Track approved roles, hiring owners and recruitment status.")
    with st.form("vacancy_form", clear_on_submit=True):
        c1,c2=st.columns(2)
        job_title=c1.text_input("Job title *"); department=c2.text_input("Department")
        manager=c1.text_input("Hiring manager"); employment_type=c2.selectbox("Employment type",["Permanent","Fixed-term","Contract","Temporary","Internship","Part-time"])
        location=c1.text_input("Work location"); headcount=c2.number_input("Number of positions",min_value=1,value=1)
        status=c1.selectbox("Vacancy status",["Draft","Open","On hold","Filled","Cancelled"])
        opened=c2.date_input("Opening date",value=date.today()); closing=c1.date_input("Closing date",value=date.today())
        notes=st.text_area("Role summary / requirements")
        if st.form_submit_button("Add Vacancy"):
            if not job_title.strip(): st.error("Enter a job title.")
            else:
                add_record("vacancies",{"job_title":job_title.strip(),"department":department.strip(),"hiring_manager":manager.strip(),"employment_type":employment_type,"location":location.strip(),"headcount":headcount,"status":status,"opened_date":opened.isoformat(),"closing_date":closing.isoformat(),"notes":notes.strip()}); st.success("Vacancy added."); st.rerun()
    if st.session_state.vacancies:
        st.dataframe(pd.DataFrame(st.session_state.vacancies).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(st.session_state.vacancies,"lynnewaters_hr_vacancies.csv")
    else: st.info("No vacancies recorded yet.")

elif page in ["Onboarding", "Onboarding Checklist"]:
    header("Onboarding Checklist", "Coordinate new-starter preparation and track completion of onboarding tasks.")
    with st.form("onboarding_form", clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); job=c2.text_input("Job title")
        department=c1.text_input("Department"); manager=c2.text_input("Line manager")
        start=date.today(); start=c1.date_input("Start date",value=start)
        checklist=c2.multiselect("Onboarding checklist",["Contract issued","ID / right-to-work verified","Payroll setup","Equipment prepared","System access","Policies acknowledged","Health & safety induction","Team introduction"])
        status=c1.selectbox("Status",["Not started","In progress","Complete","On hold"]); notes=st.text_area("Notes (avoid unnecessary sensitive data)")
        if st.form_submit_button("Add Onboarding Record"):
            if not employee.strip(): st.error("Employee name is required.")
            else:
                add_record("onboarding",{"employee_name":employee.strip(),"job_title":job.strip(),"department":department.strip(),"start_date":start.isoformat(),"manager":manager.strip(),"checklist":"; ".join(checklist),"status":status,"notes":notes.strip()}); st.success("Onboarding record added."); st.rerun()
    if st.session_state.onboarding:
        st.dataframe(pd.DataFrame(st.session_state.onboarding).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(st.session_state.onboarding,"lynnewaters_hr_onboarding.csv")
    else: st.info("No onboarding records yet.")

elif page == "Training & Development":
    header("Training & Development", "Plan learning activities and monitor completion and due dates.")
    with st.form("training_form", clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); department=c2.text_input("Department")
        course=c1.text_input("Course / development activity *"); provider=c2.text_input("Provider")
        due=c1.date_input("Due date",value=date.today()); completion=c2.date_input("Completion date (if complete)",value=date.today())
        status=c1.selectbox("Status",["Planned","In progress","Complete","Overdue","Cancelled"]); notes=st.text_area("Notes")
        if st.form_submit_button("Add Training Record"):
            if not employee.strip() or not course.strip(): st.error("Employee name and course are required.")
            else:
                add_record("training",{"employee_name":employee.strip(),"department":department.strip(),"course":course.strip(),"provider":provider.strip(),"due_date":due.isoformat(),"completion_date":completion.isoformat() if status=="Complete" else "","status":status,"notes":notes.strip()}); st.success("Training record added."); st.rerun()
    if st.session_state.training:
        st.dataframe(pd.DataFrame(st.session_state.training).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(st.session_state.training,"lynnewaters_hr_training.csv")
    else: st.info("No training records yet.")

elif page in ["Leave Management", "Leave & Absence"]:
    header("Leave & Absence", "Manage leave requests, approval decisions and absence visibility and track manager decisions. This is a tracker, not a payroll or statutory leave calculator.")
    with st.form("leave_form", clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); leave_type=c2.selectbox("Leave type",["Annual","Sick","Family responsibility","Maternity / parental","Unpaid","Study","Other"])
        start=c1.date_input("Start date",value=date.today()); end=c2.date_input("End date",value=date.today())
        days=c1.number_input("Working days requested",min_value=0.5,step=0.5,value=1.0); manager=c2.text_input("Approving manager")
        status=c1.selectbox("Decision status",["Pending","Approved","Declined","Cancelled"]); notes=st.text_area("Administrative notes (do not record medical details)")
        if st.form_submit_button("Add Leave Request"):
            if not employee.strip(): st.error("Employee name is required.")
            elif end < start: st.error("End date cannot be before start date.")
            else:
                add_record("leave_requests",{"employee_name":employee.strip(),"leave_type":leave_type,"start_date":start.isoformat(),"end_date":end.isoformat(),"days":days,"manager":manager.strip(),"status":status,"notes":notes.strip()}); st.success("Leave request added."); st.rerun()
    if st.session_state.leave_requests:
        st.dataframe(pd.DataFrame(st.session_state.leave_requests).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(st.session_state.leave_requests,"lynnewaters_hr_leave_requests.csv")
    else: st.info("No leave requests recorded yet.")

elif page == "Interview Scorecards":
    header("Interview Scorecards", "Record structured, job-related interview assessments. Apply the same criteria consistently to each candidate.")
    with st.form("new_interview_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Interview title", placeholder="Business Discovery Interview")
        person = c2.text_input("Interviewee name")
        position = c1.text_input("Position / role")
        org = c2.text_input("Organisation")
        purpose = st.text_area("Interview purpose")
        interview_date = st.date_input("Interview date", value=date.today())
        submitted = st.form_submit_button("＋ Create Interview", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Please enter an interview title.")
            else:
                record = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "title": title.strip(),
                    "person": person.strip() or "Not specified",
                    "position": position.strip() or "Not specified",
                    "org": org.strip() or "Not specified",
                    "purpose": purpose.strip(),
                    "date": interview_date.isoformat(),
                    "status": "Active",
                }
                save_record("interviews", record)
                log_audit("CREATE", "interviews", record["id"], "Created interview: " + record["title"])
                st.session_state.interviews = load_records("interviews")
                st.success("Interview created.")
                st.rerun()
    st.subheader("Interview Register")
    if st.session_state.interviews:
        df = pd.DataFrame(st.session_state.interviews)
        st.dataframe(df.drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)
        export_csv(st.session_state.interviews, "lynnewaters_interviews.csv")
        ids = {f"{i['title']} — {i['person']} ({i['date']})": i["id"] for i in st.session_state.interviews}
        selected_label = st.selectbox("Select an interview to remove", ["— Select —"] + list(ids))
        if selected_label != "— Select —" and st.button("Delete selected interview"):
            selected_id = ids[selected_label]
            log_audit("DELETE", "interviews", selected_id, f"Deleted interview: {selected_label}")
            delete_record("interviews", selected_id)
            st.session_state.interviews = load_records("interviews")
            st.success("Interview deleted.")
            st.rerun()
    else:
        st.info("Your interview register is empty.")

elif page == "HR Documents":
    header("HR Document Register", "A searchable register for HR documents gathered during recruitment and employee administration. Upload only documents you are authorised to retain.")
    st.info("For privacy, avoid storing unnecessary identity, banking, medical or other sensitive personal information. Restrict access before using real employee files.")
    employees = st.session_state.get("employees", [])
    candidates = st.session_state.get("candidates", [])
    people = [f"Employee · {e.get('full_name','')} ({e.get('employee_number','')})" for e in employees]
    people += [f"Candidate · {c.get('full_name','')} ({c.get('position','')})" for c in candidates]
    with st.form("hr_document_upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Choose document(s)",
            type=["pdf", "doc", "docx", "txt", "csv", "xlsx", "xls", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Accepted formats: PDF, Word, text, CSV, Excel and common image files."
        )
        c1, c2 = st.columns(2)
        document_type = c1.selectbox("Document category", [
            "CV / Resume", "Application Form", "Interview Notes", "Offer Letter", "Employment Contract",
            "ID / Work Eligibility", "Qualification / Certificate", "Reference Check", "Onboarding Form",
            "Policy Acknowledgement", "Training Record", "Performance Review", "Leave Form", "Disciplinary Record",
            "Other HR Document"
        ])
        related_person = c2.selectbox("Related person (optional)", ["Not linked"] + people)
        c3, c4 = st.columns(2)
        document_date = c3.date_input("Document date", value=date.today())
        expiry_date = c4.date_input("Expiry / review date (optional)", value=None)
        confidentiality = st.selectbox("Handling level", ["Internal", "Confidential HR", "Highly restricted"])
        notes = st.text_area("Notes (avoid sensitive details)", placeholder="Purpose, source or follow-up needed")
        submitted = st.form_submit_button("Upload and register documents")
        if submitted:
            if not uploaded_files:
                st.error("Choose at least one document to upload.")
            else:
                related_id = ""
                if related_person != "Not linked":
                    try:
                        label = related_person.split(" · ", 1)[1]
                        related_id = label.rsplit("(", 1)[-1].rstrip(")")
                    except Exception:
                        related_id = ""
                saved_count = 0
                for file in uploaded_files:
                    original_name = Path(file.name).name
                    # Avoid overwriting a different file with the same name.
                    target = UPLOAD_DIR / original_name
                    if target.exists():
                        target = UPLOAD_DIR / f"{Path(original_name).stem}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{Path(original_name).suffix}"
                    target.write_bytes(file.getvalue())
                    doc_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    record = {
                        "id": doc_id, "filename": target.name, "document_type": document_type,
                        "related_person": related_person if related_person != "Not linked" else "",
                        "related_id": related_id, "document_date": document_date.isoformat(),
                        "expiry_date": expiry_date.isoformat() if expiry_date else "",
                        "confidentiality": confidentiality, "notes": notes.strip(),
                        "uploaded_at": datetime.now().isoformat(timespec="seconds"), "uploaded_by": "Workspace user"
                    }
                    save_record("document_register", record)
                    log_audit("UPLOAD", "documents", doc_id, f"Registered {document_type}: {target.name}; handling={confidentiality}")
                    saved_count += 1
                st.success(f"Uploaded and registered {saved_count} document(s).")
                st.session_state["document_register"] = load_records("document_register")
                st.rerun()

    docs = load_records("document_register")
    disk_files = {p.name: p for p in UPLOAD_DIR.iterdir() if p.is_file()}
    # Surface any files from earlier versions that pre-date the document register.
    registered_names = {d.get("filename") for d in docs}
    legacy = [{"id": "legacy-" + name, "filename": name, "document_type": "Legacy upload", "related_person": "", "related_id": "", "document_date": "", "expiry_date": "", "confidentiality": "Unclassified", "notes": "Uploaded before the document register was introduced.", "uploaded_at": "", "uploaded_by": ""} for name in disk_files if name not in registered_names]
    docs = docs + legacy
    st.subheader("Documents gathered")
    f1, f2, f3 = st.columns([1.3, 1, 1])
    with f1:
        search_doc = st.text_input("Search documents", placeholder="Filename, person or notes")
    with f2:
        type_filter = st.selectbox("Category filter", ["All"] + sorted({d.get("document_type", "") for d in docs if d.get("document_type")}))
    with f3:
        expiry_filter = st.selectbox("Expiry / review", ["All", "Has date", "No date", "Expired / due"])
    filtered_docs = docs
    if search_doc.strip():
        term = search_doc.lower().strip()
        filtered_docs = [d for d in filtered_docs if term in " ".join(str(d.get(k, "")) for k in ["filename", "related_person", "document_type", "notes"]).lower()]
    if type_filter != "All":
        filtered_docs = [d for d in filtered_docs if d.get("document_type") == type_filter]
    today = date.today().isoformat()
    if expiry_filter == "Has date":
        filtered_docs = [d for d in filtered_docs if d.get("expiry_date")]
    elif expiry_filter == "No date":
        filtered_docs = [d for d in filtered_docs if not d.get("expiry_date")]
    elif expiry_filter == "Expired / due":
        filtered_docs = [d for d in filtered_docs if d.get("expiry_date") and d.get("expiry_date") <= today]
    st.caption(f"Showing {len(filtered_docs)} of {len(docs)} document(s).")
    if filtered_docs:
        view_rows = [{k: d.get(k, "") for k in ["filename", "document_type", "related_person", "document_date", "expiry_date", "confidentiality", "uploaded_at", "notes"]} for d in filtered_docs]
        st.dataframe(pd.DataFrame(view_rows), use_container_width=True, hide_index=True)
        st.download_button("Export document register (CSV)", pd.DataFrame(view_rows).to_csv(index=False).encode("utf-8-sig"), file_name="lynnewaters_hr_document_register.csv", mime="text/csv", on_click=lambda: log_audit("EXPORT", "documents", "document_register.csv", f"Exported {len(view_rows)} document register rows"))
        st.markdown("**Download stored files**")
        for d in filtered_docs:
            path = disk_files.get(d.get("filename", ""))
            if path:
                label = f"Download: {d.get('filename')} · {d.get('document_type', 'Document')}"
                st.download_button(label, path.read_bytes(), file_name=path.name, key=f"hrdoc_download_{d.get('id')}", on_click=lambda doc=d: log_audit("DOWNLOAD", "documents", doc.get("id", ""), f"Downloaded {doc.get('filename', '')}"))
    else:
        st.info("No matching documents yet. Upload and register the first document above.")

elif page == "Meeting Minutes":
    header("Meeting Minutes", "Create, organise and retrieve formal HR meeting records, decisions and follow-up actions.")
    st.info("Keep minutes factual and work-related. Do not include unnecessary sensitive employee details. Access should be restricted before using real confidential records.")
    with st.form("meeting_minutes_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        meeting_title = c1.text_input("Meeting title *", placeholder="e.g. Monthly HR Operations Meeting")
        meeting_date = c2.date_input("Meeting date", value=date.today())
        c3, c4 = st.columns(2)
        meeting_type = c3.selectbox("Meeting type", ["HR Operations", "Recruitment", "Workforce Planning", "Employee Relations", "Training & Development", "Health & Safety", "Performance Review", "Other"])
        chairperson = c4.text_input("Chairperson / meeting lead")
        c5, c6 = st.columns(2)
        attendees = c5.text_area("Attendees", placeholder="Names or roles, separated by commas")
        apologies = c6.text_area("Apologies / absentees", placeholder="Names or roles, separated by commas")
        agenda = st.text_area("Agenda", placeholder="List the topics discussed")
        discussion_notes = st.text_area("Discussion notes", placeholder="Summarise key points objectively")
        decisions = st.text_area("Decisions made", placeholder="Record agreed decisions and owners where relevant")
        action_items = st.text_area("Actions, owners and due dates", placeholder="Action — owner — due date")
        c7, c8 = st.columns(2)
        next_meeting_date = c7.date_input("Next meeting date (optional)", value=None)
        confidentiality = c8.selectbox("Confidentiality", ["Internal", "Confidential HR", "Highly restricted"])
        submitted = st.form_submit_button("Save meeting minutes")
        if submitted:
            if not meeting_title.strip():
                st.error("Enter a meeting title before saving.")
            else:
                meeting_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                record = {
                    "id": meeting_id, "meeting_date": meeting_date.isoformat(), "meeting_title": meeting_title.strip(),
                    "meeting_type": meeting_type, "chairperson": chairperson.strip(), "attendees": attendees.strip(),
                    "apologies": apologies.strip(), "agenda": agenda.strip(), "discussion_notes": discussion_notes.strip(),
                    "decisions": decisions.strip(), "action_items": action_items.strip(),
                    "next_meeting_date": next_meeting_date.isoformat() if next_meeting_date else "",
                    "confidentiality": confidentiality, "created_at": datetime.now().isoformat(timespec="seconds")
                }
                save_record("meeting_minutes", record)
                log_audit("CREATE", "meeting_minutes", meeting_id, f"Saved minutes: {meeting_title.strip()}; confidentiality={confidentiality}")
                st.session_state["meeting_minutes"] = load_records("meeting_minutes")
                st.success("Meeting minutes saved.")
                st.rerun()

    minutes = load_records("meeting_minutes")
    st.subheader("Saved meeting minutes")
    f1, f2 = st.columns([1.5, 1])
    with f1:
        minutes_search = st.text_input("Search minutes", placeholder="Title, attendee, decision or action")
    with f2:
        minutes_type_filter = st.selectbox("Meeting type filter", ["All"] + sorted({m.get("meeting_type", "") for m in minutes if m.get("meeting_type")}))
    filtered_minutes = minutes
    if minutes_search.strip():
        term = minutes_search.lower().strip()
        fields = ["meeting_title", "meeting_type", "chairperson", "attendees", "apologies", "agenda", "discussion_notes", "decisions", "action_items"]
        filtered_minutes = [m for m in filtered_minutes if term in " ".join(str(m.get(k, "")) for k in fields).lower()]
    if minutes_type_filter != "All":
        filtered_minutes = [m for m in filtered_minutes if m.get("meeting_type") == minutes_type_filter]
    st.caption(f"Showing {len(filtered_minutes)} of {len(minutes)} meeting record(s).")
    if filtered_minutes:
        summary_rows = [{k: m.get(k, "") for k in ["meeting_date", "meeting_title", "meeting_type", "chairperson", "attendees", "decisions", "action_items", "next_meeting_date", "confidentiality", "created_at"]} for m in filtered_minutes]
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
        st.download_button("Export minutes register (CSV)", pd.DataFrame(summary_rows).to_csv(index=False).encode("utf-8-sig"), file_name="lynnewaters_meeting_minutes.csv", mime="text/csv", on_click=lambda: log_audit("EXPORT", "meeting_minutes", "meeting_minutes.csv", f"Exported {len(summary_rows)} meeting records"))
        for m in filtered_minutes:
            with st.expander(f"{m.get('meeting_date', '')} · {m.get('meeting_title', 'Meeting')}"):
                for label, field in [("Meeting type", "meeting_type"), ("Chairperson", "chairperson"), ("Attendees", "attendees"), ("Apologies", "apologies"), ("Agenda", "agenda"), ("Discussion notes", "discussion_notes"), ("Decisions", "decisions"), ("Actions, owners and due dates", "action_items"), ("Next meeting", "next_meeting_date"), ("Confidentiality", "confidentiality")]:
                    value = m.get(field, "")
                    if value:
                        st.markdown(f"**{label}**")
                        st.write(value)
                if st.button("Delete this meeting record", key=f"delete_minutes_{m.get('id')}"):
                    delete_record("meeting_minutes", m.get("id", ""))
                    log_audit("DELETE", "meeting_minutes", m.get("id", ""), f"Deleted minutes: {m.get('meeting_title', '')}")
                    st.session_state["meeting_minutes"] = load_records("meeting_minutes")
                    st.rerun()
    else:
        st.info("No meeting minutes match your search. Save the first meeting above.")

elif page == "Performance & Reviews":
    header("Performance & Reviews", "Plan employee check-ins, document job-related feedback and track agreed development goals.")
    st.info("Use consistent, job-related criteria. Keep sensitive case details out of performance notes and restrict access to authorised HR and managers.")
    with st.form("performance_review_form", clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); empno=c2.text_input("Employee number")
        dept=c1.text_input("Department"); reviewer=c2.text_input("Reviewer / line manager")
        period=c1.selectbox("Review period",["Probation review","Monthly check-in","Quarterly review","Mid-year review","Annual review","Return-to-work check-in","Development review"])
        review_date=c2.date_input("Review date",value=date.today())
        rating=st.selectbox("Overall assessment",["Not rated","Needs improvement","Partially meets expectations","Meets expectations","Exceeds expectations","Outstanding"])
        progress=st.text_area("Progress against objectives"); strengths=st.text_area("Strengths and contributions")
        needs=st.text_area("Development needs / support required"); goals=st.text_area("Agreed goals and actions")
        follow=c1.date_input("Follow-up date",value=date.today()); status=c2.selectbox("Review status",["Draft","Discussed","Action plan agreed","Follow-up due","Closed"])
        if st.form_submit_button("Save performance review"):
            if not employee.strip(): st.error("Employee name is required.")
            else:
                add_record("performance_reviews",{"employee_name":employee.strip(),"employee_number":empno.strip(),"department":dept.strip(),"review_period":period,"review_date":review_date.isoformat(),"reviewer":reviewer.strip(),"goal_progress":progress.strip(),"strengths":strengths.strip(),"development_needs":needs.strip(),"overall_rating":rating,"agreed_goals":goals.strip(),"follow_up_date":follow.isoformat(),"status":status,"created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Review saved to the HR review workflow."); st.rerun()
    rows=load_records("performance_reviews")
    if rows:
        st.dataframe(pd.DataFrame(rows).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True)
        export_csv(rows,"lynnewaters_performance_reviews.csv")
    else: st.info("No reviews yet. Start with a probation review or regular employee check-in.")

elif page == "Employee Relations":
    header("Employee Relations", "Track workplace cases, ownership, review dates and outcomes without turning the console into an unrestricted case-notes repository.")
    st.warning("Limit access to authorised HR staff. Record only necessary, factual information; do not store medical details or allegations beyond the approved case-management process.")
    with st.form("employee_relations_form",clear_on_submit=True):
        c1,c2=st.columns(2)
        ref=c1.text_input("Case reference *",placeholder="ER-2026-001"); opened=c2.date_input("Date opened",value=date.today())
        case_type=c1.selectbox("Case type",["Grievance","Disciplinary process","Workplace conflict","Wellbeing referral","Accommodation request","Harassment / misconduct","Other"])
        employee=c2.text_input("Employee / parties reference"); dept=c1.text_input("Department"); owner=c2.text_input("HR case owner")
        priority=c1.selectbox("Priority",["Routine","Medium","High","Urgent"]); status=c2.selectbox("Case status",["New","Under review","Meeting scheduled","Awaiting information","Action required","Resolved","Closed"])
        review=c1.date_input("Next review date",value=date.today()); confidentiality=c2.selectbox("Access classification",["Confidential HR","Highly restricted"])
        summary=st.text_area("Brief factual summary",help="Keep this concise and reference approved case files rather than copying sensitive evidence here.")
        resolution=st.text_area("Outcome / next step")
        if st.form_submit_button("Create case tracker"):
            if not ref.strip(): st.error("Case reference is required.")
            elif any(x.get("case_reference"," ").lower()==ref.strip().lower() for x in load_records("employee_relations")): st.error("Case reference already exists.")
            else:
                add_record("employee_relations",{"case_reference":ref.strip(),"opened_date":opened.isoformat(),"case_type":case_type,"employee_name":employee.strip(),"department":dept.strip(),"case_owner":owner.strip(),"priority":priority,"status":status,"next_review_date":review.isoformat(),"summary":summary.strip(),"resolution":resolution.strip(),"confidentiality":confidentiality,"created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Case tracker created and audit event recorded."); st.rerun()
    rows=load_records("employee_relations")
    if rows:
        status_filter=st.selectbox("Case status filter",["All"]+sorted({r.get("status","") for r in rows}))
        shown=rows if status_filter=="All" else [r for r in rows if r.get("status")==status_filter]
        st.dataframe(pd.DataFrame([{k:r.get(k,"") for k in ["case_reference","opened_date","case_type","employee_name","department","case_owner","priority","status","next_review_date","confidentiality"]} for r in shown]),use_container_width=True,hide_index=True)
        export_csv(shown,"lynnewaters_employee_relations_register.csv")
    else: st.info("No case trackers have been created.")

elif page == "Attendance Register":
    header("Attendance Register", "Maintain a simple operational attendance log and review absence patterns. This is not a biometric clocking or payroll system.")
    with st.form("attendance_form",clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); empno=c2.text_input("Employee number")
        dept=c1.text_input("Department"); workdate=c2.date_input("Work date",value=date.today())
        status=c1.selectbox("Attendance status",["Present","Absent - authorised","Absent - unauthorised","Late arrival","Early departure","Remote work","On approved leave","Public holiday","Rest day"])
        hours=c2.number_input("Hours worked (if applicable)",min_value=0.0,max_value=24.0,value=0.0,step=0.5); manager=c1.text_input("Manager")
        notes=st.text_area("Administrative note",help="Do not record medical details or unnecessary personal information.")
        if st.form_submit_button("Log attendance"):
            if not employee.strip(): st.error("Employee name is required.")
            else:
                add_record("attendance",{"employee_name":employee.strip(),"employee_number":empno.strip(),"department":dept.strip(),"work_date":workdate.isoformat(),"attendance_status":status,"hours":hours,"manager":manager.strip(),"notes":notes.strip(),"created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Attendance entry saved."); st.rerun()
    rows=load_records("attendance")
    if rows:
        c1,c2=st.columns(2); start=c1.date_input("From date",value=date.today().replace(day=1),key="att_from"); end=c2.date_input("To date",value=date.today(),key="att_to")
        shown=[r for r in rows if start.isoformat()<=r.get("work_date","")<=end.isoformat()]
        st.metric("Entries in selected period",len(shown))
        st.dataframe(pd.DataFrame(shown).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(shown,"lynnewaters_attendance.csv")
    else: st.info("No attendance entries yet.")

elif page == "Offboarding":
    header("Offboarding", "Coordinate employee exits with a checklist for handover, equipment, system access and final documentation.")
    with st.form("offboarding_form",clear_on_submit=True):
        c1,c2=st.columns(2)
        employee=c1.text_input("Employee name *"); empno=c2.text_input("Employee number")
        dept=c1.text_input("Department"); job=c2.text_input("Job title")
        lastday=c1.date_input("Last working day",value=date.today()); reason=c2.selectbox("Exit category",["Resignation","End of fixed term","Retirement","Dismissal","Redundancy / restructuring","Other"])
        manager=c1.text_input("Manager"); status=c2.selectbox("Workflow status",["Not started","In progress","Waiting for items","Ready for final review","Complete"])
        equipment=st.checkbox("Company equipment returned"); access=st.checkbox("System access removal confirmed"); exitint=st.checkbox("Exit interview offered / completed"); docs=st.checkbox("Final documents prepared")
        notes=st.text_area("Handover / admin notes")
        if st.form_submit_button("Create offboarding checklist"):
            if not employee.strip(): st.error("Employee name is required.")
            else:
                add_record("offboarding",{"employee_name":employee.strip(),"employee_number":empno.strip(),"department":dept.strip(),"job_title":job.strip(),"last_working_day":lastday.isoformat(),"reason_category":reason,"manager":manager.strip(),"equipment_return":"Complete" if equipment else "Outstanding","system_access_removed":"Confirmed" if access else "Outstanding","exit_interview":"Offered / complete" if exitint else "Outstanding","final_documents":"Prepared" if docs else "Outstanding","status":status,"notes":notes.strip(),"created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Offboarding checklist created."); st.rerun()
    rows=load_records("offboarding")
    if rows:
        st.dataframe(pd.DataFrame(rows).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(rows,"lynnewaters_offboarding.csv")
    else: st.info("No offboarding workflows yet.")

elif page == "HR Policies":
    header("HR Policies", "Maintain a policy register with ownership, version, effective date and scheduled review.")
    with st.form("hr_policy_form",clear_on_submit=True):
        c1,c2=st.columns(2)
        title=c1.text_input("Policy title *"); category=c2.selectbox("Category",["Recruitment","Code of conduct","Leave and attendance","Performance management","Disciplinary and grievance","Health and safety","Information security","Privacy and records","Training and development","Other"])
        version=c1.text_input("Version",value="1.0"); owner=c2.text_input("Policy owner")
        effective=c1.date_input("Effective date",value=date.today()); review=c2.date_input("Review date",value=date.today())
        status=c1.selectbox("Policy status",["Draft","Under review","Approved","Superseded","Archived"]); ack=c2.checkbox("Employee acknowledgement required")
        summary=st.text_area("Purpose / summary")
        if st.form_submit_button("Add policy to register"):
            if not title.strip(): st.error("Policy title is required.")
            else:
                add_record("hr_policies",{"policy_title":title.strip(),"policy_category":category,"version":version.strip(),"owner":owner.strip(),"effective_date":effective.isoformat(),"review_date":review.isoformat(),"status":status,"summary":summary.strip(),"acknowledgement_required":"Yes" if ack else "No","created_at":datetime.now().isoformat(timespec="minutes")})
                st.success("Policy register updated."); st.rerun()
    rows=load_records("hr_policies")
    if rows:
        st.dataframe(pd.DataFrame(rows).drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True); export_csv(rows,"lynnewaters_hr_policy_register.csv")
    else: st.info("No policies registered yet. Store approved policy files in HR Documents and track them here.")

elif page == "HR Findings":
    header("HR Findings", "Record process issues, employee feedback themes and evidence-based observations.")
    with st.form("finding_form", clear_on_submit=True):
        name = st.text_input("Finding")
        detail = st.text_area("Description / evidence")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        source = st.text_input("Source interview / document")
        if st.form_submit_button("Add Finding"):
            if name.strip():
                add_record("findings", {"finding": name.strip(), "description": detail, "priority": priority, "source": source, "date": date.today().isoformat()})
                st.success("Finding added.")
                st.rerun()
            else:
                st.error("Enter a finding name.")
    if st.session_state.findings:
        st.dataframe(st.session_state.findings, use_container_width=True, hide_index=True)
        export_csv(st.session_state.findings, "lynnewaters_findings.csv")
    else: st.info("No findings recorded yet.")

elif page == "HR Requirements":
    header("HR Requirements", "Record HR policy, process, compliance and reporting requirements.")
    with st.form("requirement_form", clear_on_submit=True):
        name = st.text_input("Requirement")
        category = st.selectbox("Category", ["Business", "Functional", "Technical", "Reporting", "Security", "Other"])
        detail = st.text_area("Description / acceptance criteria")
        priority = st.selectbox("Priority", ["Must have", "Should have", "Could have"])
        if st.form_submit_button("Add Requirement"):
            if name.strip():
                add_record("requirements", {"requirement": name.strip(), "category": category, "description": detail, "priority": priority, "date": date.today().isoformat()})
                st.success("Requirement added.")
                st.rerun()
            else: st.error("Enter a requirement.")
    if st.session_state.requirements:
        st.dataframe(st.session_state.requirements, use_container_width=True, hide_index=True)
        export_csv(st.session_state.requirements, "lynnewaters_requirements.csv")
    else: st.info("No requirements recorded yet.")

elif page == "HR Risks":
    header("HR Risk Register", "Track workforce, recruitment, policy and process risks with owners and mitigations.")
    with st.form("risk_form", clear_on_submit=True):
        risk = st.text_input("Risk")
        severity = st.selectbox("Severity", ["High", "Medium", "Low"])
        mitigation = st.text_area("Mitigation / response")
        owner = st.text_input("Owner")
        if st.form_submit_button("Add Risk"):
            if risk.strip():
                add_record("risks", {"risk": risk.strip(), "severity": severity, "mitigation": mitigation, "owner": owner, "status": "Open"})
                st.success("Risk added.")
                st.rerun()
            else: st.error("Enter a risk.")
    if st.session_state.risks:
        st.dataframe(st.session_state.risks, use_container_width=True, hide_index=True)
        export_csv(st.session_state.risks, "lynnewaters_risks.csv")
    else: st.info("No risks recorded yet.")

elif page == "Improvement Opportunities":
    header("HR Improvement Opportunities", "Identify improvements to recruitment, retention, employee experience and HR operations.")
    with st.form("opportunity_form", clear_on_submit=True):
        name = st.text_input("Opportunity")
        impact = st.selectbox("Expected impact", ["High", "Medium", "Low"])
        effort = st.selectbox("Estimated effort", ["Small", "Medium", "Large"])
        value = st.text_input("Estimated value (optional)", placeholder="e.g. R50,000")
        detail = st.text_area("Description")
        if st.form_submit_button("Add Opportunity"):
            if name.strip():
                add_record("opportunities", {"opportunity": name.strip(), "impact": impact, "effort": effort, "estimated_value": value, "description": detail, "status": "Under review"})
                st.success("Opportunity added.")
                st.rerun()
            else: st.error("Enter an opportunity.")
    if st.session_state.opportunities:
        st.dataframe(st.session_state.opportunities, use_container_width=True, hide_index=True)
        export_csv(st.session_state.opportunities, "lynnewaters_opportunities.csv")
    else: st.info("No opportunities recorded yet.")

elif page in ["HR Actions", "HR Action Tracker"]:
    header("HR Action Tracker", "Assign HR follow-ups, owners, due dates and completion status.")
    with st.form("action_form", clear_on_submit=True):
        task = st.text_input("Action / task")
        owner = st.text_input("Owner")
        due = st.date_input("Due date", value=date.today())
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        if st.form_submit_button("Add Action"):
            if task.strip():
                add_record("actions", {"action": task.strip(), "owner": owner, "due_date": due.isoformat(), "priority": priority, "status": "Open"})
                st.success("Action added.")
                st.rerun()
            else: st.error("Enter an action.")
    if st.session_state.actions:
        for idx, action in enumerate(st.session_state.actions):
            with st.expander(f"{action['action']} · {action['status']}"):
                st.write(f"Owner: {action.get('owner') or 'Not assigned'}")
                st.write(f"Due: {action.get('due_date')} · Priority: {action.get('priority')}")
                new_status = st.selectbox("Status", ["Open", "In progress", "Complete"], index=["Open", "In progress", "Complete"].index(action["status"]), key=f"action_status_{idx}")
                if new_status != action["status"]:
                    update_record("actions", action["id"], "status", new_status)
                    log_audit("UPDATE", "actions", action["id"], "Action status changed to " + new_status)
                    st.session_state.actions = load_records("actions")
                    st.rerun()
        export_csv(st.session_state.actions, "lynnewaters_actions.csv")
    else: st.info("No actions recorded yet.")

elif page == "HR Reports":
    header("HR Reports", "Export HR operations summaries and registers from the records currently available.")
    st.warning("This report uses records saved in this running app. It is not an AI-generated analysis.")
    report = {
        "generated_at": datetime.now().isoformat(timespec="minutes"),
        "employees": st.session_state.employees,
        "candidates": st.session_state.candidates,
        "vacancies": st.session_state.vacancies,
        "onboarding": st.session_state.onboarding,
        "training": st.session_state.training,
        "leave_requests": st.session_state.leave_requests,
        "interviews": st.session_state.interviews,
        "findings": st.session_state.findings,
        "requirements": st.session_state.requirements,
        "risks": st.session_state.risks,
        "opportunities": st.session_state.opportunities,
        "actions": st.session_state.actions,
        "uploaded_documents": [{k: d.get(k, "") for k in ["filename", "document_type", "related_person", "document_date", "expiry_date", "confidentiality", "uploaded_at"]} for d in load_records("document_register")],
    }
    st.subheader("Report Preview")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Candidates", len(report["candidates"]))
    with c2: st.metric("Open vacancies", sum(v.get("status") == "Open" for v in report["vacancies"]))
    with c3: st.metric("Onboarding records", len(report["onboarding"]))
    with c4: st.metric("Pending leave", sum(l.get("status") == "Pending" for l in report["leave_requests"]))
    st.json({k: v for k, v in report.items() if k != "generated_at"})
    json_name = f"lynnewaters_hr_report_{date.today().isoformat()}.json"
    if st.download_button(
        "Download HR Report (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
        file_name=json_name,
        mime="application/json",
    ):
        log_audit("EXPORT", "report", json_name, "Exported HR workspace report as JSON")

    # Build a printable PDF summary using ReportLab.
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, pagesize=A4,
            rightMargin=16*mm, leftMargin=16*mm,
            topMargin=16*mm, bottomMargin=16*mm
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ConsoleTitle", parent=styles["Title"],
            textColor=colors.HexColor("#073763"), fontSize=19, leading=23, spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name="ConsoleSection", parent=styles["Heading2"],
            textColor=colors.HexColor("#087eaa"), fontSize=12, leading=15, spaceBefore=10, spaceAfter=5
        ))
        story = [
            Paragraph("Lynnewaters HR Management Console", styles["ConsoleTitle"]),
            Paragraph(f"Workspace report · Generated {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]),
            Spacer(1, 8*mm),
            Paragraph("Executive Summary", styles["ConsoleSection"]),
        ]
        summary_rows = [
            ["Record type", "Count"],
            ["Employees", len(report["employees"])],
            ["Candidates", len(report["candidates"])],
            ["Vacancies", len(report["vacancies"])],
            ["Onboarding", len(report["onboarding"])],
            ["Training", len(report["training"])],
            ["Leave requests", len(report["leave_requests"])],
            ["Interviews", len(report["interviews"])],
            ["Documents", len(report["uploaded_documents"])],
            ["Findings", len(report["findings"])],
            ["Requirements", len(report["requirements"])],
            ["Risks", len(report["risks"])],
            ["Opportunities", len(report["opportunities"])],
            ["Actions", len(report["actions"])],
        ]
        summary_table = Table(summary_rows, colWidths=[105*mm, 45*mm], repeatRows=1)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#073763")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#b7d7e8")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#eef7fb")]),
            ("PADDING", (0,0), (-1,-1), 7),
        ]))
        story.append(summary_table)

        section_configs = [
            ("Employees", "employees", ["employee_number", "full_name", "department", "job_title", "employment_type", "start_date", "employment_status"]),
            ("Candidates", "candidates", ["full_name", "position", "stage", "interview_date", "score"]),
            ("Vacancies", "vacancies", ["job_title", "department", "hiring_manager", "status"]),
            ("Onboarding", "onboarding", ["employee_name", "job_title", "start_date", "status"]),
            ("Training", "training", ["employee_name", "course", "due_date", "status"]),
            ("Leave Requests", "leave_requests", ["employee_name", "leave_type", "start_date", "end_date", "days", "status"]),
            ("Interviews", "interviews", ["title", "person", "org", "date", "status"]),
            ("Findings", "findings", ["finding", "priority", "source"]),
            ("Requirements", "requirements", ["requirement", "category", "priority"]),
            ("Risks", "risks", ["risk", "severity", "owner", "status"]),
            ("Opportunities", "opportunities", ["opportunity", "impact", "effort", "status"]),
            ("Actions", "actions", ["action", "owner", "due_date", "priority", "status"]),
        ]
        for section_title, key, fields in section_configs:
            story.append(Paragraph(section_title, styles["ConsoleSection"]))
            rows = [[field.replace("_", " ").title() for field in fields]]
            for item in report[key]:
                rows.append([str(item.get(field, "") or "—")[:110] for field in fields])
            if len(rows) == 1:
                rows.append(["No records"] + ["—"] * (len(fields)-1))
            available_width = 178*mm
            col_width = available_width / len(fields)
            tbl = Table(rows, colWidths=[col_width] * len(fields), repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0a6588")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#b7d7e8")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f8fb")]),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("FONTSIZE", (0,0), (-1,-1), 7.5),
                ("PADDING", (0,0), (-1,-1), 5),
            ]))
            story.append(tbl)
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("Uploaded Documents", styles["ConsoleSection"]))
        story.append(Paragraph(", ".join(report["uploaded_documents"]) if report["uploaded_documents"] else "No documents uploaded.", styles["Normal"]))
        doc.build(story)
        pdf_name = f"lynnewaters_hr_report_{date.today().isoformat()}.pdf"
        if st.download_button(
            "Download Professional HR PDF Report",
            data=pdf_buffer.getvalue(),
            file_name=pdf_name,
            mime="application/pdf",
        ):
            log_audit("EXPORT", "report", pdf_name, "Exported HR workspace report as PDF")
    except ImportError:
        st.warning("PDF export requires ReportLab. Install dependencies from requirements.txt and restart the app.")

    st.markdown("**CSV exports**")
    for key, filename in [
        ("employees", "hr_employee_register.csv"), ("candidates", "hr_candidates.csv"), ("vacancies", "hr_vacancies.csv"),
        ("onboarding", "hr_onboarding.csv"), ("training", "hr_training.csv"),
        ("leave_requests", "hr_leave_requests.csv"),
        ("interviews", "interviews.csv"), ("findings", "findings.csv"),
        ("requirements", "requirements.csv"), ("risks", "risks.csv"),
        ("opportunities", "opportunities.csv"), ("actions", "actions.csv")
    ]:
        if report[key]:
            export_csv(report[key], f"lynnewaters_{filename}")

elif page == "Audit Log":
    header("Audit Log", "Review a timestamped history of key workspace activity.")
    audit_rows = load_records("audit_log")
    c1, c2 = st.columns([1, 2])
    with c1:
        event_filter = st.selectbox("Event type", ["All", "CREATE", "DELETE", "UPDATE", "UPLOAD", "DOWNLOAD", "EXPORT"])
    with c2:
        search_text = st.text_input("Search audit entries", placeholder="Search details, record type or ID")
    filtered = audit_rows
    if event_filter != "All":
        filtered = [r for r in filtered if r.get("event") == event_filter]
    if search_text.strip():
        term = search_text.strip().lower()
        filtered = [r for r in filtered if term in " ".join(str(r.get(k, "")) for k in ["timestamp", "event", "record_type", "record_id", "details", "actor"]).lower()]
    m1, m2, m3 = st.columns(3)
    m1.metric("Total events", len(audit_rows))
    m2.metric("Shown", len(filtered))
    m3.metric("Event types", len(set(r.get("event", "") for r in audit_rows)))
    if filtered:
        st.dataframe(pd.DataFrame(filtered).drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)
        export_csv(filtered, "lynnewaters_audit_log.csv")
    else:
        st.info("No audit events match these filters.")
    st.caption("Audit entries record tracked application actions, including employee creation, status changes, deletions and CSV exports. This is an operational history, not a tamper-proof security log; restrict database access and back it up for production use.")

elif page == "Settings":
    header("HR Console Settings", "Workspace details and production-readiness guidance.")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Workspace Profile")
    st.write("**Workspace:** Lynnewaters HR Management Console")
    st.write("**Application version:** V11 · Neon Glass HR Operations Console")
    st.write("**Data mode:** SQLite database plus local uploads")
    st.write("**Workspace directory:** `data/` and `uploads/` beside `app.py`")
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("For production use, configure named user accounts, role-based permissions, secure shared database hosting, backups, retention rules and a POPIA privacy review. Do not use this prototype as a payroll engine or legal case-management system.")

st.markdown("---")
st.caption("Lynnewaters HR Management Console V11 · Streamlit prototype · Verify records before relying on reports.")
