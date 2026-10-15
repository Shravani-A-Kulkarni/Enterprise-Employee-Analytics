# import streamlit as st

# from auth import PAGE_ACCESS
# from ui_helpers import (AnalyticsManager, DatabaseError, EmployeeManager,
#                         current_user, page_setup, show_error)

# user = current_user()
# page_setup("Enterprise Employee Analytics", "Ã°Å¸ÂÂ¢")

# # --- employees only get a welcome message --------------------------------------------
# if user["role"] == "Employee":
#     st.subheader(f"Welcome, {user['display_name']}")
#     st.write("Open **My Profile** in the sidebar to see your details, projects, "
#              "performance reviews and career history.")
#     st.stop()

# st.caption("HR data entry (OLTP) and analytics (Data Warehouse star schema)")

# # --- connection status -----------------------------------------------------------
# col1, col2 = st.columns(2)
# oltp_ok, oltp_msg = EmployeeManager().test_connection()
# olap_ok, olap_msg = AnalyticsManager().test_connection()
# col1.metric("OLTP database", "Connected" if oltp_ok else "Down")
# col1.caption(oltp_msg)
# col2.metric("Data warehouse (OLAP)", "Connected" if olap_ok else "Down")
# col2.caption(olap_msg)

# if not (oltp_ok and olap_ok):
#     st.warning("Check MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / OLTP_DB / OLAP_DB in your .env "
#                "(or Streamlit secrets when deployed).")
#     st.stop()


# # --- headline numbers ----------------------------------------------------------------
# @st.cache_data(ttl=300, show_spinner=False)
# def load_kpis():
#     return AnalyticsManager().kpis()


# try:
#     k = load_kpis()
#     st.subheader("Company snapshot")
#     a, b, c, d = st.columns(4)
#     a.metric("Current employees", f"{k['current_employees']:,}")
#     b.metric("Attrition rate", f"{k['attrition_rate']}%")
#     c.metric("Avg monthly income", f"{int(k['avg_income']):,}")
#     d.metric("Historical SCD versions", f"{k['past_versions']:,}")
#     e, f, _, _ = st.columns(4)
#     e.metric("Performance reviews", f"{k['reviews']:,}")
#     f.metric("Projects", f"{k['projects']:,}")
# except DatabaseError as exc:
#     show_error(exc)

# # --- page guide: only the pages this role can open ------------------------------------
# GUIDE = {
#     "Onboarding": "Add employees, **update department/role/salary (triggers SCD Type 2)**, search",
#     "Projects": "Create projects and assign employees",
#     "Reviews": "Submit performance reviews",
#     "Analytics": "Year-over-year trends, top performers, attrition risk, project bottlenecks",
# }
# rows = [f"| {name} | {GUIDE[name]} |" for name in PAGE_ACCESS[user["role"]] if name in GUIDE]
# st.markdown("**Use the sidebar to navigate**\n\n| Page | What it does |\n|---|---|\n" + "\n".join(rows))
import streamlit as st

from auth import PAGE_ACCESS
from ui_helpers import (AnalyticsManager, DatabaseError, EmployeeManager,
                        current_user, page_setup, show_error)

user = current_user()
page_setup("Enterprise Employee Analytics", ":material/home:")

# --- employees only get a welcome message --------------------------------------------
if user["role"] == "Employee":
    st.subheader(f"Welcome, {user['display_name']}")
    st.write("Open **My Profile** in the sidebar to see your details, projects, "
             "performance reviews and career history.")
    st.stop()

st.caption("HR data entry (OLTP) and analytics (Data Warehouse star schema)")

# --- connection status -----------------------------------------------------------
col1, col2 = st.columns(2)
oltp_ok, oltp_msg = EmployeeManager().test_connection()
olap_ok, olap_msg = AnalyticsManager().test_connection()
col1.metric("OLTP database", "Connected" if oltp_ok else "Down")
col1.caption(oltp_msg)
col2.metric("Data warehouse (OLAP)", "Connected" if olap_ok else "Down")
col2.caption(olap_msg)

if not (oltp_ok and olap_ok):
    st.warning("Check MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / OLTP_DB / OLAP_DB in your .env "
               "(or Streamlit secrets when deployed).")
    st.stop()


# --- headline numbers ----------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_kpis():
    return AnalyticsManager().kpis()


try:
    k = load_kpis()
    st.subheader("Company snapshot")
    a, b, c, d = st.columns(4)
    a.metric("Current employees", f"{k['current_employees']:,}")
    b.metric("Attrition rate", f"{k['attrition_rate']}%")
    c.metric("Avg monthly income", f"{int(k['avg_income']):,}")
    d.metric("Historical SCD versions", f"{k['past_versions']:,}")
    e, f, _, _ = st.columns(4)
    e.metric("Performance reviews", f"{k['reviews']:,}")
    f.metric("Projects", f"{k['projects']:,}")
except DatabaseError as exc:
    show_error(exc)

# --- page guide: only the pages this role can open ------------------------------------
GUIDE = {
    "Onboarding": "Add employees, **update department/role/salary (triggers SCD Type 2)**, search",
    "Employee Directory": "Look up employee IDs, names, email, department and role (read-only)",
    "Projects": "Create projects and assign employees",
    "Reviews": "Submit performance reviews",
    "Analytics": "Year-over-year trends, top performers, attrition risk, project bottlenecks",
}
rows = [f"| {name} | {GUIDE[name]} |" for name in PAGE_ACCESS[user["role"]] if name in GUIDE]
st.markdown("**Use the sidebar to navigate**\n\n| Page | What it does |\n|---|---|\n" + "\n".join(rows))

