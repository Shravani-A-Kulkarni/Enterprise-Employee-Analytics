from datetime import date

import pandas as pd
import streamlit as st

from entities import PROJECT_STATUS, Project
from ui_helpers import (DatabaseError, ProjectManager, clear_dashboard_cache,
                        page_setup, safe_lookup_options, show_error)

page_setup("Projects", "📁")
manager = ProjectManager()
departments, _, _ = safe_lookup_options()

tab_new, tab_assign, tab_list = st.tabs(["Create project", "Assign employee", "Projects & teams"])

# ------------------------------------------------------------------ create
with tab_new:
    with st.form("project_form", clear_on_submit=True):
        name = st.text_input("Project name")
        c1, c2 = st.columns(2)
        dept = c1.selectbox("Owning department", list(departments))
        status = c2.selectbox("Status", PROJECT_STATUS)
        start = c1.date_input("Start date", date.today())
        has_end = c2.checkbox("Has an end date")
        end = c2.date_input("End date", date.today(), disabled=not has_end)
        submitted = st.form_submit_button("Create project", type="primary")
    if submitted:
        try:
            project = Project(name, departments[dept], start, end if has_end else None, status)
            project_id = manager.create_project(project)
            clear_dashboard_cache()
            st.success(f"Project '{project.project_name}' created (id {project_id}).")
        except ValueError as exc:
            st.warning(str(exc))
        except DatabaseError as exc:
            show_error(exc)

# ------------------------------------------------------------------ assign
with tab_assign:
    try:
        projects = manager.list_projects()
    except DatabaseError as exc:
        show_error(exc)
        projects = []
    labels = {f"{p['project_id']} - {p['project_name']} ({p['status']})": p["project_id"] for p in projects}
    with st.form("assign_form"):
        number = st.number_input("Employee number", min_value=1, step=1)
        project_label = st.selectbox("Project", list(labels))
        c1, c2, c3 = st.columns(3)
        role = c1.text_input("Role on project", "Developer")
        allocation = c2.slider("Allocation %", 5, 100, 50, step=5)
        assigned = c3.date_input("Assigned date", date.today())
        go = st.form_submit_button("Assign", type="primary")
    if go:
        try:
            result = manager.assign_employee(int(number), labels[project_label], assigned, role, allocation)
            clear_dashboard_cache()
            st.success(f"Assigned (assignment id {result['assignment_id']}).")
            if result["total_allocation"] > 100:
                st.warning(f"This employee is now allocated {result['total_allocation']}% in total - over 100%.")
        except DatabaseError as exc:
            show_error(exc)

# ------------------------------------------------------------------ list
with tab_list:
    status_filter = st.selectbox("Status filter", ["All"] + PROJECT_STATUS)
    try:
        rows = manager.list_projects(None if status_filter == "All" else status_filter)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        pick = st.selectbox("Show team of project", ["-"] + list(labels))
        if pick != "-":
            team = manager.list_assignments(labels[pick])
            st.dataframe(pd.DataFrame(team), width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)
