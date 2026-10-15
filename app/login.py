# """Login page (shown only while nobody is signed in)."""
# import streamlit as st

# from auth import AuthManager
# from db_manager import DatabaseError, get_setting

# left, mid, right = st.columns([1, 2, 1])
# with mid:
#     st.title("Ã°Å¸ÂÂ¢ Enterprise Employee Analytics")
#     st.subheader("Sign in")
#     with st.form("login_form"):
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")
#         go = st.form_submit_button("Sign in", type="primary", width="stretch")

#     if go:
#         try:
#             user = AuthManager().authenticate(email, password)
#         except DatabaseError as exc:
#             st.error(str(exc))
#         else:
#             if user is None:
#                 st.error("Invalid email or password.")
#             else:
#                 st.session_state["user"] = user
#                 st.rerun()

#     # Set SHOW_DEMO_LOGINS = "0" in .env / Streamlit secrets to hide this box on a public deployment.
#     if get_setting("SHOW_DEMO_LOGINS", "1") == "1":
#         with st.expander("Demo accounts (password for all: Demo@123)"):
#             st.markdown(
#                 """
# | Email | Role | Sees |
# |---|---|---|
# | `hr@company.com` | HR | Everything |
# | `manager@company.com` | Manager | Projects, Reviews, Analytics |
# | `employee1@company.com` | Employee | Own profile only (employee #1) |
# | `employee2@company.com` | Employee | Own profile only (employee #2) |
# """
#             )
"""Login page (shown only while nobody is signed in)."""
import streamlit as st

from auth import AuthManager
from db_manager import DatabaseError, get_setting

left, mid, right = st.columns([1, 2, 1])
with mid:
    st.title("🏢 Enterprise Employee Analytics")
    st.subheader("Sign in")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        go = st.form_submit_button("Sign in", type="primary", width="stretch")

    if go:
        try:
            user = AuthManager().authenticate(email, password)
        except DatabaseError as exc:
            st.error(str(exc))
        else:
            if user is None:
                st.error("Invalid email or password.")
            else:
                st.session_state["user"] = user
                st.rerun()

    st.page_link("signup.py", label="New employee? Create an account", icon=":material/person_add:")

    # Set SHOW_DEMO_LOGINS = "0" in .env / Streamlit secrets to hide this box on a public deployment.
    if get_setting("SHOW_DEMO_LOGINS", "1") == "1":
        with st.expander("Demo accounts (password for all: Demo@123)"):
            st.markdown(
                """
| Email | Role | Sees |
|---|---|---|
| `hr@company.com` | HR | Home, Onboarding, Reviews, Analytics |
| `manager@company.com` | Manager | Projects, Reviews, Analytics |
| `employee1@company.com` | Employee | Own profile only (employee #1) |
| `employee2@company.com` | Employee | Own profile only (employee #2) |
"""
            )


