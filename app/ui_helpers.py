"""ui_helpers.py - small shared pieces used by every Streamlit page."""
import streamlit as st

from db_manager import DatabaseError
from managers import (AnalyticsManager, EmployeeManager, ProjectManager,
                      ReviewManager)


def page_setup(title, icon):
    st.set_page_config(page_title=f"{title} - Employee Analytics", page_icon=icon, layout="wide")
    st.title(f"{icon} {title}")


def show_error(exc):
    st.error(str(exc))


@st.cache_data(ttl=600, show_spinner=False)
def lookup_options():
    """Department / job role / education field dropdown data: {label: id}."""
    em = EmployeeManager()
    return (
        {r["department_name"]: r["department_id"] for r in em.get_departments()},
        {r["job_role_name"]: r["job_role_id"] for r in em.get_job_roles()},
        {r["education_field_name"]: r["education_field_id"] for r in em.get_education_fields()},
    )


def safe_lookup_options():
    try:
        return lookup_options()
    except DatabaseError as exc:
        show_error(exc)
        st.stop()


def clear_dashboard_cache():
    """Call after any write so the dashboards show the new data."""
    st.cache_data.clear()


__all__ = ["page_setup", "show_error", "safe_lookup_options", "clear_dashboard_cache",
           "EmployeeManager", "ProjectManager", "ReviewManager", "AnalyticsManager", "DatabaseError"]
