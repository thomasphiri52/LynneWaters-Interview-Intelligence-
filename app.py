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

init_db()

st.set_page_config(
    page_title="Lynnewaters Interview Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp {
  background:
    radial-gradient(circle at 78% 3%, rgba(0,170,255,.13), transparent 28%),
    radial-gradient(circle at 15% 75%, rgba(0,80,255,.10), transparent 28%),
    #030b18;
  color: #edf7ff;
}
[data-testid="stSidebar"] {
  background: rgba(4,15,31,.96);
  border-right: 1px solid rgba(70,190,255,.18);
}
h1, h2, h3 { color: #edf7ff !important; }
.eyebrow {
  color: #48cfff; font-size: .72rem; letter-spacing: .18em;
  font-weight: 700; text-transform: uppercase;
}
.hero-title { font-size: 2rem; font-weight: 750; margin: .15rem 0 1.2rem; }
.metric-card {
  background: linear-gradient(145deg, rgba(12,37,63,.82), rgba(4,20,38,.72));
  border: 1px solid rgba(61,195,255,.20);
  border-radius: 15px; padding: 18px 20px; min-height: 112px;
}
.metric-label { color: #8bb0c7; font-size: .72rem; letter-spacing: .08em; }
.metric-value { color: #edfaff; font-size: 1.8rem; font-weight: 750; margin-top: 7px; }
.panel {
  background: linear-gradient(145deg, rgba(12,37,63,.68), rgba(4,20,38,.55));
  border: 1px solid rgba(61,195,255,.18); border-radius: 16px;
  padding: 18px 20px; margin-bottom: 14px;
}
div.stButton > button, div.stDownloadButton > button {
  border-radius: 10px; border: 1px solid rgba(57,208,255,.4);
  background: linear-gradient(135deg,#007bd8,#00a9d8); color: white;
  font-weight: 650; min-height: 2.5rem;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
  border-color: #4bdcff; color: white; filter: brightness(1.08);
}
div[data-testid="stForm"] {
  background: rgba(5,22,39,.58); padding: 18px;
  border: 1px solid rgba(61,195,255,.18); border-radius: 15px;
}
[data-testid="stMetric"] {
  background: rgba(12,37,63,.72); padding: 15px;
  border: 1px solid rgba(61,195,255,.18); border-radius: 14px;
}
small, .stCaption { color: #8aa9bd !important; }
</style>
""", unsafe_allow_html=True)

for collection in TABLES:
    if collection not in st.session_state:
        st.session_state[collection] = load_records(collection)

def header(section, subtitle=None):
    st.markdown('<div class="eyebrow">LYNNEWATERS · INTERVIEW INTELLIGENCE CONSOLE</div>', unsafe_allow_html=True)
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
    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=f"download_{filename}",
    )

def add_record(collection_key, record):
    if not record.get("id"):
        record["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    save_record(collection_key, record)
    st.session_state[collection_key] = load_records(collection_key)

with st.sidebar:
    st.markdown("## ◈ LYNNEWATERS")
    st.caption("INTERVIEW INTELLIGENCE")
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard", "Interviews", "Documents", "Findings",
            "Requirements", "Risks", "Opportunities", "Actions",
            "Reports", "Settings"
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Workspace status")
    st.success("Console ready")
    st.caption("Local prototype · Data is stored with this app")

if page == "Dashboard":
    header("Executive Intelligence", "A central workspace for interviews, evidence, requirements, risks and business opportunities.")
    interviews = st.session_state.interviews
    findings = st.session_state.findings
    requirements = st.session_state.requirements
    risks = st.session_state.risks
    opportunities = st.session_state.opportunities
    actions = st.session_state.actions
    cols = st.columns(5)
    with cols[0]: metric_card("INTERVIEWS", len(interviews))
    with cols[1]: metric_card("DOCUMENTS", len(list(UPLOAD_DIR.iterdir())))
    with cols[2]: metric_card("FINDINGS", len(findings))
    with cols[3]: metric_card("REQUIREMENTS", len(requirements))
    with cols[4]: metric_card("OPEN ACTIONS", sum(a.get("status") != "Complete" for a in actions))
    st.write("")
    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Recent Interviews")
        if interviews:
            df = pd.DataFrame(interviews)
            show_cols = [c for c in ["title", "person", "org", "date", "status"] if c in df.columns]
            st.dataframe(df[show_cols].tail(6).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No interviews recorded yet. Open Interviews to create your first session.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Workspace Snapshot")
        st.write(f"**Documents uploaded:** {len(list(UPLOAD_DIR.iterdir()))}")
        st.write(f"**Findings captured:** {len(findings)}")
        st.write(f"**Risks logged:** {len(risks)}")
        st.write(f"**Opportunities recorded:** {len(opportunities)}")
        st.write(f"**Actions tracked:** {len(actions)}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Quick Start")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.write("**1 · Capture**")
        st.caption("Create an interview session and record the purpose.")
    with q2:
        st.write("**2 · Analyse**")
        st.caption("Log findings, requirements, risks and opportunities.")
    with q3:
        st.write("**3 · Report**")
        st.caption("Export the current interview register and workspace records.")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Interviews":
    header("Interview Management", "Create and maintain structured business discovery interview sessions.")
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
            delete_record("interviews", selected_id)
            st.session_state.interviews = load_records("interviews")
            st.success("Interview deleted.")
            st.rerun()
    else:
        st.info("Your interview register is empty.")

elif page == "Documents":
    header("Document Management", "Upload supporting files and maintain an evidence register.")
    uploads = st.file_uploader(
        "Upload interview documents",
        type=["pdf", "doc", "docx", "txt", "csv", "xlsx", "xls", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if uploads:
        for file in uploads:
            safe_name = Path(file.name).name
            target = UPLOAD_DIR / safe_name
            if not target.exists():
                target.write_bytes(file.getvalue())
                st.success(f"Saved {safe_name}")
    files = sorted([p for p in UPLOAD_DIR.iterdir() if p.is_file()])
    st.subheader("Uploaded Documents")
    if files:
        st.dataframe(
            [{"File": p.name, "Size (KB)": round(p.stat().st_size / 1024, 1)} for p in files],
            use_container_width=True, hide_index=True
        )
        for p in files:
            st.download_button(f"Download {p.name}", p.read_bytes(), file_name=p.name, key=f"doc_{p.name}")
    else:
        st.info("No documents uploaded yet.")

elif page == "Findings":
    header("Findings", "Capture and prioritise observations from interviews and supporting evidence.")
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

elif page == "Requirements":
    header("Requirements", "Translate validated findings into actionable business or technical requirements.")
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

elif page == "Risks":
    header("Risk Register", "Record potential issues and planned mitigations.")
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

elif page == "Opportunities":
    header("Opportunities", "Identify improvements and prioritise potential business value.")
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

elif page == "Actions":
    header("Action Tracker", "Assign follow-up actions and track completion.")
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
                    st.session_state.actions = load_records("actions")
                    st.rerun()
        export_csv(st.session_state.actions, "lynnewaters_actions.csv")
    else: st.info("No actions recorded yet.")

elif page == "Reports":
    header("Report Builder", "Export a simple workspace report from the records currently available.")
    st.warning("This report uses records saved in this running app. It is not an AI-generated analysis.")
    report = {
        "generated_at": datetime.now().isoformat(timespec="minutes"),
        "interviews": st.session_state.interviews,
        "findings": st.session_state.findings,
        "requirements": st.session_state.requirements,
        "risks": st.session_state.risks,
        "opportunities": st.session_state.opportunities,
        "actions": st.session_state.actions,
        "uploaded_documents": [p.name for p in UPLOAD_DIR.iterdir() if p.is_file()],
    }
    st.subheader("Report Preview")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Interviews", len(report["interviews"]))
    with c2: st.metric("Findings", len(report["findings"]))
    with c3: st.metric("Open actions", sum(a.get("status") != "Complete" for a in report["actions"]))
    st.json({k: v for k, v in report.items() if k != "generated_at"})
    st.download_button(
        "Download Workspace Report (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
        file_name=f"lynnewaters_workspace_report_{date.today().isoformat()}.json",
        mime="application/json",
    )

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
            Paragraph("Lynnewaters Interview Intelligence Console", styles["ConsoleTitle"]),
            Paragraph(f"Workspace report · Generated {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]),
            Spacer(1, 8*mm),
            Paragraph("Executive Summary", styles["ConsoleSection"]),
        ]
        summary_rows = [
            ["Record type", "Count"],
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
        st.download_button(
            "Download Professional PDF Report",
            data=pdf_buffer.getvalue(),
            file_name=f"lynnewaters_workspace_report_{date.today().isoformat()}.pdf",
            mime="application/pdf",
        )
    except ImportError:
        st.warning("PDF export requires ReportLab. Install dependencies from requirements.txt and restart the app.")

    st.markdown("**CSV exports**")
    for key, filename in [
        ("interviews", "interviews.csv"), ("findings", "findings.csv"),
        ("requirements", "requirements.csv"), ("risks", "risks.csv"),
        ("opportunities", "opportunities.csv"), ("actions", "actions.csv")
    ]:
        if report[key]:
            export_csv(report[key], f"lynnewaters_{filename}")

elif page == "Settings":
    header("Settings", "Basic workspace details and prototype configuration.")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Workspace Profile")
    st.write("**Workspace:** Lynnewaters Interview Intelligence Console")
    st.write("**Application version:** V3 · Streamlit edition")
    st.write("**Data mode:** Local JSON register plus local uploads")
    st.write("**Workspace directory:** `data/` and `uploads/` beside `app.py`")
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("For multi-user production use, add authentication, access controls, database storage, backup procedures and a privacy review before storing confidential interview material.")

st.markdown("---")
st.caption("Lynnewaters Interview Intelligence Console · Streamlit prototype · Verify records before relying on reports.")
