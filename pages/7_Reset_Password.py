# pages/7_Reset_Password.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import reset_password_by_email, validate_charlotte_email, validate_password
from app.nav import render_nav_sidebar

st.set_page_config(page_title="Reset Password - Campus Market", layout="centered")

# Custom nav sidebar
render_nav_sidebar()

# Charlotte colors
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

st.title("🔒 Reset Password")
st.write("Forgot your password? Enter your Charlotte email to set a new one.")
st.info("Password requirements: At least 8 characters with 1 special character.")

# If logged in, pre-fill email but still allow reset
prefill_email = st.session_state.get("user_email", "")

# Track success across reruns so the "Go to Login" button stays visible
reset_success = st.session_state.get("reset_success", False)

with st.form("reset_password_form"):
    email = st.text_input("Student Email", placeholder="you@charlotte.edu", value=prefill_email)
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    submitted = st.form_submit_button("Reset Password")

    if submitted:
        # Validate email
        is_valid_email, email_error = validate_charlotte_email(email)
        if not is_valid_email:
            st.error(email_error)
        else:
            # Validate password rules
            is_valid_pw, pw_error = validate_password(new_password)
            if not is_valid_pw:
                st.error(pw_error)
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                db = SessionLocal()
                try:
                    reset_password_by_email(db, email.strip().lower(), new_password)
                    reset_success = True
                    st.session_state["reset_success"] = True
                    st.success("✅ Password reset successful! You can now log in with your new password.")
                except ValueError as e:
                    st.error(str(e))
                finally:
                    db.close()

# Post-form controls (buttons not allowed inside form)
if reset_success:
    if st.button("Go to Login"):
        st.session_state.pop("reset_success", None)
        st.switch_page("pages/2_Login.py")
