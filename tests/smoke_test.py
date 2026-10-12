# """End-to-end check of the OOP layer against your REAL databases.

#     python tests/smoke_test.py

# It creates a few TEST rows (a test employee, a test project, one assignment and
# one review) so you can see the whole OLTP -> SCD2 -> warehouse -> analytics chain
# work. Prints PASS/FAIL per check; exits non-zero if anything fails.
# """
# import os
# import sys
# from datetime import date

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# from db_manager import DatabaseConnection, DatabaseError          # noqa: E402
# from entities import Employee, Project                             # noqa: E402
# from managers import (AnalyticsManager, EmployeeManager,           # noqa: E402
#                       ProjectManager, ReviewManager)

# failures = []


# def check(name, condition, detail=""):
#     print(("PASS  " if condition else "FAIL  ") + name + (f"  [{detail}]" if detail and not condition else ""))
#     if not condition:
#         failures.append(name)


# em, pm, rm, am = EmployeeManager(), ProjectManager(), ReviewManager(), AnalyticsManager()

# # --- Singleton -----------------------------------------------------------------
# check("Singleton: same object every time", EmployeeManager() is em and AnalyticsManager() is am)
# check("Singleton: OLTP and OLAP are different connections", em is not am and em.database_name != am.database_name)
# check("OLTP connection works", em.test_connection()[0], em.test_connection()[1])
# check("OLAP connection works", am.test_connection()[0], am.test_connection()[1])

# # --- Entity validation -------------------------------------------------------------
# try:
#     Employee("A", "B", 15, "Male", "Single", 1, 1, 1, 3, 1, 5000)
#     check("Entity rejects age 15", False)
# except ValueError:
#     check("Entity rejects age 15", True)

# # --- Onboard + SCD2 ----------------------------------------------------------------
# depts = {d["department_name"]: d["department_id"] for d in em.get_departments()}
# roles = {r["job_role_name"]: r["job_role_id"] for r in em.get_job_roles()}
# fields = {f["education_field_name"]: f["education_field_id"] for f in em.get_education_fields()}
# emp = Employee("Smoke", "Test", 30, "Female", "Single", depts["Sales"], roles["Sales Executive"],
#                2, 3, fields["Marketing"], 6000)
# res = em.add_employee(emp)
# number = res["employee_number"]
# check("Onboard: employee saved in OLTP", em.get_employee(number) is not None)
# hist = em.get_dimension_history(number)
# check("Onboard: employee also in warehouse (1 current version)", len(hist) == 1 and hist[0]["is_current"] == 1)

# r1 = em.update_employee(number, department_id=depts["Research & Development"])
# check("SCD2: department change creates a new version", r1["changed"] and r1["new_employee_key"])
# hist = em.get_dimension_history(number)
# check("SCD2: now 2 versions, exactly 1 current", len(hist) == 2 and sum(h["is_current"] for h in hist) == 1)
# old, new = hist[0], hist[1]
# check("SCD2: old row closed, new row open", old["is_current"] == 0 and old["effective_end_date"] is not None
#       and new["is_current"] == 1 and new["effective_end_date"] is None)
# check("SCD2: department changed in the new version",
#       old["department_name"] == "Sales" and new["department_name"] == "Research & Development")
# check("SCD2: old end date is before new start date", old["effective_end_date"] < new["effective_start_date"])
# check("SCD2: new key differs from old key (surrogate keys)", old["employee_key"] != new["employee_key"])

# r2 = em.update_employee(number, department_id=depts["Research & Development"])
# check("SCD2: no real change -> no new version", r2["changed"] is False and len(em.get_dimension_history(number)) == 2)

# r3 = em.update_employee(number, monthly_income=7500, job_level=3)
# check("SCD2: salary/level change creates a 3rd version", r3["changed"] and len(em.get_dimension_history(number)) == 3)

