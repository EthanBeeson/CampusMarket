import json
import os
import streamlit as st

ADMIN_CONFIG_PATH = os.path.join("config", "admins.json")

NAV_ITEMS = [
    {"path": "home.py", "label": "Home"},
    {"path": "pages/1_create_listing.py", "label": "Create Listing"},
    {"path": "pages/2_Login.py", "label": "Login"},
    {"path": "pages/3_Signup.py", "label": "Sign Up"},
    {"path": "pages/4_Profile.py", "label": "Profile"},
    {"path": "pages/5_Messages.py", "label": "Messages"},
]

ADMIN_ITEM = {"path": "pages/Admin_Reports.py", "label": "Admin Reports"}


def _load_admins():
    """Return lowercase admin emails from config/admins.json."""
    try:
        with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return [str(e).lower() for e in data]
    except Exception:
        return []
    return []


def _is_admin_user() -> bool:
    email = st.session_state.get("user_email")
    if not email:
        return False
    return email.lower() in _load_admins()


def render_nav_sidebar():
    """Render custom navigation sidebar with optional admin link."""
    with st.sidebar:
        st.markdown(
            """
            <style>
            /* Black/white, aligned nav links in sidebar */
            section[data-testid="stSidebar"] [data-testid="stPageLink-container"] a {
                color: #111 !important;
                font-weight: 700;
                letter-spacing: 0.2px;
                font-size: 1.05rem;
            }
            section[data-testid="stSidebar"] [data-testid="stPageLink-container"] {
                margin-bottom: 0.25rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        for item in NAV_ITEMS:
            st.page_link(item["path"], label=item["label"], icon=None)

        if _is_admin_user():
            st.page_link(ADMIN_ITEM["path"], label=ADMIN_ITEM["label"], icon=None)

        st.divider()
