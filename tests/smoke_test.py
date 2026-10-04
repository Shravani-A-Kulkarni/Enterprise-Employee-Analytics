"""End-to-end check of the OOP layer against your REAL databases.

    python tests/smoke_test.py

It creates a few TEST rows (a test employee, a test project, one assignment and
one review) so you can see the whole OLTP -> SCD2 -> warehouse -> analytics chain
work. Prints PASS/FAIL per check; exits non-zero if anything fails.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from db_manager import DatabaseConnection, DatabaseError          # noqa: E402
from entities import Employee, Project                             # noqa: E402
from managers import (AnalyticsManager, EmployeeManager,           # noqa: E402
                      ProjectManager, ReviewManager)

failures = []


def check(name, condition, detail=""):
    print(("PASS  " if condition else "FAIL  ") + name + (f"  [{detail}]" if detail and not condition else ""))
    if not condition:
        failures.append(name)


em, pm, rm, am = EmployeeManager(), ProjectManager(), ReviewManager(), AnalyticsManager()

# --- Singleton -----------------------------------------------------------------
check("Singleton: same object every time", EmployeeManager() is em and AnalyticsManager() is am)
check("Singleton: OLTP and OLAP are different connections", em is not am and em.database_name != am.database_name)
check("OLTP connection works", em.test_connection()[0], em.test_connection()[1])
check("OLAP connection works", am.test_connection()[0], am.test_connection()[1])

# --- Entity validation -------------------------------------------------------------
try:
    Employee("A", "B", 15, "Male", "Single", 1, 1, 1, 3, 1, 5000)
    check("Entity rejects age 15", False)
except ValueError:
    check("Entity rejects age 15", True)

# --- Onboard + SCD2 ----------------------------------------------------------------
depts = {d["department_name"]: d["department_id"] for d in em.get_departments()}
roles = {r["job_role_name"]: r["job_role_id"] for r in em.get_job_roles()}
fields = {f["education_field_name"]: f["education_field_id"] for f in em.get_education_fields()}
emp = Employee("Smoke", "Test", 30, "Female", "Single", depts["Sales"], roles["Sales Executive"],
               2, 3, fields["Marketing"], 6000)
res = em.add_employee(emp)
number = res["employee_number"]
check("Onboard: employee saved in OLTP", em.get_employee(number) is not None)
hist = em.get_dimension_history(number)
check("Onboard: employee also in warehouse (1 current version)", len(hist) == 1 and hist[0]["is_current"] == 1)

r1 = em.update_employee(number, department_id=depts["Research & Development"])
check("SCD2: department change creates a new version", r1["changed"] and r1["new_employee_key"])
hist = em.get_dimension_history(number)
check("SCD2: now 2 versions, exactly 1 current", len(hist) == 2 and sum(h["is_current"] for h in hist) == 1)
old, new = hist[0], hist[1]
check("SCD2: old row closed, new row open", old["is_current"] == 0 and old["effective_end_date"] is not None
      and new["is_current"] == 1 and new["effective_end_date"] is None)
check("SCD2: department changed in the new version",
      old["department_name"] == "Sales" and new["department_name"] == "Research & Development")
check("SCD2: old end date is before new start date", old["effective_end_date"] < new["effective_start_date"])
check("SCD2: new key differs from old key (surrogate keys)", old["employee_key"] != new["employee_key"])

r2 = em.update_employee(number, department_id=depts["Research & Development"])
check("SCD2: no real change -> no new version", r2["changed"] is False and len(em.get_dimension_history(number)) == 2)

r3 = em.update_employee(number, monthly_income=7500, job_level=3)
check("SCD2: salary/level change creates a 3rd version", r3["changed"] and len(em.get_dimension_history(number)) == 3)

# --- Rollback: a failing update must leave NOTHING behind -----------------------------
before = em.query("SELECT COUNT(*) AS n FROM employee_scd_history WHERE employee_number = %s", (number,))[0]["n"]
try:
    em.update_employee(number, department_id=999)
    check("Rollback: invalid department rejected", False)
except DatabaseError:
    after = em.query("SELECT COUNT(*) AS n FROM employee_scd_history WHERE employee_number = %s", (number,))[0]["n"]
    check("Rollback: invalid department rejected and nothing half-written", before == after)
check("Rollback: warehouse versions unchanged", len(em.get_dimension_history(number)) == 3)

# --- Project, assignment, review ---------------------------------------------------------
pid = pm.create_project(Project("Smoke Test Project", depts["Sales"], date.today()))
check("Project created", any(p["project_id"] == pid for p in pm.list_projects()))
a = pm.assign_employee(number, pid, date.today(), "Tester", 60)
check("Assignment saved", a["assignment_id"] > 0 and a["total_allocation"] == 60)
try:
    pm.assign_employee(number, pid, date.today(), "Tester", 60)
    check("Duplicate assignment rejected", False)
except DatabaseError:
    check("Duplicate assignment rejected", True)
rid = rm.add_review(number, 5, date.today(), "Smoke test review")
check("Review saved", any(r["review_id"] == rid for r in rm.list_reviews(number)))
wh = am.query("SELECT COUNT(*) AS n FROM FactReview WHERE review_id = %s", (rid,))[0]["n"]
check("Review reached the warehouse (FactReview)", wh == 1)
wh = am.query("SELECT COUNT(*) AS n FROM FactAssignment WHERE assignment_id = %s", (a["assignment_id"],))[0]["n"]
check("Assignment reached the warehouse (FactAssignment)", wh == 1)
try:
    rm.add_review(number, 9)
    check("Invalid rating rejected", False)
except DatabaseError:
    check("Invalid rating rejected", True)

# --- Warehouse integrity ------------------------------------------------------------------
bad = am.query("""SELECT COUNT(*) AS n FROM (SELECT employee_number FROM DimEmployee WHERE is_current = 1
                  GROUP BY employee_number HAVING COUNT(*) > 1) x""")[0]["n"]
check("Warehouse: never 2 current rows for one employee", bad == 0)

# --- Analytics ----------------------------------------------------------------------------
k = am.kpis()
check("KPIs return data", k["current_employees"] > 0)
yoy = am.yoy_performance()
check("YoY performance returns rows + LAG column", not yoy.empty and "yoy_change" in yoy.columns)
top = am.top_employees_by_department(3)
check("Top-N per department uses DENSE_RANK", not top.empty and top["dept_rank"].max() <= 3)
check("Attrition by department", not am.attrition_by_group("Department").empty)
check("Attrition by job role", not am.attrition_by_group("Job role").empty)
check("Attrition risk summary", not am.attrition_risk_summary().empty)
check("Attrition risk top list", not am.attrition_risk_top(10).empty)
check("Project bottlenecks", not am.project_bottlenecks().empty)
check("Over-allocated employees query runs", am.overallocated_employees(5) is not None)

print()
print("ALL CHECKS PASSED" if not failures else f"{len(failures)} CHECK(S) FAILED: {failures}")
sys.exit(1 if failures else 0)
