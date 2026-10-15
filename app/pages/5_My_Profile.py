# import pandas as pd
# import streamlit as st

# from ui_helpers import (DatabaseError, EmployeeManager, ProjectManager, ReviewManager,
#                         current_user, page_setup, show_error)

# page_setup("My Profile", ":material/account_circle:")
# user = current_user()
# number = user.get("employee_number")      # taken from the login, never typed in -> own data only

# if not number:
#     st.info("Your login is not linked to an employee record, so there is no personal profile to show.")
#     st.stop()

# try:
#     emp = EmployeeManager().get_employee(int(number))
# except DatabaseError as exc:
#     show_error(exc)
#     st.stop()
# if emp is None:
#     st.warning(f"Employee record {number} was not found.")
#     st.stop()

# tab_me, tab_proj, tab_rev, tab_hist = st.tabs(
#     ["My details", "My projects", "My reviews", "Career history"])

# with tab_me:
#     st.subheader(f"{emp['first_name']} {emp['last_name']}")
#     a, b, c = st.columns(3)
#     a.metric("Employee number", emp["employee_number"])
#     b.metric("Job level", emp["job_level"])
#     c.metric("Monthly income", f"{int(emp['monthly_income']):,}")
#     st.write(f"**Email:** {emp.get('email') or user['email']}")
#     st.write(f"**Department:** {emp['department_name']}  \n**Job role:** {emp['job_role_name']}")
#     st.write(f"**Education field:** {emp['education_field_name']}  \n"
#              f"**Total working years:** {emp['total_working_years']}  \n"
#              f"**Years at company:** {emp['years_at_company']}")

# with tab_proj:
#     try:
#         rows = ProjectManager().list_assignments(employee_number=int(number))
#         if rows:
#             df = pd.DataFrame(rows).drop(columns=["assignment_id", "employee_number", "employee_name"])
#             st.dataframe(df, width="stretch", hide_index=True)
#         else:
#             st.info("You are not assigned to any project yet.")
#     except DatabaseError as exc:
#         show_error(exc)

# with tab_rev:
#     try:
#         rows = ReviewManager().list_reviews(int(number))
#         if rows:
#             df = pd.DataFrame(rows).drop(columns=["review_id", "employee_number", "employee_name"])
#             st.dataframe(df, width="stretch", hide_index=True)
#         else:
#             st.info("No performance reviews yet.")
#     except DatabaseError as exc:
#         show_error(exc)

# with tab_hist:
#     st.caption("Every version of your department, role, level and salary (SCD Type 2).")
#     try:
#         rows = EmployeeManager().get_dimension_history(int(number))
#         if rows:
#             st.dataframe(pd.DataFrame(rows).drop(columns=["employee_key"]),
#                          width="stretch", hide_index=True)
#         else:
#             st.info("No history recorded.")
#     except DatabaseError as exc:
#         show_error(exc)
# import pandas as pd
# import streamlit as st

# from ui_helpers import (DatabaseError, EmployeeManager, ProjectManager, ReviewManager,
#                         current_user, page_setup, show_error)

# page_setup("My Profile", ":material/account_circle:")
# user = current_user()
# number = user.get("employee_number")      # taken from the login, never typed in -> own data only

# if not number:
#     st.info(f"Your account ({user['email']}) has not been linked to an employee profile yet. "
#             "Either HR has not created your employee record, or it has not been connected to "
#             "this login. Please ask HR to check that your employee record uses this same email address.")
#     st.stop()

# try:
#     emp = EmployeeManager().get_employee(int(number))
# except DatabaseError as exc:
#     show_error(exc)
#     st.stop()
# if emp is None:
#     st.warning(f"Your account is linked to employee number {number}, but no matching employee "
#                "record was found. Please contact HR.")
#     st.stop()

# tab_me, tab_proj, tab_rev, tab_hist = st.tabs(
#     ["My details", "My projects", "My reviews", "Career history"])

# with tab_me:
#     st.subheader(f"{emp['first_name']} {emp['last_name']}")
#     a, b, c = st.columns(3)
#     a.metric("Employee number", emp["employee_number"])
#     b.metric("Job level", emp["job_level"])
#     c.metric("Monthly income", f"{int(emp['monthly_income']):,}")
#     st.write(f"**Email:** {emp.get('email') or user['email']}")
#     st.write(f"**Department:** {emp['department_name']}  \n**Job role:** {emp['job_role_name']}")
#     st.write(f"**Education field:** {emp['education_field_name']}  \n"
#              f"**Total working years:** {emp['total_working_years']}  \n"
#              f"**Years at company:** {emp['years_at_company']}")

