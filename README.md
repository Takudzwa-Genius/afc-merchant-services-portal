# AFC Merchant Services Portal (Prototype)

A local prototype for logging POS complaints, allocating tickets to analysts by merchant branch, tracking status and priority, and viewing a management dashboard.

## Features
- Log a merchant/POS complaint
- Sample branch-to-analyst allocation
- Track status, priority, target resolution date, and notes
- Dashboard for open, resolved, critical, and overdue complaints
- Filters by branch, status, and analyst
- CSV export for demo records

## Run locally
1. Install Python 3.10 or later.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

5. Open the local address shown in the terminal.

## Configure branch allocation
Edit `BRANCH_ANALYSTS` in `app.py` and replace sample branches and analyst labels with approved test assignments. Do not commit real merchant data or confidential bank information.

## Important security notice
This is a proof-of-concept, not a production-ready banking application. The current prototype has no authentication or role-based access control and stores data in a local SQLite database. Before any real use, obtain AFC ICT, Information Security, Risk, Compliance, and Data Protection approval. Implement approved SSO/MFA, role-based access, audit logs, secure hosting, encryption, backups, retention rules, monitoring, incident response, and security testing. Do not use real customer, merchant, transaction, terminal, or credential data in this demo.