# # --- Rollback: a failing update must leave NOTHING behind -----------------------------
# before = em.query("SELECT COUNT(*) AS n FROM employee_scd_history WHERE employee_number = %s", (number,))[0]["n"]
# try:
#     em.update_employee(number, department_id=999)
#     check("Rollback: invalid department rejected", False)
# except DatabaseError:
#     after = em.query("SELECT COUNT(*) AS n FROM employee_scd_history WHERE employee_number = %s", (number,))[0]["n"]
#     check("Rollback: invalid department rejected and nothing half-written", before == after)
# check("Rollback: warehouse versions unchanged", len(em.get_dimension_history(number)) == 3)

# # --- Project, assignment, review ---------------------------------------------------------
# pid = pm.create_project(Project("Smoke Test Project", depts["Sales"], date.today()))
# check("Project created", any(p["project_id"] == pid for p in pm.list_projects()))
# a = pm.assign_employee(number, pid, date.today(), "Tester", 60)
# check("Assignment saved", a["assignment_id"] > 0 and a["total_allocation"] == 60)
# try:
#     pm.assign_employee(number, pid, date.today(), "Tester", 60)
#     check("Duplicate assignment rejected", False)
# except DatabaseError:
#     check("Duplicate assignment rejected", True)
# rid = rm.add_review(number, 5, date.today(), "Smoke test review")
# check("Review saved", any(r["review_id"] == rid for r in rm.list_reviews(number)))
# wh = am.query("SELECT COUNT(*) AS n FROM FactReview WHERE review_id = %s", (rid,))[0]["n"]
# check("Review reached the warehouse (FactReview)", wh == 1)
# wh = am.query("SELECT COUNT(*) AS n FROM FactAssignment WHERE assignment_id = %s", (a["assignment_id"],))[0]["n"]
# check("Assignment reached the warehouse (FactAssignment)", wh == 1)
# try:
#     rm.add_review(number, 9)
#     check("Invalid rating rejected", False)
# except DatabaseError:
#     check("Invalid rating rejected", True)

# # --- Warehouse integrity ------------------------------------------------------------------
# bad = am.query("""SELECT COUNT(*) AS n FROM (SELECT employee_number FROM DimEmployee WHERE is_current = 1
#                   GROUP BY employee_number HAVING COUNT(*) > 1) x""")[0]["n"]
# check("Warehouse: never 2 current rows for one employee", bad == 0)

# # --- Analytics ----------------------------------------------------------------------------
# k = am.kpis()
# check("KPIs return data", k["current_employees"] > 0)
# yoy = am.yoy_performance()
# check("YoY performance returns rows + LAG column", not yoy.empty and "yoy_change" in yoy.columns)
# top = am.top_employees_by_department(3)
# check("Top-N per department uses DENSE_RANK", not top.empty and top["dept_rank"].max() <= 3)
# check("Attrition by department", not am.attrition_by_group("Department").empty)
# check("Attrition by job role", not am.attrition_by_group("Job role").empty)
# check("Attrition risk summary", not am.attrition_risk_summary().empty)
# check("Attrition risk top list", not am.attrition_risk_top(10).empty)
# check("Project bottlenecks", not am.project_bottlenecks().empty)
# check("Over-allocated employees query runs", am.overallocated_employees(5) is not None)

