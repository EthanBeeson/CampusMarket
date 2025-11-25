import streamlit as st
import os
import json
from datetime import datetime
#how does update and leave a review work together is there a way we can just make update your review replace leave a review after someone has filed out that form?
from app.db import SessionLocal
from app.models.listing import Listing
from app.models.image import Image

st.set_page_config(page_title="Admin Reports - Campus Market", layout="wide")

st.markdown(
    """
    <style>
        /* Global background */
        .stApp { background-color: #fffdf2 !important; }
        .block-container { max-width: 900px; margin: 0 auto; }

        /* Headings and main content text */
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        div[data-testid="stAppViewContainer"] h4,
        div[data-testid="stAppViewContainer"] h5,
        div[data-testid="stAppViewContainer"] h6 {
            color: #005035 !important;   /* Charlotte green headings */
        }
        div[data-testid="stAppViewContainer"] .stMarkdown,
        div[data-testid="stAppViewContainer"] p,
        div[data-testid="stAppViewContainer"] span,
        div[data-testid="stAppViewContainer"] label,
        div[data-testid="stAppViewContainer"] div:not([data-testid="stSidebar"]) {
            color: #333333 !important;   /* readable grey body text */
        }
        div[data-testid="stAppViewContainer"] .stCaption {
            color: #666666 !important;   /* softer grey captions */
        }

        /* Sidebar text stays white */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] .stMarkdown {
            color: #ffffff !important;
        }

        /* Inputs */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #666666 !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #003d28 !important;
            box-shadow: 0 0 0 3px rgba(0, 80, 53, 0.1) !important;
        }
        .stTextInput input[type="password"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        .stTextInput input[type="password"]::placeholder {
            color: #666666 !important;
        }

        /* Buttons: Charlotte green with white text */
        div.stButton > button,
        .stFormSubmitButton > button {
            background-color: #005035 !important;
            color: #ffffff !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 10px 14px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin-top: 15px !important;
        }
        div.stButton > button *,
        .stFormSubmitButton > button * {
            color: #ffffff !important;
        }
        div.stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background-color: #003d28 !important;
            border-color: #003d28 !important;
        }
        /* ADD THIS: Ensure form submit button text stays white on hover */
        .stFormSubmitButton > button:hover,
        .stFormSubmitButton > button:hover * {
            color: #ffffff !important;
        }
            /* ADD THIS: Specific fix for form submit button text */
.stFormSubmitButton > button {
    color: white !important;
}

.stFormSubmitButton > button div,
.stFormSubmitButton > button p,
.stFormSubmitButton > button span {
    color: white !important;
    -webkit-text-fill-color: white !important;
}

.stFormSubmitButton > button:hover,
.stFormSubmitButton > button:hover div,
.stFormSubmitButton > button:hover p,
.stFormSubmitButton > button:hover span {
    color: white !important;
    -webkit-text-fill-color: white !important;
}

/* Target the specific button content */
.stFormSubmitButton button [data-testid="stMarkdownContainer"],
.stFormSubmitButton button [data-testid="stMarkdownContainer"] * {
    color: white !important;
    -webkit-text-fill-color: white !important;
}
        /* Notifications/messages */
        div[data-testid="stNotification"] {
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            background-color: #ffffff !important;
        }
        div[data-testid="stNotification"] p,
        div[data-testid="stNotification"] span,
        div[data-testid="stNotification"] div {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        div[role="alert"] {
            background-color: rgba(211, 47, 47, 0.12) !important;
            border: 1px solid #d32f2f !important;
            border-radius: 8px !important;
        }
        div[data-testid="stNotification"]:not([role="alert"]) {
            background-color: rgba(0, 80, 53, 0.12) !important;
            border: 1px solid #005035 !important;
            border-radius: 8px !important;
        }

        /* Horizontal rule */
        hr { border-color: #cccccc !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

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

                # Admin delete listing flow (with confirmation)
                if st.button("Delete Listing (remove)", key=f"delete_listing_{idx}"):
                    # show a confirmation prompt on next render
                    st.session_state[f"confirm_delete_{rep.get('id')}"] = True

                if st.session_state.get(f"confirm_delete_{rep.get('id')}", False):
                    st.warning("Are you sure? This will permanently delete the listing and its images.")
                    c_yes, c_no = st.columns([1, 1])
                    if c_yes.button("Yes, delete listing", key=f"confirm_yes_{idx}"):
                        # perform deletion using DB session and also remove files
                        db = SessionLocal()
                        try:
                            listing_id = rep.get("listing_id")
                            listing = db.query(Listing).filter(Listing.id == listing_id).first()
                            if not listing:
                                st.error("Listing not found in database.")
                            else:
                                # remove image files from disk
                                try:
                                    for img in list(listing.images):
                                        try:
                                            if img.url and os.path.exists(img.url):
                                                os.remove(img.url)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                                # delete listing record
                                try:
                                    db.delete(listing)
                                    db.commit()
                                except Exception as e:
                                    db.rollback()
                                    st.error(f"Failed to delete listing: {e}")
                                    db.close()
                                    raise

                                # move report to resolved with resolution info
                                resolver = current_email
                                rep_res = rep.copy()
                                rep_res["resolved_by"] = resolver
                                rep_res["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                                rep_res["resolution"] = "deleted_listing"
                                os.makedirs(os.path.dirname(RESOLVED_PATH), exist_ok=True)
                                with open(RESOLVED_PATH, "a", encoding="utf-8") as fh:
                                    fh.write(json.dumps(rep_res, ensure_ascii=False) + "\n")

                                # remove from open reports and rewrite
                                reports.pop(idx)
                                write_reports(reports)
                                st.success("Listing deleted and report moved to resolved_reports.jsonl")
                                # cleanup session state and rerun
                                st.session_state.pop(f"confirm_delete_{rep.get('id')}", None)
                                db.close()
                                st.rerun()
                        finally:
                            try:
                                db.close()
                            except Exception:
                                pass
                    if c_no.button("Cancel", key=f"confirm_no_{idx}"):
                        st.session_state.pop(f"confirm_delete_{rep.get('id')}", None)
                        st.info("Deletion cancelled.")

# Provide download links
st.markdown("---")
if os.path.exists(REPORTS_PATH):
    with open(REPORTS_PATH, "r", encoding="utf-8") as fh:
        st.download_button("Download open reports (JSONL)", fh.read(), file_name="reports.jsonl")
if os.path.exists(RESOLVED_PATH):
    with open(RESOLVED_PATH, "r", encoding="utf-8") as fh:
        st.download_button("Download resolved reports (JSONL)", fh.read(), file_name="resolved_reports.jsonl")
