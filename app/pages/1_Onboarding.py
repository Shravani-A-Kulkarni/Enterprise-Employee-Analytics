import pandas as pd
import streamlit as st

from entities import GENDERS, MARITAL, TRAVEL, Employee
from ui_helpers import (DatabaseError, EmployeeManager, clear_dashboard_cache,
                        page_setup, safe_lookup_options, show_error)

page_setup("Employees", "👤")
manager = EmployeeManager()
departments, job_roles, edu_fields = safe_lookup_options()

tab_new, tab_update, tab_dir = st.tabs(["Onboard employee", "Update employee (SCD Type 2)", "Directory"])

# ------------------------------------------------------------------ onboard
with tab_new:
    with st.form("onboard_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        first = c1.text_input("First name")
        last = c2.text_input("Last name")
        age = c3.number_input("Age", 18, 70, 30)
        gender = c1.selectbox("Gender", GENDERS)
        marital = c2.selectbox("Marital status", MARITAL)
        education = c3.slider("Education level (1-5)", 1, 5, 3)
        dept = c1.selectbox("Department", list(departments))
        role = c2.selectbox("Job role", list(job_roles))
        level = c3.slider("Job level (1-5)", 1, 5, 1)
        field = c1.selectbox("Education field", list(edu_fields))
        income = c2.number_input("Monthly income", 1000, 1_000_000, 5000, step=500)
        travel = c3.selectbox("Business travel", TRAVEL, index=1)
        distance = c1.number_input("Distance from home (km)", 0, 500, 5)
        years = c2.number_input("Total working years", 0, 50, 0)
        companies = c3.number_input("Companies worked before", 0, 30, 0)
        overtime = c1.radio("Overtime", ["No", "Yes"], horizontal=True)
        submitted = st.form_submit_button("Onboard employee", type="primary")
    if submitted:
        try:
            emp = Employee(first, last, age, gender, marital, departments[dept], job_roles[role],
                           level, education, edu_fields[field], income, travel, distance,
                           overtime, years, companies)
            result = manager.add_employee(emp)
            clear_dashboard_cache()
            st.success(f"{emp.full_name()} onboarded with employee number {result['employee_number']}. "
                       "The data warehouse has been updated as well.")
        except ValueError as exc:       # validation from the entity class
            st.warning(str(exc))
        except DatabaseError as exc:
            show_error(exc)

# ------------------------------------------------------------------ update (SCD2)
with tab_update:
    st.write("Changing department, role, level or salary closes the employee's current "
             "warehouse record and opens a **new version** (SCD Type 2).")
    number = st.number_input("Employee number", min_value=1, step=1, key="upd_number")
    employee = None
    try:
        employee = manager.get_employee(int(number))
    except DatabaseError as exc:
        show_error(exc)

    if employee is None:
        st.info("No employee with that number.")
    else:
        st.write(f"**{employee['first_name']} {employee['last_name']}** - "
                 f"{employee['department_name']}, {employee['job_role_name']}, "
                 f"level {employee['job_level']}, income {employee['monthly_income']:,}")
        with st.form("update_form"):
            dept_names, role_names = list(departments), list(job_roles)
            new_dept = st.selectbox("Department", dept_names,
                                    index=dept_names.index(employee["department_name"]))
            new_role = st.selectbox("Job role", role_names,
                                    index=role_names.index(employee["job_role_name"]))
            new_level = st.slider("Job level", 1, 5, int(employee["job_level"]))
            new_income = st.number_input("Monthly income", 1000, 1_000_000,
                                         int(employee["monthly_income"]), step=500)
            go = st.form_submit_button("Save change", type="primary")
        if go:
            try:
                result = manager.update_employee(
                    int(number), departments[new_dept], job_roles[new_role], new_level, new_income)
                if result["changed"]:
                    clear_dashboard_cache()
                    st.success(f"Saved. New warehouse version created (employee_key "
                               f"{result['new_employee_key']}, effective {result['effective_date']}).")
                else:
                    st.info("Nothing changed - no new version was created.")
            except DatabaseError as exc:
                show_error(exc)

        st.markdown("**Version history in the data warehouse (DimEmployee)**")
        try:
            hist = manager.get_dimension_history(int(number))
            st.dataframe(pd.DataFrame(hist), width="stretch", hide_index=True)
        except DatabaseError as exc:
            show_error(exc)

        with st.expander("Danger zone: delete employee"):
            st.caption("Only possible when the employee has no reviews or assignments. "
                       "Warehouse history is kept.")
            if st.button("Delete this employee"):
                try:
                    manager.delete_employee(int(number))
                    clear_dashboard_cache()
                    st.success("Employee deleted from the OLTP database.")
                except DatabaseError as exc:
                    show_error(exc)

# ------------------------------------------------------------------ directory
with tab_dir:
    c1, c2 = st.columns([2, 1])
    term = c1.text_input("Search by name or employee number")
    dept_filter = c2.selectbox("Department", ["All"] + list(departments))
    try:
        rows = manager.search_employees(term or None,
                                        departments.get(dept_filter) if dept_filter != "All" else None)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(f"Showing up to 100 rows ({len(rows)} found).")
    except DatabaseError as exc:
        show_error(exc)
