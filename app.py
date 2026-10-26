import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "merchant_queries.db"

st.set_page_config(page_title="AFC Merchant Services Portal", page_icon="🏦", layout="wide")

# DEMO ONLY: This prototype is not approved for production banking data.
# Before deployment, add AFC-approved authentication/SSO, role-based access,
# audit logging, encryption, retention controls, backups, and security review.

STATUSES = ["New", "Assigned", "In Progress", "Awaiting Merchant", "Awaiting ICT", "Resolved", "Closed"]
PRIORITIES = ["Low", "Normal", "High", "Critical"]
ISSUE_TYPES = [
    "POS not powering on", "POS network/connectivity", "POS transaction declined",
    "Settlement/query", "Terminal configuration", "Paper/receipt issue",
    "POS deployment", "POS replacement", "Merchant training", "Other"
]

# Replace these examples with approved branch and analyst assignments.
# Keep only fictional/test data in this prototype.
BRANCH_ANALYSTS = {
    "Harare": ["Analyst 1", "Analyst 2"],
    "Bulawayo": ["Analyst 3"],
    "Mutare": ["Analyst 4"],
    "Gweru": ["Analyst 5"],
    "Other": ["Unassigned"]
}

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            merchant_name TEXT NOT NULL,
            merchant_branch TEXT NOT NULL,
            contact_person TEXT,
            contact_phone TEXT,
            terminal_id TEXT,
            issue_type TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            assigned_analyst TEXT NOT NULL,
            status TEXT NOT NULL,
            target_resolution_date TEXT,
            last_updated TEXT NOT NULL,
            resolution_notes TEXT,
            resolved_at TEXT
        )
        """)
        conn.commit()

def fetch_df():
    with connect() as conn:
        return pd.read_sql_query("SELECT * FROM complaints ORDER BY created_at DESC", conn)

def assign_analyst(branch):
    names = BRANCH_ANALYSTS.get(branch, ["Unassigned"])
    return names[0] if names else "Unassigned"

def insert_complaint(data):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute("""
        INSERT INTO complaints (
            created_at, merchant_name, merchant_branch, contact_person, contact_phone,
            terminal_id, issue_type, description, priority, assigned_analyst, status,
            target_resolution_date, last_updated, resolution_notes, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now, data["merchant_name"], data["merchant_branch"], data["contact_person"],
            data["contact_phone"], data["terminal_id"], data["issue_type"], data["description"],
            data["priority"], data["assigned_analyst"], "New",
            data["target_resolution_date"], now, "", None
        ))
        conn.commit()

def update_complaint(ticket_id, status, analyst, priority, notes):
    now = datetime.now().isoformat(timespec="seconds")
    resolved_at = now if status in ("Resolved", "Closed") else None
    with connect() as conn:
        conn.execute("""
        UPDATE complaints
        SET status=?, assigned_analyst=?, priority=?, resolution_notes=?,
            last_updated=?, resolved_at=COALESCE(?, resolved_at)
        WHERE id=?
        """, (status, analyst, priority, notes, now, resolved_at, int(ticket_id)))
        conn.commit()

init_db()
st.title("🏦 AFC Bank | Merchant Services Portal")
st.caption("POS complaints • Merchant queries • Analyst allocation • Resolution dashboard")
st.warning(
    "Prototype only. Use fictional/test records. Do not enter real customer or merchant information "
    "until AFC ICT, Information Security, Risk and Compliance approve the design and hosting."
)

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Open", ["Dashboard", "Log a complaint", "Manage complaints", "Branch & analyst setup"])
    st.divider()
    st.caption("Demo prototype • Local SQLite database")

