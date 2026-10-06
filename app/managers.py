"""managers.py - Data Access Layer.

Every manager INHERITS from DatabaseConnection (so it is itself a Singleton and
owns a connection) and wraps its work in try/except via DatabaseError.

  EmployeeManager  -> OLTP : employee CRUD + SCD Type 2 update
  ProjectManager   -> OLTP : projects + assignments
  ReviewManager    -> OLTP : performance reviews
  AnalyticsManager -> OLAP : star-schema queries (CTEs + window functions)

OLTP writes call the warehouse stored procedures from sql/06_app_support.sql
inside the SAME transaction, so OLTP and warehouse never disagree.
"""
from datetime import date, timedelta

from db_manager import DatabaseConnection, DatabaseError, get_setting
from entities import Employee, Project, Review, check_role

BASELINE_START = date(2025, 1, 1)   # same "current version" start date the synthesizer used


def olap_db():
    return get_setting("OLAP_DB", "enterprise_employee_analytics_olap")


# =============================================================================
class EmployeeManager(DatabaseConnection):
    DB_SETTING = "OLTP_DB"

    # ---- lookups (for dropdowns) -------------------------------------------------
    def get_departments(self):
        return self.query("SELECT department_id, department_name FROM Department ORDER BY department_name")

    def get_job_roles(self):
        return self.query("SELECT job_role_id, job_role_name FROM JobRole ORDER BY job_role_name")

    def get_education_fields(self):
        return self.query("SELECT education_field_id, education_field_name FROM EducationField ORDER BY education_field_name")

    # ---- CREATE ---------------------------------------------------------------
    def add_employee(self, emp: Employee):
        """Insert into OLTP, record the history row, push the new employee to the warehouse."""
        try:
            with self.transaction() as cur:
                cur.execute("SELECT COALESCE(MAX(employee_number), 0) + 1 AS n FROM Employee")
                emp.employee_number = cur.fetchone()["n"]
                row = emp.to_db_row()
                cols = ", ".join(row)
                marks = ", ".join(["%s"] * len(row))
                cur.execute(f"INSERT INTO Employee ({cols}) VALUES ({marks})", tuple(row.values()))
                employee_id = cur.lastrowid
                cur.execute(
                    """INSERT INTO employee_scd_history
                       (employee_number, department_id, job_role_id, education_field_id,
                        monthly_income, job_level, effective_start_date, effective_end_date, is_current)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, 1)""",
                    (emp.employee_number, emp.department_id, emp.job_role_id,
                     emp.education_field_id, emp.monthly_income, emp.job_level, date.today()))
                cur.execute(f"CALL {olap_db()}.sp_sync_new_employee(%s)", (emp.employee_number,))
            return {"employee_id": employee_id, "employee_number": emp.employee_number}
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not add employee: {exc}") from exc

    # ---- READ -----------------------------------------------------------------
    def search_employees(self, term=None, department_id=None, limit=100):
        sql = """SELECT e.employee_number, e.first_name, e.last_name, d.department_name,
                        j.job_role_name, e.job_level, e.monthly_income, e.attrition
                 FROM Employee e
                 JOIN Department d ON d.department_id = e.department_id
                 JOIN JobRole j ON j.job_role_id = e.job_role_id
                 WHERE 1 = 1"""
        params = []
        if term:
            term = term.strip()
            if term.isdigit():
                sql += " AND e.employee_number = %s"
                params.append(int(term))
            else:
                sql += " AND (e.first_name LIKE %s OR e.last_name LIKE %s)"
                params += [f"{term}%", f"{term}%"]
        if department_id:
            sql += " AND e.department_id = %s"
            params.append(department_id)
        sql += " ORDER BY e.employee_number DESC LIMIT %s"
        params.append(int(limit))
        return self.query(sql, params)

    def get_employee(self, employee_number):
        rows = self.query(
            """SELECT e.*, d.department_name, j.job_role_name, ef.education_field_name
               FROM Employee e
               JOIN Department d ON d.department_id = e.department_id
               JOIN JobRole j ON j.job_role_id = e.job_role_id
               JOIN EducationField ef ON ef.education_field_id = e.education_field_id
               WHERE e.employee_number = %s""", (employee_number,))
        return rows[0] if rows else None

    def get_dimension_history(self, employee_number):
        """All SCD2 versions of one employee as the warehouse sees them."""
        return self.query(
            f"""SELECT employee_key, department_name, job_role_name, job_level, monthly_income,
                       effective_start_date, effective_end_date, is_current
                FROM {olap_db()}.DimEmployee
                WHERE employee_number = %s
                ORDER BY effective_start_date IS NULL, effective_start_date, employee_key""",
            (employee_number,))

    # ---- UPDATE (SCD Type 2) --------------------------------------------------
    def update_employee(self, employee_number, department_id=None, job_role_id=None,
                        job_level=None, monthly_income=None):
        """Change department / role / level / salary.

        One transaction does all of this:
          1. update OLTP Employee
          2. close the current employee_scd_history row (or create the baseline) + insert the new one
          3. CALL sp_scd2_update_employee -> closes old DimEmployee row, inserts new version
        Returns {"changed": False} when nothing actually differs.
        """
        if job_level is not None and not 1 <= int(job_level) <= 5:
            raise DatabaseError("Job level must be between 1 and 5")
        if monthly_income is not None and int(monthly_income) < 1000:
            raise DatabaseError("Monthly income must be at least 1000")
        try:
            with self.transaction() as cur:
                cur.execute(
                    """SELECT department_id, job_role_id, job_level, monthly_income, education_field_id
                       FROM Employee WHERE employee_number = %s FOR UPDATE""", (employee_number,))
                old = cur.fetchone()
                if old is None:
                    raise DatabaseError(f"Employee {employee_number} not found")
                new = {
                    "department_id": department_id if department_id is not None else old["department_id"],
                    "job_role_id": job_role_id if job_role_id is not None else old["job_role_id"],
                    "job_level": job_level if job_level is not None else old["job_level"],
                    "monthly_income": monthly_income if monthly_income is not None else old["monthly_income"],
                }
                if all(new[k] == old[k] for k in new):
                    return {"changed": False}

                effective = date.today()
                cur.execute(
                    """SELECT history_id, effective_start_date FROM employee_scd_history
                       WHERE employee_number = %s AND is_current = 1
                       ORDER BY effective_start_date DESC LIMIT 1""", (employee_number,))
                hist = cur.fetchone()
                if hist and hist["effective_start_date"] and hist["effective_start_date"] >= effective:
                    effective = hist["effective_start_date"] + timedelta(days=1)
                day_before = effective - timedelta(days=1)

                if hist:
                    cur.execute(
                        """UPDATE employee_scd_history SET effective_end_date = %s, is_current = 0
                           WHERE history_id = %s""", (day_before, hist["history_id"]))
                else:   # employee had no history yet -> store the OLD version first
                    cur.execute(
                        """INSERT INTO employee_scd_history
                           (employee_number, department_id, job_role_id, education_field_id,
                            monthly_income, job_level, effective_start_date, effective_end_date, is_current)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)""",
                        (employee_number, old["department_id"], old["job_role_id"],
                         old["education_field_id"], old["monthly_income"], old["job_level"],
                         min(BASELINE_START, day_before), day_before))
                cur.execute(
                    """INSERT INTO employee_scd_history
                       (employee_number, department_id, job_role_id, education_field_id,
                        monthly_income, job_level, effective_start_date, effective_end_date, is_current)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, 1)""",
                    (employee_number, new["department_id"], new["job_role_id"],
                     old["education_field_id"], new["monthly_income"], new["job_level"], effective))
                cur.execute(
                    """UPDATE Employee SET department_id = %s, job_role_id = %s,
                              job_level = %s, monthly_income = %s
                       WHERE employee_number = %s""",
                    (new["department_id"], new["job_role_id"], new["job_level"],
                     new["monthly_income"], employee_number))
                cur.execute(
                    f"CALL {olap_db()}.sp_scd2_update_employee(%s, %s, %s, %s, %s, %s, @new_key)",
                    (employee_number, department_id, job_role_id, job_level, monthly_income, effective))
                cur.execute("SELECT @new_key AS new_key")
                new_key = cur.fetchone()["new_key"]
            return {"changed": True, "new_employee_key": new_key, "effective_date": effective}
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not update employee: {exc}") from exc

    # ---- DELETE ---------------------------------------------------------------
    def delete_employee(self, employee_number):
        """Hard delete from OLTP - only if the employee has no reviews/assignments.
        Warehouse rows are kept on purpose: history must stay reportable."""
        try:
            with self.transaction() as cur:
                cur.execute("SELECT employee_id FROM Employee WHERE employee_number = %s FOR UPDATE", (employee_number,))
                row = cur.fetchone()
                if row is None:
                    raise DatabaseError(f"Employee {employee_number} not found")
                cur.execute(
                    """SELECT (SELECT COUNT(*) FROM Reviews WHERE employee_id = %s) +
                              (SELECT COUNT(*) FROM Assignment WHERE employee_id = %s) AS n""",
                    (row["employee_id"], row["employee_id"]))
                if cur.fetchone()["n"] > 0:
                    raise DatabaseError("Employee has reviews or assignments and cannot be deleted")
                cur.execute("DELETE FROM employee_scd_history WHERE employee_number = %s", (employee_number,))
                cur.execute("DELETE FROM Employee WHERE employee_number = %s", (employee_number,))
            return True
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not delete employee: {exc}") from exc


