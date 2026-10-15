"""Employee sign-up page (shown only while nobody is signed in)."""
import streamlit as st

from auth import AuthManager
from db_manager import DatabaseError

left, mid, right = st.columns([1, 2, 1])
with mid:
    st.title("🏢 Enterprise Employee Analytics")
    st.subheader("Create your account")
    with st.form("signup_form"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password",
                                 help="At least 8 characters, with a letter and a number.")
        confirm = st.text_input("Confirm password", type="password")
        go = st.form_submit_button("Sign up", type="primary", width="stretch")

    if go:
        try:
            AuthManager().sign_up(name, email, password, confirm)
        except ValueError as exc:          # bad input or duplicate email
            st.warning(str(exc))
        except DatabaseError as exc:       # database problem
            st.error(str(exc))
        else:
            st.success("Account created! You can now sign in.")

    st.page_link("login.py", label="Already have an account? Sign in", icon=":material/login:")



