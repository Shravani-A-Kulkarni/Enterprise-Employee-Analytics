import pandas as pd
import streamlit as st

from ui_helpers import (DatabaseError, EmployeeManager, page_setup, require_roles,
                        safe_lookup_options, show_error)

require_roles("Manager", "HR")          # read-only, basic details only
page_setup("Employee Directory", ":material/contacts:")
st.caption("Find an employee's ID before assigning them to a project. "
           "Onboarding and employee changes are handled by HR.")

manager = EmployeeManager()
departments, _, _ = safe_lookup_options()

c1, c2 = st.columns([2, 1])
term = c1.text_input("Search by employee ID, name or email")
dept_filter = c2.selectbox("Department", ["All"] + list(departments))

try:
    rows = manager.list_directory(term or None,
                                  departments.get(dept_filter) if dept_filter != "All" else None)
except DatabaseError as exc:
    show_error(exc)
    st.stop()

if not rows:
    st.info("No employees match your search.")
    st.stop()

df = pd.DataFrame(rows).rename(columns={
    "employee_number": "Employee ID", "first_name": "First name", "last_name": "Last name",
    "email": "Email", "department_name": "Department", "job_role_name": "Job role",
    "job_level": "Job level", "employment_status": "Status"})
st.dataframe(df, width="stretch", hide_index=True,
             column_config={"Employee ID": st.column_config.NumberColumn("Employee ID", format="%d")})
st.caption(f"Showing up to 200 rows ({len(rows)} found). Newest employees first.")

# one-click copy of an ID
labels = {f"{r['first_name']} {r['last_name']} (ID {r['employee_number']})": r["employee_number"]
          for r in rows}
pick = st.selectbox("Copy an employee ID", list(labels))
st.code(str(labels[pick]), language=None)


