import pandas as pd
import streamlit as st

from ui_helpers import (DatabaseError, EmployeeManager, ProjectManager, ReviewManager,
                        current_user, page_setup, show_error)

page_setup("My Profile", "🙋")
user = current_user()
number = user.get("employee_number")      # taken from the login, never typed in -> own data only

if not number:
    st.info("Your login is not linked to an employee record, so there is no personal profile to show.")
    st.stop()

try:
    emp = EmployeeManager().get_employee(int(number))
except DatabaseError as exc:
    show_error(exc)
    st.stop()
if emp is None:
    st.warning(f"Employee record {number} was not found.")
    st.stop()

tab_me, tab_proj, tab_rev, tab_hist = st.tabs(
    ["My details", "My projects", "My reviews", "Career history"])

with tab_me:
    st.subheader(f"{emp['first_name']} {emp['last_name']}")
    a, b, c = st.columns(3)
    a.metric("Employee number", emp["employee_number"])
    b.metric("Job level", emp["job_level"])
    c.metric("Monthly income", f"{int(emp['monthly_income']):,}")
    st.write(f"**Email:** {emp.get('email') or user['email']}")
    st.write(f"**Department:** {emp['department_name']}  \n**Job role:** {emp['job_role_name']}")
    st.write(f"**Education field:** {emp['education_field_name']}  \n"
             f"**Total working years:** {emp['total_working_years']}  \n"
             f"**Years at company:** {emp['years_at_company']}")

with tab_proj:
    try:
        rows = ProjectManager().list_assignments(employee_number=int(number))
        if rows:
            df = pd.DataFrame(rows).drop(columns=["assignment_id", "employee_number", "employee_name"])
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.info("You are not assigned to any project yet.")
    except DatabaseError as exc:
        show_error(exc)

with tab_rev:
    try:
        rows = ReviewManager().list_reviews(int(number))
        if rows:
            df = pd.DataFrame(rows).drop(columns=["review_id", "employee_number", "employee_name"])
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.info("No performance reviews yet.")
    except DatabaseError as exc:
        show_error(exc)

with tab_hist:
    st.caption("Every version of your department, role, level and salary (SCD Type 2).")
    try:
        rows = EmployeeManager().get_dimension_history(int(number))
        if rows:
            st.dataframe(pd.DataFrame(rows).drop(columns=["employee_key"]),
                         width="stretch", hide_index=True)
        else:
            st.info("No history recorded.")
    except DatabaseError as exc:
        show_error(exc)
