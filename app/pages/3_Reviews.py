from datetime import date

import pandas as pd
import streamlit as st

from entities import RATING_LABELS
from ui_helpers import (DatabaseError, EmployeeManager, ReviewManager,
                        clear_dashboard_cache, page_setup, show_error)

page_setup("Performance Reviews", "⭐")
manager = ReviewManager()

tab_new, tab_hist = st.tabs(["Submit review", "Review history"])

with tab_new:
    number = st.number_input("Employee number", min_value=1, step=1, key="rev_number")
    employee = None
    try:
        employee = EmployeeManager().get_employee(int(number))
    except DatabaseError as exc:
        show_error(exc)
    if employee is None:
        st.info("No employee with that number.")
    else:
        st.write(f"**{employee['first_name']} {employee['last_name']}** - "
                 f"{employee['department_name']}, {employee['job_role_name']}")
        with st.form("review_form", clear_on_submit=True):
            rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=3,
                                      format_func=lambda r: f"{r} - {RATING_LABELS[r]}")
            review_date = st.date_input("Review date", date.today(), max_value=date(2027, 12, 31))
            comments = st.text_area("Comments (optional)", max_chars=500)
            go = st.form_submit_button("Submit review", type="primary")
        if go:
            try:
                review_id = manager.add_review(int(number), rating, review_date, comments)
                clear_dashboard_cache()
                st.success(f"Review {review_id} saved and added to the data warehouse.")
            except DatabaseError as exc:
                show_error(exc)

with tab_hist:
    filter_number = st.number_input("Employee number (0 = latest reviews of everyone)",
                                    min_value=0, step=1, value=0)
    try:
        rows = manager.list_reviews(int(filter_number) or None)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)
