# pages/7_Reset_Password.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import reset_password_by_email, validate_charlotte_email, validate_password

st.set_page_config(page_title="Reset Password - Campus Market", layout="centered")

# Charlotte colors
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035;
    }
    div[data-testid="stForm"] {
        background-color: #87B481;
        padding: 20px;
        border-radius: 10px;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        background-color: white;
        color: black;
    }
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: black !important;
        opacity: 1 !important;
    }
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
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