if page == "Dashboard":
    df = fetch_df()
    total = len(df)
    open_count = int((~df["status"].isin(["Resolved", "Closed"])).sum()) if total else 0
    resolved = int(df["status"].isin(["Resolved", "Closed"]).sum()) if total else 0
    critical = int((df["priority"] == "Critical").sum()) if total else 0
    overdue = 0
    if total:
        due = pd.to_datetime(df["target_resolution_date"], errors="coerce")
        overdue = int(((due.dt.date < date.today()) & (~df["status"].isin(["Resolved", "Closed"]))).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total complaints", total)
    c2.metric("Open complaints", open_count)
    c3.metric("Resolved / closed", resolved)
    c4.metric("Critical priority", critical)
    c5.metric("Past target date", overdue)

    st.subheader("Complaints by status")
    if total:
        status_counts = df["status"].value_counts().rename_axis("Status").reset_index(name="Count")
        st.bar_chart(status_counts.set_index("Status"))
        left, right = st.columns(2)
        with left:
            st.subheader("Complaints by branch")
            st.bar_chart(df.groupby("merchant_branch").size().sort_values(ascending=False))
        with right:
            st.subheader("Workload by analyst")
            st.bar_chart(df.groupby("assigned_analyst").size().sort_values(ascending=False))
        st.subheader("Latest complaints")
        cols = ["id", "created_at", "merchant_name", "merchant_branch", "terminal_id",
                "issue_type", "priority", "assigned_analyst", "status", "target_resolution_date"]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
        st.download_button("Export current complaints (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="demo_complaints_export.csv", mime="text/csv")
    else:
        st.info("No complaints logged yet. Add a fictional test complaint from 'Log a complaint' to see the dashboard.")

elif page == "Log a complaint":
    st.subheader("Log a new POS complaint / merchant query")
    with st.form("new_complaint", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            merchant = st.text_input("Merchant name *", placeholder="Demo Merchant A")
            branch = st.selectbox("Merchant branch *", list(BRANCH_ANALYSTS.keys()))
            contact = st.text_input("Contact person (optional)")
            phone = st.text_input("Contact phone (optional; test data only)")
            terminal = st.text_input("POS terminal ID (use fictional ID in demo)", placeholder="TEST-POS-001")
        with col2:
            issue = st.selectbox("Issue type *", ISSUE_TYPES)
            priority = st.selectbox("Priority *", PRIORITIES, index=1)
            target = st.date_input("Target resolution date", value=date.today())
            suggested_analyst = assign_analyst(branch)
            st.info(f"Default analyst for {branch}: **{suggested_analyst}**")
        description = st.text_area("Issue description *", placeholder="Describe the problem, when it started, and any troubleshooting already done.")
        submitted = st.form_submit_button("Submit complaint", type="primary")
        if submitted:
            if not merchant.strip() or not description.strip():
                st.error("Please complete Merchant name and Issue description.")
            else:
                insert_complaint({
                    "merchant_name": merchant.strip(),
                    "merchant_branch": branch,
                    "contact_person": contact.strip(),
                    "contact_phone": phone.strip(),
                    "terminal_id": terminal.strip(),
                    "issue_type": issue,
                    "description": description.strip(),
                    "priority": priority,
                    "assigned_analyst": suggested_analyst,
                    "target_resolution_date": target.isoformat()
                })
                st.success("Complaint logged and assigned using the sample branch-to-analyst mapping.")

elif page == "Manage complaints":
    st.subheader("Search, assign and update complaints")
    df = fetch_df()
    if df.empty:
        st.info("No complaints available.")
    else:
        filters = st.columns(3)
        with filters[0]:
            status_filter = st.multiselect("Filter by status", STATUSES, default=STATUSES)
        with filters[1]:
            branch_filter = st.multiselect("Filter by branch", sorted(df["merchant_branch"].dropna().unique()))
        with filters[2]:
            analyst_filter = st.multiselect("Filter by analyst", sorted(df["assigned_analyst"].dropna().unique()))
        view = df[df["status"].isin(status_filter)]
        if branch_filter:
            view = view[view["merchant_branch"].isin(branch_filter)]
        if analyst_filter:
            view = view[view["assigned_analyst"].isin(analyst_filter)]
        st.dataframe(view[["id", "created_at", "merchant_name", "merchant_branch", "terminal_id",
                           "issue_type", "priority", "assigned_analyst", "status", "target_resolution_date"]],
                     use_container_width=True, hide_index=True)
        ids = view["id"].tolist()
        if ids:
            chosen = st.selectbox("Select ticket ID to update", ids)
            row = df[df["id"] == chosen].iloc[0]
            with st.form("update_ticket"):
                st.write(f"**{row['merchant_name']}** — {row['issue_type']}")
                col1, col2 = st.columns(2)
                with col1:
                    new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(row["status"]))
                    analyst_options = sorted(set(sum(BRANCH_ANALYSTS.values(), [])) | {row["assigned_analyst"]})
                    new_analyst = st.selectbox("Assigned analyst", analyst_options,
                                               index=analyst_options.index(row["assigned_analyst"]))
                with col2:
                    new_priority = st.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(row["priority"]))
                    st.text_input("Branch", value=row["merchant_branch"], disabled=True)
                notes = st.text_area("Resolution / follow-up notes", value=row["resolution_notes"] or "")
                save = st.form_submit_button("Save update", type="primary")
                if save:
                    update_complaint(chosen, new_status, new_analyst, new_priority, notes)
                    st.success(f"Ticket #{chosen} updated. Refresh the page to view the latest values.")

else:
    st.subheader("Branch and analyst assignment")
    st.write("The mapping below is sample configuration. Replace it with the approved AFC branch portfolio and analyst allocations.")
    rows = [{"Branch": branch, "Default analyst": ", ".join(analysts)} for branch, analysts in BRANCH_ANALYSTS.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.info(
        "To change assignments in this prototype, edit BRANCH_ANALYSTS near the top of app.py. "
        "For production, use an administrator-controlled configuration table and role-based permissions."
    )

st.divider()
st.caption("Internal concept prototype only. Production deployment requires AFC-approved hosting, access controls, security testing, audit trails, data protection review, and operational sign-off.")
