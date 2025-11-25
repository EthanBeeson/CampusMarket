import streamlit as st
import os
import json
from datetime import datetime
#how does update and leave a review work together is there a way we can just make update your review replace leave a review after someone has filed out that form?
st.set_page_config(page_title="Admin Reports - Campus Market", layout="wide")

# Simple admin check based on config/admins.json
ADMINS_PATH = os.path.join("config", "admins.json")
REPORTS_PATH = os.path.join("reports", "reports.jsonl")
RESOLVED_PATH = os.path.join("reports", "resolved_reports.jsonl")


def load_admins():
    try:
        with open(ADMINS_PATH, "r", encoding="utf-8") as fh:
            return [e.lower() for e in json.load(fh)]
    except Exception:
        return []


def read_reports():
    reports = []
    if not os.path.exists(REPORTS_PATH):
        return reports
    with open(REPORTS_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                reports.append(obj)
            except Exception:
                continue
    return reports


def write_reports(reports):
    # overwrite reports file with given list
    os.makedirs(os.path.dirname(REPORTS_PATH), exist_ok=True)
    with open(REPORTS_PATH, "w", encoding="utf-8") as fh:
        for r in reports:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


# Page
st.title("Admin — Reported Listings")

if "user_email" not in st.session_state:
    st.error("You must have admin privileges to view reports.")
    st.stop()

current_email = st.session_state.get("user_email")
admins = load_admins()

if current_email.lower() not in admins:
    st.error("Access denied — you do not have admin privileges.")
    st.stop()

# Show stats
reports = read_reports()
st.markdown(f"**Open reports:** {len(reports)}")

if not reports:
    st.info("No current reports.")
else:
    for idx, rep in enumerate(reports):
        with st.expander(f"Report {idx+1}: listing {rep.get('listing_id')} — reported by {rep.get('reporter_id')}"):
            st.write(rep)
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Resolve", key=f"resolve_{idx}"):
                    # move this report to resolved file with resolver info
                    resolver = current_email
                    rep_res = rep.copy()
                    rep_res["resolved_by"] = resolver
                    rep_res["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                    os.makedirs(os.path.dirname(RESOLVED_PATH), exist_ok=True)
                    with open(RESOLVED_PATH, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rep_res, ensure_ascii=False) + "\n")

                    # remove from open reports and rewrite
                    reports.pop(idx)
                    write_reports(reports)
                    st.success("Report resolved and moved to resolved_reports.jsonl")
                    st.experimental_rerun()
            with col2:
                if st.button("Ignore (delete)", key=f"ignore_{idx}"):
                    reports.pop(idx)
                    write_reports(reports)
                    st.warning("Report ignored and moved from open reports")
                    st.experimental_rerun()

# Provide download links
st.markdown("---")
if os.path.exists(REPORTS_PATH):
    with open(REPORTS_PATH, "r", encoding="utf-8") as fh:
        st.download_button("Download open reports (JSONL)", fh.read(), file_name="reports.jsonl")
if os.path.exists(RESOLVED_PATH):
    with open(RESOLVED_PATH, "r", encoding="utf-8") as fh:
        st.download_button("Download resolved reports (JSONL)", fh.read(), file_name="resolved_reports.jsonl")