# =============================================================================
class ProjectManager(DatabaseConnection):
    DB_SETTING = "OLTP_DB"

    def create_project(self, project: Project):
        try:
            with self.transaction() as cur:
                cur.execute(
                    """INSERT INTO Project (project_name, department_id, start_date, end_date, status)
                       VALUES (%s, %s, %s, %s, %s)""", project.to_db_row())
                project_id = cur.lastrowid
                cur.execute(f"CALL {olap_db()}.sp_sync_project(%s)", (project_id,))
            return project_id
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not create project: {exc}") from exc

    def list_projects(self, status=None):
        sql = """SELECT p.project_id, p.project_name, d.department_name, p.start_date, p.end_date, p.status,
                        (SELECT COUNT(*) FROM Assignment a WHERE a.project_id = p.project_id) AS team_size
                 FROM Project p JOIN Department d ON d.department_id = p.department_id"""
        params = []
        if status:
            sql += " WHERE p.status = %s"
            params.append(status)
        return self.query(sql + " ORDER BY p.project_id DESC", params)

    def employee_allocation(self, employee_number):
        rows = self.query(
            """SELECT COALESCE(SUM(a.allocation_percentage), 0) AS total
               FROM Assignment a JOIN Employee e ON e.employee_id = a.employee_id
               WHERE e.employee_number = %s""", (employee_number,))
        return int(rows[0]["total"])

    def assign_employee(self, employee_number, project_id, assigned_date, role, allocation):
        """Returns {'assignment_id', 'total_allocation'} (total > 100 means over-allocated)."""
        try:
            role = check_role(role)
        except ValueError as exc:
            raise DatabaseError(str(exc)) from exc
        if not 1 <= int(allocation) <= 100:
            raise DatabaseError("Allocation must be between 1 and 100")
        try:
            with self.transaction() as cur:
                cur.execute("SELECT employee_id FROM Employee WHERE employee_number = %s", (employee_number,))
                emp = cur.fetchone()
                if emp is None:
                    raise DatabaseError(f"Employee {employee_number} not found")
                cur.execute("SELECT 1 AS ok FROM Project WHERE project_id = %s", (project_id,))
                if cur.fetchone() is None:
                    raise DatabaseError(f"Project {project_id} not found")
                cur.execute(
                    "SELECT 1 AS ok FROM Assignment WHERE employee_id = %s AND project_id = %s",
                    (emp["employee_id"], project_id))
                if cur.fetchone():
                    raise DatabaseError("This employee is already assigned to that project")
                cur.execute(
                    """INSERT INTO Assignment (employee_id, project_id, assigned_date, role, allocation_percentage)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (emp["employee_id"], project_id, assigned_date, role, int(allocation)))
                assignment_id = cur.lastrowid
                cur.execute(f"CALL {olap_db()}.sp_sync_assignment(%s)", (assignment_id,))
                cur.execute(
                    "SELECT SUM(allocation_percentage) AS total FROM Assignment WHERE employee_id = %s",
                    (emp["employee_id"],))
                total = int(cur.fetchone()["total"])
            return {"assignment_id": assignment_id, "total_allocation": total}
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not assign employee: {exc}") from exc

    def list_assignments(self, project_id=None, limit=200):
        sql = """SELECT a.assignment_id, e.employee_number, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
                        p.project_name, a.role, a.allocation_percentage, a.assigned_date
                 FROM Assignment a
                 JOIN Employee e ON e.employee_id = a.employee_id
                 JOIN Project p ON p.project_id = a.project_id"""
        params = []
        if project_id:
            sql += " WHERE a.project_id = %s"
            params.append(project_id)
        sql += " ORDER BY a.assignment_id DESC LIMIT %s"
        params.append(int(limit))
        return self.query(sql, params)


# =============================================================================
class ReviewManager(DatabaseConnection):
    DB_SETTING = "OLTP_DB"

    def add_review(self, employee_number, rating, review_date=None, comments=""):
        try:
            rows = self.query("SELECT employee_id FROM Employee WHERE employee_number = %s", (employee_number,))
            if not rows:
                raise DatabaseError(f"Employee {employee_number} not found")
            try:
                review = Review(rows[0]["employee_id"], rating, review_date, comments)
            except ValueError as exc:
                raise DatabaseError(str(exc)) from exc
            with self.transaction() as cur:
                cur.execute(
                    """INSERT INTO Reviews (employee_id, review_date, review_period, rating, comments)
                       VALUES (%s, %s, %s, %s, %s)""", review.to_db_row())
                review_id = cur.lastrowid
                cur.execute(f"CALL {olap_db()}.sp_sync_review(%s)", (review_id,))
            return review_id
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Could not save review: {exc}") from exc

    def list_reviews(self, employee_number=None, limit=100):
        sql = """SELECT r.review_id, e.employee_number, CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
                        r.review_date, r.review_period, r.rating, r.comments
                 FROM Reviews r JOIN Employee e ON e.employee_id = r.employee_id"""
        params = []
        if employee_number:
            sql += " WHERE e.employee_number = %s"
            params.append(employee_number)
        sql += " ORDER BY r.review_date DESC, r.review_id DESC LIMIT %s"
        params.append(int(limit))
        return self.query(sql, params)


# =============================================================================
class AnalyticsManager(DatabaseConnection):
    """Reads ONLY from the star schema (OLAP database)."""
    DB_SETTING = "OLAP_DB"
    DB_DEFAULT = "enterprise_employee_analytics_olap"

    GROUPS = {"Department": "department_name", "Job role": "job_role_name"}

    def kpis(self):
        return self.query(
            """SELECT
                 (SELECT COUNT(*) FROM DimEmployee WHERE is_current = 1) AS current_employees,
                 (SELECT COUNT(*) FROM DimEmployee WHERE is_current = 0) AS past_versions,
                 (SELECT ROUND(100 * AVG(attrition = 'Yes'), 1) FROM DimEmployee WHERE is_current = 1) AS attrition_rate,
                 (SELECT ROUND(AVG(monthly_income)) FROM DimEmployee WHERE is_current = 1) AS avg_income,
                 (SELECT COUNT(*) FROM FactReview) AS reviews,
                 (SELECT COUNT(*) FROM DimProject) AS projects""")[0]

    def departments(self):
        return [r["department_name"] for r in self.query(
            "SELECT department_name FROM DimDepartment ORDER BY department_name")]

    def review_years(self):
        return [r["y"] for r in self.query(
            """SELECT DISTINCT dd.year AS y FROM FactReview fr
               JOIN DimDate dd ON dd.date_key = fr.date_key ORDER BY y""")]

    # ---- 1. year-over-year performance (CTE + LAG) -----------------------------------
    def yoy_performance(self, department=None):
        where, params = "", []
        if department:
            where, params = "WHERE de.department_name = %s", [department]
        return self.query_df(
            f"""WITH yearly AS (
                    SELECT dd.year AS review_year,
                           de.department_name,
                           ROUND(AVG(fr.rating), 3) AS avg_rating,
                           COUNT(*) AS reviews
                    FROM FactReview fr
                    JOIN DimDate dd     ON dd.date_key = fr.date_key
                    JOIN DimEmployee de ON de.employee_key = fr.employee_key
                    {where}
                    GROUP BY dd.year, de.department_name
                )
                SELECT review_year, department_name, avg_rating, reviews,
                       ROUND(avg_rating - LAG(avg_rating) OVER (
                             PARTITION BY department_name ORDER BY review_year), 3) AS yoy_change
                FROM yearly
                ORDER BY department_name, review_year""", params)

    # ---- 2. top performers per department (CTE + DENSE_RANK) -----------------------------
    def top_employees_by_department(self, top_n=5, year=None, department=None):
        filters, params = [], []
        if year:
            filters.append("dd.year = %s")
            params.append(int(year))
        if department:
            filters.append("cur.department_name = %s")
            params.append(department)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        params.append(int(top_n))
        return self.query_df(
            f"""WITH scores AS (
                    SELECT cur.employee_number,
                           CONCAT(cur.first_name, ' ', cur.last_name) AS employee_name,
                           cur.department_name, cur.job_role_name,
                           cur.performance_rating, cur.monthly_income,
                           ROUND(AVG(fr.rating), 2) AS avg_rating,
                           COUNT(*) AS review_count
                    FROM FactReview fr
                    JOIN DimDate dd     ON dd.date_key = fr.date_key
                    JOIN DimEmployee v  ON v.employee_key = fr.employee_key
                    JOIN DimEmployee cur ON cur.employee_number = v.employee_number AND cur.is_current = 1
                    {where}
                    GROUP BY cur.employee_number, cur.first_name, cur.last_name, cur.department_name,
                             cur.job_role_name, cur.performance_rating, cur.monthly_income
                ),
                ranked AS (
                    SELECT *, DENSE_RANK() OVER (
                               PARTITION BY department_name
                               ORDER BY avg_rating DESC, review_count DESC,
                                        performance_rating DESC, monthly_income DESC) AS dept_rank
                    FROM scores
                )
                SELECT department_name, dept_rank, employee_number, employee_name, job_role_name,
                       avg_rating, review_count, monthly_income
                FROM ranked
                WHERE dept_rank <= %s
                ORDER BY department_name, dept_rank, employee_number""", params)

    # ---- 3a. attrition by group ---------------------------------------------------------
    def attrition_by_group(self, group="Department"):
        col = self.GROUPS.get(group)
        if col is None:
            raise DatabaseError("Unknown grouping")
        return self.query_df(
            f"""SELECT {col} AS grp, COUNT(*) AS employees,
                       SUM(attrition = 'Yes') AS leavers,
                       ROUND(100 * AVG(attrition = 'Yes'), 2) AS attrition_rate
                FROM DimEmployee WHERE is_current = 1
                GROUP BY {col} ORDER BY attrition_rate DESC""")

    # ---- 3b. attrition RISK score for people who are still here -----------------------------
    RISK_CTE = """
        WITH dept_avg AS (
            SELECT department_name, AVG(monthly_income) AS avg_income
            FROM DimEmployee WHERE is_current = 1 GROUP BY department_name
        ),
        scored AS (
            SELECT de.employee_number,
                   CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
                   de.department_name, de.job_role_name, de.monthly_income,
                   ( (de.overtime = 'Yes')
                   + (de.job_satisfaction <= 2)
                   + (de.work_life_balance <= 2)
                   + (de.environment_satisfaction <= 2)
                   + (de.years_since_last_promotion >= 5)
                   + (de.distance_from_home >= 20)
                   + (de.monthly_income < 0.8 * da.avg_income)
                   + (de.years_at_company <= 2) ) AS risk_score
            FROM DimEmployee de
            JOIN dept_avg da ON da.department_name = de.department_name
            WHERE de.is_current = 1 AND de.attrition = 'No'
        ),
        banded AS (
            SELECT *, CASE WHEN risk_score >= 5 THEN 'High'
                           WHEN risk_score >= 3 THEN 'Medium' ELSE 'Low' END AS risk_band
            FROM scored
        )"""

    def attrition_risk_summary(self):
        return self.query_df(
            self.RISK_CTE + """
            SELECT department_name, risk_band, COUNT(*) AS employees
            FROM banded GROUP BY department_name, risk_band
            ORDER BY department_name, FIELD(risk_band, 'High', 'Medium', 'Low')""")

    def attrition_risk_top(self, limit=25, department=None):
        where, params = "", []
        if department:
            where, params = "WHERE department_name = %s", [department]
        params.append(int(limit))
        return self.query_df(
            self.RISK_CTE + f"""
            SELECT employee_number, employee_name, department_name, job_role_name,
                   monthly_income, risk_score, risk_band
            FROM banded {where}
            ORDER BY risk_score DESC, monthly_income ASC, employee_number
            LIMIT %s""", params)

    # ---- 4. project bottlenecks (CTEs + RANK) ----------------------------------------------
    def project_bottlenecks(self):
        return self.query_df(
            """WITH emp_load AS (
                   SELECT de.employee_number, SUM(fa.allocation_percentage) AS total_alloc
                   FROM FactAssignment fa
                   JOIN DimEmployee de ON de.employee_key = fa.employee_key
                   GROUP BY de.employee_number
               ),
               project_load AS (
                   SELECT fa.project_key,
                          COUNT(*) AS team_size,
                          ROUND(AVG(fa.allocation_percentage), 1) AS avg_allocation,
                          SUM(el.total_alloc > 100) AS overloaded_members
                   FROM FactAssignment fa
                   JOIN DimEmployee de ON de.employee_key = fa.employee_key
                   JOIN emp_load el    ON el.employee_number = de.employee_number
                   GROUP BY fa.project_key
               )
               SELECT dp.project_name, dp.department_name, dp.status,
                      COALESCE(pl.team_size, 0) AS team_size,
                      COALESCE(pl.avg_allocation, 0) AS avg_allocation,
                      COALESCE(pl.overloaded_members, 0) AS overloaded_members,
                      ROUND(100 * COALESCE(pl.overloaded_members, 0) / NULLIF(pl.team_size, 0), 1) AS pct_overloaded,
                      RANK() OVER (ORDER BY COALESCE(pl.overloaded_members, 0) DESC,
                                            COALESCE(pl.team_size, 0) DESC) AS bottleneck_rank
               FROM DimProject dp
               LEFT JOIN project_load pl ON pl.project_key = dp.project_key
               ORDER BY bottleneck_rank, dp.project_name""")

    def overallocated_employees(self, limit=25):
        return self.query_df(
            """SELECT cur.employee_number, CONCAT(cur.first_name, ' ', cur.last_name) AS employee_name,
                      cur.department_name, COUNT(*) AS projects, SUM(fa.allocation_percentage) AS total_allocation
               FROM FactAssignment fa
               JOIN DimEmployee v   ON v.employee_key = fa.employee_key
               JOIN DimEmployee cur ON cur.employee_number = v.employee_number AND cur.is_current = 1
               GROUP BY cur.employee_number, cur.first_name, cur.last_name, cur.department_name
               HAVING SUM(fa.allocation_percentage) > 100
               ORDER BY total_allocation DESC, cur.employee_number
               LIMIT %s""", [int(limit)])
