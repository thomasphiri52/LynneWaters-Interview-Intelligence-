# Lynnewaters Interview Intelligence Console — V4

A navy-blue interview intelligence console with persistent SQLite storage, document uploads, register exports and a printable PDF workspace report.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

## Modules

- Executive dashboard with record counts
- Interview register: create, list, delete and CSV export
- Document uploads and downloads
- Findings register
- Requirements register
- Risk register
- Opportunities register
- Action tracker with persistent status changes
- Workspace report: JSON, CSV and PDF exports
- Basic settings page

## Persistence

- SQLite database is stored at `data/lynnewaters.db`.
- Uploaded documents are stored in `uploads/`.
- Interview, finding, requirement, risk, opportunity and action records are saved to SQLite.
- For Streamlit Community Cloud, the local filesystem may not be durable across app rebuilds/restarts. For production, use a managed external database and external file storage, with backups.

## Deployment

Push `app.py`, `requirements.txt`, and the project files to GitHub. In Streamlit Community Cloud, select the repository and set the main file path to `app.py`.

## Production readiness notes

This remains a prototype. Before storing sensitive interview information or using it with multiple users, add authentication, authorisation, secure secrets handling, a managed database, backups, audit logs, and a privacy/security review. AI transcription, OCR, integrations, and automatic email reminders are not connected.