# with tab_proj:
#     try:
#         rows = ProjectManager().list_assignments(employee_number=int(number))
#         if rows:
#             df = pd.DataFrame(rows).drop(columns=["assignment_id", "employee_number", "employee_name"])
#             st.dataframe(df, width="stretch", hide_index=True)
#         else:
#             st.info("You are not assigned to any project yet.")
#     except DatabaseError as exc:
#         show_error(exc)

# with tab_rev:
#     try:
#         rows = ReviewManager().list_reviews(int(number))
#         if rows:
#             df = pd.DataFrame(rows).drop(columns=["review_id", "employee_number", "employee_name"])
#             st.dataframe(df, width="stretch", hide_index=True)
#         else:
#             st.info("No performance reviews yet.")
#     except DatabaseError as exc:
#         show_error(exc)

# with tab_hist:
#     st.caption("Every version of your department, role, level and salary (SCD Type 2).")
#     try:
#         rows = EmployeeManager().get_dimension_history(int(number))
#         if rows:
#             st.dataframe(pd.DataFrame(rows).drop(columns=["employee_key"]),
#                          width="stretch", hide_index=True)
#         else:
#             st.info("No history recorded.")
#     except DatabaseError as exc:
#         show_error(exc)
import pandas as pd
import streamlit as st

from auth import AuthManager
from ui_helpers import (DatabaseError, EmployeeManager, ProjectManager, ReviewManager,
                        current_user, page_setup, show_error)

# (label, column in the Employee row) - only the ones the row really has are shown
DETAIL_FIELDS = [
    ("Age", "age"), ("Gender", "gender"), ("Marital status", "marital_status"),
    ("Education level (1-5)", "education"), ("Education field", "education_field_name"),
    ("Distance from home (km)", "distance_from_home"),
    ("Department", "department_name"), ("Job role", "job_role_name"), ("Job level", "job_level"),
    ("Business travel", "business_travel"), ("Overtime", "overtime"),
    ("Total working years", "total_working_years"), ("Years at company", "years_at_company"),
    ("Years in current role", "years_in_current_role"),
    ("Years since last promotion", "years_since_last_promotion"),
    ("Years with current manager", "years_with_current_manager"),
    ("Companies worked before", "num_companies_worked"),
    ("Training times last year", "training_times_last_year"),
    ("Monthly income", "monthly_income"), ("Daily rate", "daily_rate"),
    ("Hourly rate", "hourly_rate"), ("Monthly rate", "monthly_rate"),
    ("Percent salary hike", "percent_salary_hike"), ("Stock option level", "stock_option_level"),
    ("Performance rating", "performance_rating"), ("Job satisfaction", "job_satisfaction"),
    ("Environment satisfaction", "environment_satisfaction"),
    ("Job involvement", "job_involvement"),
    ("Relationship satisfaction", "relationship_satisfaction"),
    ("Work-life balance", "work_life_balance"), ("Attrition", "attrition"),
]

page_setup("My Profile", ":material/account_circle:")
user = current_user()

# WHO is this? Decided from the signed-in account in the database - never from the URL or a form,
# so an employee can only ever see their own data.
try:
    number, source = AuthManager().find_employee_for_user(user)
except DatabaseError as exc:
    show_error(exc)
    st.stop()

if not number:
    st.info(f"Your account ({user['email']}) has not been linked to an employee profile yet. "
            "Either HR has not created your employee record, or it has not been connected to "
            "this login. Please ask HR to check that your employee record uses this same email address.")
    st.stop()                      # nothing below runs, so no other employee's data can appear

try:
    emp = EmployeeManager().get_employee(int(number))
except DatabaseError as exc:
    show_error(exc)
    st.stop()
if emp is None:
    st.warning(f"Your account is linked to employee number {number}, but no matching employee "
               "record was found. Please contact HR.")
    st.stop()

if source == "email":
    st.caption("Your profile was found by matching your login email to your employee record. "
               "Ask HR to confirm the link so it is saved on your account.")

tab_me, tab_proj, tab_rev, tab_hist = st.tabs(
    ["My details", "My projects", "My reviews", "Career history"])

with tab_me:
    st.subheader(f"{emp['first_name']} {emp['last_name']}")
    a, b, c = st.columns(3)
    a.metric("Employee number", emp["employee_number"])
    b.metric("Job level", emp["job_level"])
    c.metric("Monthly income", f"{int(emp['monthly_income']):,}")
    st.write(f"**Email:** {emp.get('email') or user['email']}")
    details = [(label, str(emp[key])) for label, key in DETAIL_FIELDS if emp.get(key) is not None]
    st.dataframe(pd.DataFrame(details, columns=["Detail", "Value"]), width="stretch", hide_index=True)

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
        rows = ReviewManager().list_reviews(int(number), limit=1000)
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


