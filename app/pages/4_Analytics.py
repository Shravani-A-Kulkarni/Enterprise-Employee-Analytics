import plotly.express as px
import streamlit as st

from ui_helpers import AnalyticsManager, DatabaseError, page_setup, show_error

page_setup("Analytics Dashboard", "📊")


# Every query is cached for 5 minutes; forms clear the cache after a write.
@st.cache_data(ttl=300, show_spinner="Querying the data warehouse...")
def q(method, *args):
    return getattr(AnalyticsManager(), method)(*args)


try:
    departments = q("departments")
    years = q("review_years")
except DatabaseError as exc:
    show_error(exc)
    st.stop()

# ------------------------------------------------------------------ sidebar filters
st.sidebar.header("Filters")
dept_choice = st.sidebar.selectbox("Department", ["All"] + departments)
dept = None if dept_choice == "All" else dept_choice
top_n = st.sidebar.slider("Top N per department", 1, 10, 5)
year_choice = st.sidebar.selectbox("Year (top performers)", ["All years"] + [int(y) for y in years])
year = None if year_choice == "All years" else year_choice
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

tab_yoy, tab_top, tab_attr, tab_proj = st.tabs(
    ["Year-over-year performance", "Top performers", "Attrition risk", "Project bottlenecks"])

# ------------------------------------------------------------------ 1. YoY
with tab_yoy:
    try:
        df = q("yoy_performance", dept)
        if df.empty:
            st.info("No review data yet. Run sql/07_seed_demo_data.sql and the ETL, or submit reviews.")
        else:
            df["review_year"] = df["review_year"].astype(int)
            fig = px.line(df, x="review_year", y="avg_rating", color="department_name", markers=True,
                          labels={"review_year": "Year", "avg_rating": "Average rating",
                                  "department_name": "Department"},
                          title="Average review rating by year")
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, width="stretch")
            c1, c2 = st.columns(2)
            fig2 = px.bar(df, x="review_year", y="reviews", color="department_name", barmode="group",
                          title="Number of reviews per year")
            fig2.update_xaxes(dtick=1)
            c1.plotly_chart(fig2, width="stretch")
            c2.markdown("**Year-over-year change (SQL `LAG()` window function)**")
            c2.dataframe(df, width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)

# ------------------------------------------------------------------ 2. Top performers
with tab_top:
    st.caption("Ranked inside each department with SQL `DENSE_RANK()` on average review rating "
               "(ties broken by number of reviews, performance rating, salary).")
    try:
        df = q("top_employees_by_department", top_n, year, dept)
        if df.empty:
            st.info("No reviews match these filters.")
        else:
            df["label"] = df["employee_name"] + " (#" + df["employee_number"].astype(str) + ")"
            fig = px.bar(df, x="avg_rating", y="label", color="department_name", orientation="h",
                         hover_data=["job_role_name", "review_count", "dept_rank"],
                         labels={"avg_rating": "Average rating", "label": ""},
                         title=f"Top {top_n} per department" + (f" - {year}" if year else ""))
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(350, 28 * len(df) + 150))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(df.drop(columns="label"), width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)

# ------------------------------------------------------------------ 3. Attrition
with tab_attr:
    try:
        group = st.radio("Attrition rate by", ["Department", "Job role"], horizontal=True)
        df = q("attrition_by_group", group)
        fig = px.bar(df, x="grp", y="attrition_rate", text="attrition_rate", hover_data=["employees", "leavers"],
                     labels={"grp": group, "attrition_rate": "Attrition rate (%)"},
                     title=f"Attrition rate by {group.lower()} (current employees)")
        st.plotly_chart(fig, width="stretch")

        st.subheader("Who might leave next?")
        st.caption("Risk score (0-8) for employees still here: overtime, low job/environment satisfaction, "
                   "poor work-life balance, 5+ years without promotion, long commute, pay 20% below "
                   "department average, short tenure.")
        summary = q("attrition_risk_summary")
        if not summary.empty:
            if dept:
                summary = summary[summary["department_name"] == dept]
            fig = px.bar(summary, x="department_name", y="employees", color="risk_band",
                         category_orders={"risk_band": ["High", "Medium", "Low"]},
                         color_discrete_map={"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c"},
                         labels={"department_name": "Department", "employees": "Employees"},
                         title="Employees by attrition-risk band")
            st.plotly_chart(fig, width="stretch")
        st.markdown("**Highest-risk employees**")
        st.dataframe(q("attrition_risk_top", 25, dept), width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)

# ------------------------------------------------------------------ 4. Bottlenecks
with tab_proj:
    try:
        df = q("project_bottlenecks")
        if df.empty or df["team_size"].sum() == 0:
            st.info("No assignments yet. Run sql/07_seed_demo_data.sql and the ETL, or assign employees.")
        else:
            if dept:
                df = df[df["department_name"] == dept]
            st.caption("A project is a bottleneck when many of its team members are over-allocated "
                       "(total allocation above 100% across projects).")
            top = df.sort_values("bottleneck_rank").head(15)
            fig = px.bar(top, x="project_name", y="overloaded_members", color="status",
                         hover_data=["team_size", "avg_allocation", "pct_overloaded"],
                         labels={"project_name": "Project", "overloaded_members": "Over-allocated members"},
                         title="Projects with the most over-allocated team members")
            st.plotly_chart(fig, width="stretch")
            c1, c2 = st.columns(2)
            fig2 = px.scatter(df, x="team_size", y="avg_allocation", size="overloaded_members",
                              color="department_name", hover_name="project_name",
                              labels={"team_size": "Team size", "avg_allocation": "Average allocation %"},
                              title="Team size vs. average allocation")
            c1.plotly_chart(fig2, width="stretch")
            c2.markdown("**Most over-allocated people**")
            c2.dataframe(q("overallocated_employees", 15), width="stretch", hide_index=True)
            st.dataframe(df, width="stretch", hide_index=True)
    except DatabaseError as exc:
        show_error(exc)
