# Lynnewaters HR Management Console — V11 Neon Glass

A Streamlit HR operations console designed around everyday HR workflows rather than interview-intelligence research. V11 upgrades the interface to a consistent deep navy, neon cyan/electric blue and glass-panel design with hover feedback for interactive controls. This is a visual and usability upgrade; it does not add authentication or change the underlying HR business rules. The dashboard provides an HR command centre, operational indicators, action shortcuts and a priority work queue.

## Console modules
- **HR Command Centre** — live counts, recruitment snapshot, operational indicators and a priority queue for pending leave, onboarding, training, employee-relations and performance follow-ups.
- **Employee Directory** — employee register, status changes and basic employment details.
- **Recruitment Pipeline & Vacancy Planning** — applicant stages, interviews, approved roles and hiring progress.
- **Interview Scorecards** — structured, job-related interview records and consistent assessment prompts.
- **Onboarding Checklist** — coordinate pre-start and new-starter tasks.
- **Leave & Absence** — log requests and track pending/approved/declined decisions.
- **Attendance Register** — basic operational attendance log and date-range review; not a biometric timeclock or payroll calculator.
- **Performance & Reviews** — probation check-ins, quarterly/annual reviews, objective progress, development needs and follow-up dates.
- **Training & Development** — training plans, due dates and completion tracking.
- **Employee Relations** — restricted case tracker with ownership, status, priority and next review date. It is not a substitute for a secure legal case-management system.
- **Offboarding** — exit workflow checklist for equipment return, access removal, exit interview and final documents.
- **HR Policies** — policy register with version, owner, effective date and review date.
- **HR Documents** — document register, upload/download tracking and review/expiry information.
- **Meeting Minutes** — HR meeting agenda, decisions, actions, attendees and confidentiality classification.
- **HR Action Tracker** — owners, due dates, priority and completion status.
- **HR Reports & Audit Log** — operational exports and a history of tracked application activity.

## Run locally
1. Install Python 3.10 or newer.
2. In this folder, run `pip install -r requirements.txt`.
3. Start the app with `streamlit run app.py`.

## Data storage and migration
- SQLite database: `data/lynnewaters.db`
- Uploaded files: `uploads/`
- V11 retains the V10 workflow tables automatically while retaining existing tables from earlier versions. Back up the project and existing `data/` and `uploads/` folders before upgrading.

## Important production requirements
This is a working prototype, not a complete HRIS, payroll engine, statutory leave calculator, applicant tracking system with email integration, or legal case-management system. The current app does not provide user login or role-based permissions. Do not store highly sensitive employee-relations records or identity, banking, medical or other unnecessary personal information until access controls and secure storage are implemented.

Before production use, implement authenticated named accounts, role-based access (HR administrator, HR officer, line manager, read-only), secure shared database and file storage, encryption, backups, retention/deletion rules, audit-log protection, privacy notices and a POPIA review. Streamlit Community Cloud local files may not persist reliably; do not commit the live database or confidential HR data to GitHub.

## Deploy
Push the application files to a private or appropriately controlled GitHub repository, then configure Streamlit Community Cloud to use `app.py` as the main file. Confirm that persistent storage and access controls are suitable before using real employee data.
