# pages/3_Signup.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import create_user, validate_charlotte_email, validate_password

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Signup - Campus Market", layout="centered")

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

st.title("📝 Signup")

st.write("Create a new account with your @charlotte.edu email address.")
st.info("Password requirements: At least 8 characters with 1 special character")

with st.form("signup_form"):
    email = st.text_input("Student Email", placeholder="you@charlotte.edu")
    password = st.text_input("Password", type="password", 
                           help="Must be at least 8 characters with 1 special character")
    password_confirm = st.text_input("Confirm Password", type="password")
    submitted = st.form_submit_button("Sign Up")

    if submitted:
        if not email.strip():
            st.error("Please enter your student email.")
        else:
            # Validate Charlotte email
            is_valid_email, email_error = validate_charlotte_email(email)
            if not is_valid_email:
                st.error(email_error)
            elif not password:
                st.error("Please enter a password.")
            else:
                # Validate password
                is_valid_password, password_error = validate_password(password)
                if not is_valid_password:
                    st.error(password_error)
                elif password != password_confirm:
                    st.error("Passwords do not match.")
                else:
                    db = SessionLocal()
                    try:
                        user = create_user(db, email.strip().lower(), password)
                        
                        # Start session immediately after signup
                        st.session_state["user_email"] = user.email
                        st.session_state["user_id"] = user.id
                        st.session_state["authenticated"] = True
                        
                        st.success("Signup successful! 🎉 You are now logged in.")
                        st.rerun()
                        
                    except ValueError as e:
                        st.error(str(e))
                    finally:
                        db.close()