# print()
# print("ALL CHECKS PASSED" if not failures else f"{len(failures)} CHECK(S) FAILED: {failures}")
# sys.exit(1 if failures else 0)
"""End-to-end check of the OOP layer against configured REAL databases.

Run manually: python tests/smoke_test.py

This integration script creates test rows (employee, project, assignment, review)
and may leave them in the database. Do not run against production casually.
All database work is inside main(), so pytest can import this module safely.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from db_manager import DatabaseError  # noqa: E402
from entities import Employee, Project  # noqa: E402
from managers import (  # noqa: E402
    AnalyticsManager, EmployeeManager, ProjectManager, ReviewManager
)


def check(name, condition, detail="", failures=None):
    """Print a PASS/FAIL result and optionally record a failure."""
    passed = bool(condition)
    print(("PASS  " if passed else "FAIL  ") + name +
          (f"  [{detail}]" if detail and not passed else ""))
    if not passed and failures is not None:
        failures.append(name)
    return passed


def main():
    failures = []
    em, pm, rm, am = (
        EmployeeManager(), ProjectManager(), ReviewManager(), AnalyticsManager()
    )

    # Singleton and connectivity
    check("Singleton: same object every time",
          EmployeeManager() is em and AnalyticsManager() is am,
          failures=failures)
    check("Singleton: OLTP and OLAP are different connections",
          em is not am and em.database_name != am.database_name,
          failures=failures)

    oltp_ok, oltp_detail = em.test_connection()
    check("OLTP connection works", oltp_ok, oltp_detail, failures)
    olap_ok, olap_detail = am.test_connection()
    check("OLAP connection works", olap_ok, olap_detail, failures)

    if not (oltp_ok and olap_ok):
        print(f"\n{len(failures)} CHECK(S) FAILED: {failures}")
        return 1

    # Entity validation
    try:
        Employee("A", "B", 15, "Male", "Single", 1, 1, 1, 3, 1, 5000)
        check("Entity rejects age 15", False, failures=failures)
    except ValueError:
        check("Entity rejects age 15", True, failures=failures)

    depts = {d["department_name"]: d["department_id"]
             for d in em.get_departments()}
    roles = {r["job_role_name"]: r["job_role_id"]
             for r in em.get_job_roles()}
    fields = {f["education_field_name"]: f["education_field_id"]
              for f in em.get_education_fields()}

    required = {"Sales", "Research & Development"}
    if not required.issubset(depts):
        check("Required departments exist", False,
              f"Missing: {sorted(required - set(depts))}", failures)
        print(f"\n{len(failures)} CHECK(S) FAILED: {failures}")
        return 1
    if "Sales Executive" not in roles or "Marketing" not in fields:
        check("Required job role and education field exist", False,
              "Expected Sales Executive and Marketing lookup values", failures)
        print(f"\n{len(failures)} CHECK(S) FAILED: {failures}")
        return 1

    # Onboarding and SCD Type 2
    emp = Employee("Smoke", "Test", 30, "Female", "Single",
                   depts["Sales"], roles["Sales Executive"],
                   2, 3, fields["Marketing"], 6000)
    result = em.add_employee(emp)
    number = result["employee_number"]
    check("Onboard: employee saved in OLTP",
          em.get_employee(number) is not None, failures=failures)

    history = em.get_dimension_history(number)
    check("Onboard: employee in warehouse (1 current version)",
          len(history) == 1 and history[0]["is_current"] == 1,
          failures=failures)

    result = em.update_employee(
        number, department_id=depts["Research & Development"])
    check("SCD2: department change creates a new version",
          result["changed"] and result["new_employee_key"],
          failures=failures)
    history = em.get_dimension_history(number)
    check("SCD2: 2 versions, exactly 1 current",
          len(history) == 2 and sum(h["is_current"] for h in history) == 1,
          failures=failures)

    if len(history) >= 2:
        old, new = history[0], history[1]
        check("SCD2: old row closed, new row open",
              old["is_current"] == 0 and old["effective_end_date"] is not None
              and new["is_current"] == 1 and new["effective_end_date"] is None,
              failures=failures)
        check("SCD2: department changed",
              old["department_name"] == "Sales"
              and new["department_name"] == "Research & Development",
              failures=failures)
        check("SCD2: old end date precedes new start date",
              old["effective_end_date"] is not None
              and old["effective_end_date"] < new["effective_start_date"],
              failures=failures)
        check("SCD2: surrogate keys differ",
              old["employee_key"] != new["employee_key"], failures=failures)
    else:
        for name in ("SCD2: old row closed, new row open",
                     "SCD2: department changed",
                     "SCD2: old end date precedes new start date",
                     "SCD2: surrogate keys differ"):
            check(name, False, "Expected two dimension versions", failures)

    result = em.update_employee(
        number, department_id=depts["Research & Development"])
    check("SCD2: no change creates no new version",
          result["changed"] is False
          and len(em.get_dimension_history(number)) == 2,
          failures=failures)

    result = em.update_employee(number, monthly_income=7500, job_level=3)
    check("SCD2: salary/level change creates third version",
          result["changed"] and len(em.get_dimension_history(number)) == 3,
          failures=failures)

    # Rollback check
    before = em.query(
        "SELECT COUNT(*) AS n FROM employee_scd_history "
        "WHERE employee_number = %s", (number,)
    )[0]["n"]
    try:
        em.update_employee(number, department_id=999)
        check("Rollback: invalid department rejected", False, failures=failures)
    except DatabaseError:
        after = em.query(
            "SELECT COUNT(*) AS n FROM employee_scd_history "
            "WHERE employee_number = %s", (number,)
        )[0]["n"]
        check("Rollback: failed update leaves no history rows behind",
              before == after, failures=failures)
    check("Rollback: warehouse versions unchanged",
          len(em.get_dimension_history(number)) == 3, failures=failures)

    # Project, assignment, review
    project_id = pm.create_project(
        Project("Smoke Test Project", depts["Sales"], date.today()))
    check("Project created",
          any(p["project_id"] == project_id for p in pm.list_projects()),
          failures=failures)

    assignment = pm.assign_employee(
        number, project_id, date.today(), "Tester", 60)
    check("Assignment saved",
          assignment["assignment_id"] > 0
          and assignment["total_allocation"] == 60,
          failures=failures)
    try:
        pm.assign_employee(number, project_id, date.today(), "Tester", 60)
        check("Duplicate assignment rejected", False, failures=failures)
    except DatabaseError:
        check("Duplicate assignment rejected", True, failures=failures)

    review_id = rm.add_review(number, 5, date.today(), "Smoke test review")
    check("Review saved",
          any(r["review_id"] == review_id for r in rm.list_reviews(number)),
          failures=failures)
    count = am.query(
        "SELECT COUNT(*) AS n FROM FactReview WHERE review_id = %s",
        (review_id,)
    )[0]["n"]
    check("Review reached warehouse (FactReview)", count == 1, failures=failures)
    count = am.query(
        "SELECT COUNT(*) AS n FROM FactAssignment WHERE assignment_id = %s",
        (assignment["assignment_id"],)
    )[0]["n"]
    check("Assignment reached warehouse (FactAssignment)",
          count == 1, failures=failures)

    try:
        rm.add_review(number, 9)
        check("Invalid rating rejected", False, failures=failures)
    except DatabaseError:
        check("Invalid rating rejected", True, failures=failures)

    # Warehouse integrity
    count = am.query(
        """SELECT COUNT(*) AS n FROM (
               SELECT employee_number FROM DimEmployee WHERE is_current = 1
               GROUP BY employee_number HAVING COUNT(*) > 1
           ) x"""
    )[0]["n"]
    check("Warehouse: no employee has two current versions",
          count == 0, failures=failures)

    # Analytics
    kpis = am.kpis()
    check("KPIs return data", kpis["current_employees"] > 0, failures=failures)
    yoy = am.yoy_performance()
    check("YoY performance returns rows and LAG column",
          not yoy.empty and "yoy_change" in yoy.columns, failures=failures)
    top = am.top_employees_by_department(3)
    check("Top-N per department uses DENSE_RANK",
          not top.empty and top["dept_rank"].max() <= 3, failures=failures)
    check("Attrition by department",
          not am.attrition_by_group("Department").empty, failures=failures)
    check("Attrition by job role",
          not am.attrition_by_group("Job role").empty, failures=failures)
    check("Attrition risk summary",
          not am.attrition_risk_summary().empty, failures=failures)
    check("Attrition risk top list",
          not am.attrition_risk_top(10).empty, failures=failures)
    check("Project bottlenecks",
          not am.project_bottlenecks().empty, failures=failures)
    check("Over-allocated employees query runs",
          am.overallocated_employees(5) is not None, failures=failures)

    print()
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED: {failures}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
