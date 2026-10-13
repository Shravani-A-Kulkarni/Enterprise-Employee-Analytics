import pytest
from unittest.mock import Mock
from contextlib import nullcontext
from managers import (
    EmployeeManager,
    ProjectManager,
    ReviewManager,
    AnalyticsManager,
    DatabaseError,
)


@pytest.fixture
def employee_manager():
    manager = object.__new__(EmployeeManager)
    manager.query = Mock(return_value=[])
    return manager


@pytest.fixture
def project_manager():
    manager = object.__new__(ProjectManager)
    manager.query = Mock(return_value=[])
    return manager


@pytest.fixture
def review_manager():
    manager = object.__new__(ReviewManager)
    manager.query = Mock(return_value=[])
    return manager


@pytest.fixture
def analytics_manager():
    manager = object.__new__(AnalyticsManager)
    manager.query = Mock(return_value=[])
    manager.query_df = Mock(return_value=[])
    return manager


# EmployeeManager tests

def test_get_departments(employee_manager):
    employee_manager.query.return_value = [
        {"department_id": 1, "department_name": "HR"}
    ]

    result = employee_manager.get_departments()

    assert result[0]["department_name"] == "HR"
    employee_manager.query.assert_called_once()


def test_get_job_roles(employee_manager):
    employee_manager.query.return_value = [
        {"job_role_id": 1, "job_role_name": "Engineer"}
    ]

    result = employee_manager.get_job_roles()

    assert result[0]["job_role_name"] == "Engineer"


def test_get_education_fields(employee_manager):
    employee_manager.query.return_value = [
        {"education_field_id": 1, "education_field_name": "Life Sciences"}
    ]

    result = employee_manager.get_education_fields()

    assert result[0]["education_field_name"] == "Life Sciences"


def test_search_employees_by_number(employee_manager):
    employee_manager.search_employees("123")

    sql, params = employee_manager.query.call_args.args

    assert "e.employee_number = %s" in sql
    assert params == [123, 100]


def test_search_employees_by_name_and_department(employee_manager):
    employee_manager.search_employees(
        term="  Ana ",
        department_id=2,
        limit=20,
    )

    sql, params = employee_manager.query.call_args.args

    assert "e.first_name LIKE %s OR e.last_name LIKE %s" in sql
    assert "e.department_id = %s" in sql
    assert params == ["Ana%", "Ana%", 2, 20]


def test_search_employees_without_filters(employee_manager):
    employee_manager.search_employees()

    _, params = employee_manager.query.call_args.args

    assert params == [100]


def test_get_employee_found(employee_manager):
    employee_manager.query.return_value = [{"employee_number": 123}]

    assert employee_manager.get_employee(123) == {"employee_number": 123}


def test_get_employee_not_found(employee_manager):
    employee_manager.query.return_value = []

    assert employee_manager.get_employee(999) is None


def test_get_dimension_history(employee_manager):
    employee_manager.query.return_value = [{"employee_key": 10}]

    result = employee_manager.get_dimension_history(123)

    assert result == [{"employee_key": 10}]
    employee_manager.query.assert_called_once()


# ProjectManager tests

def test_list_projects_without_status(project_manager):
    project_manager.list_projects()

    sql, params = project_manager.query.call_args.args

    assert "ORDER BY p.project_id DESC" in sql
    assert params == []


def test_list_projects_with_status(project_manager):
    project_manager.list_projects(status="Active")

    sql, params = project_manager.query.call_args.args

    assert "WHERE p.status = %s" in sql
    assert params == ["Active"]


def test_employee_allocation(project_manager):
    project_manager.query.return_value = [{"total": 75}]

    assert project_manager.employee_allocation(123) == 75


def test_list_assignments_without_filters(project_manager):
    project_manager.list_assignments()

    sql, params = project_manager.query.call_args.args

    assert "ORDER BY a.assignment_id DESC LIMIT %s" in sql
    assert params == [200]


def test_list_assignments_with_project_filter(project_manager):
    project_manager.list_assignments(project_id=5, limit=10)

    sql, params = project_manager.query.call_args.args

    assert "WHERE a.project_id = %s" in sql
    assert params == [5, 10]


# ReviewManager tests

def test_list_reviews_without_employee_filter(review_manager):
    review_manager.list_reviews()

    sql, params = review_manager.query.call_args.args

    assert "ORDER BY r.review_date DESC, r.review_id DESC" in sql
    assert params == [100]


def test_list_reviews_with_employee_filter(review_manager):
    review_manager.list_reviews(employee_number=123, limit=10)

    sql, params = review_manager.query.call_args.args

    assert "WHERE e.employee_number = %s" in sql
    assert params == [123, 10]


# AnalyticsManager tests

def test_kpis(analytics_manager):
    expected = {"current_employees": 100}

    analytics_manager.query.return_value = [expected]

    assert analytics_manager.kpis() == expected


def test_departments(analytics_manager):
    analytics_manager.query.return_value = [
        {"department_name": "HR"},
        {"department_name": "IT"},
    ]

    assert analytics_manager.departments() == ["HR", "IT"]


def test_review_years(analytics_manager):
    analytics_manager.query.return_value = [
        {"y": 2024},
        {"y": 2025},
    ]

    assert analytics_manager.review_years() == [2024, 2025]


def test_yoy_performance_without_department(analytics_manager):
    analytics_manager.yoy_performance()

    _, params = analytics_manager.query_df.call_args.args

    assert params == []


def test_yoy_performance_with_department(analytics_manager):
    analytics_manager.yoy_performance(department="HR")

    sql, params = analytics_manager.query_df.call_args.args

    assert "WHERE de.department_name = %s" in sql
    assert params == ["HR"]


def test_top_employees_without_filters(analytics_manager):
    analytics_manager.top_employees_by_department(top_n=3)

    _, params = analytics_manager.query_df.call_args.args

    assert params == [3]


def test_top_employees_with_year_and_department(analytics_manager):
    analytics_manager.top_employees_by_department(
        top_n=2,
        year=2025,
        department="HR",
    )

    sql, params = analytics_manager.query_df.call_args.args

    assert "dd.year = %s" in sql
    assert "cur.department_name = %s" in sql
    assert params == [2025, "HR", 2]


@pytest.mark.parametrize(
    ("group", "column"),
    [
        ("Department", "department_name"),
        ("Job role", "job_role_name"),
    ],
)
def test_attrition_by_group_valid(analytics_manager, group, column):
    analytics_manager.attrition_by_group(group)

    sql = analytics_manager.query_df.call_args.args[0]

    assert column in sql


def test_attrition_by_group_invalid(analytics_manager):
    with pytest.raises(DatabaseError, match="Unknown grouping"):
        analytics_manager.attrition_by_group("Invalid")


def test_attrition_risk_summary(analytics_manager):
    analytics_manager.attrition_risk_summary()

    sql = analytics_manager.query_df.call_args.args[0]

    assert "FROM banded" in sql


def test_attrition_risk_top_without_department(analytics_manager):
    analytics_manager.attrition_risk_top(limit=10)

    sql, params = analytics_manager.query_df.call_args.args

    assert "LIMIT %s" in sql
    assert params == [10]


def test_attrition_risk_top_with_department(analytics_manager):
    analytics_manager.attrition_risk_top(limit=5, department="HR")

    sql, params = analytics_manager.query_df.call_args.args

    assert "WHERE department_name = %s" in sql
    assert params == ["HR", 5]


def test_project_bottlenecks(analytics_manager):
    analytics_manager.project_bottlenecks()

    sql = analytics_manager.query_df.call_args.args[0]

    assert "RANK() OVER" in sql


def test_overallocated_employees(analytics_manager):
    analytics_manager.overallocated_employees(limit=7)

    _, params = analytics_manager.query_df.call_args.args

    assert params == [7]


# Section 2: Write operations and error handling


def make_cursor(fetchone_values=(), lastrowid=101):
    """Create a fake database cursor without connecting to MySQL."""
    cursor = Mock()
    cursor.fetchone.side_effect = list(fetchone_values)
    cursor.lastrowid = lastrowid
    return cursor


def attach_cursor_transaction(manager, cursor):
    """Make transaction() return the fake cursor."""
    manager.transaction = Mock(return_value=nullcontext(cursor))


# EmployeeManager: add employee

def test_add_employee_success(employee_manager, monkeypatch):
    import managers as managers_module

    cursor = make_cursor([{"n": 123}], lastrowid=501)
    attach_cursor_transaction(employee_manager, cursor)

    employee = Mock()
    employee.employee_number = None
    employee.department_id = 1
    employee.job_role_id = 2
    employee.education_field_id = 3
    employee.monthly_income = 5000
    employee.job_level = 2
    employee.to_db_row.return_value = {
        "employee_number": 123,
        "department_id": 1,
    }

    monkeypatch.setattr(managers_module, "olap_db", lambda: "test_warehouse")

    result = employee_manager.add_employee(employee)

    assert result == {"employee_id": 501, "employee_number": 123}
    assert employee.employee_number == 123
    assert cursor.execute.call_count == 4


def test_add_employee_database_error_is_reraised(employee_manager):
    cursor = make_cursor([{"n": 123}])
    attach_cursor_transaction(employee_manager, cursor)

    employee = Mock()
    employee.department_id = 1
    employee.job_role_id = 2
    employee.education_field_id = 3
    employee.monthly_income = 5000
    employee.job_level = 2
    employee.to_db_row.side_effect = DatabaseError("database failure")

    with pytest.raises(DatabaseError, match="database failure"):
        employee_manager.add_employee(employee)


def test_add_employee_unexpected_error_is_wrapped(employee_manager):
    cursor = make_cursor([{"n": 123}])
    attach_cursor_transaction(employee_manager, cursor)

    employee = Mock()
    employee.to_db_row.side_effect = RuntimeError("unexpected failure")

    with pytest.raises(DatabaseError, match="Could not add employee"):
        employee_manager.add_employee(employee)


# EmployeeManager: update employee

def test_update_employee_rejects_invalid_job_level(employee_manager):
    with pytest.raises(DatabaseError, match="Job level"):
        employee_manager.update_employee(123, job_level=6)


def test_update_employee_rejects_low_income(employee_manager):
    with pytest.raises(DatabaseError, match="Monthly income"):
        employee_manager.update_employee(123, monthly_income=999)


def test_update_employee_not_found(employee_manager):
    cursor = make_cursor([None])
    attach_cursor_transaction(employee_manager, cursor)

    with pytest.raises(DatabaseError, match="not found"):
        employee_manager.update_employee(123, job_level=3)


def test_update_employee_without_changes(employee_manager):
    old = {
        "department_id": 1,
        "job_role_id": 2,
        "job_level": 3,
        "monthly_income": 5000,
        "education_field_id": 4,
    }
    cursor = make_cursor([old])
    attach_cursor_transaction(employee_manager, cursor)

    result = employee_manager.update_employee(123)

    assert result == {"changed": False}
    assert cursor.execute.call_count == 1


def test_update_employee_creates_new_history(employee_manager, monkeypatch):
    import managers as managers_module

    old = {
        "department_id": 1,
        "job_role_id": 2,
        "job_level": 2,
        "monthly_income": 5000,
        "education_field_id": 4,
    }
    cursor = make_cursor([old, None, {"new_key": 99}])
    attach_cursor_transaction(employee_manager, cursor)
    monkeypatch.setattr(managers_module, "olap_db", lambda: "test_warehouse")

    result = employee_manager.update_employee(123, job_level=3)

    assert result["changed"] is True
    assert result["new_employee_key"] == 99
    assert "effective_date" in result
    assert cursor.execute.call_count == 7


# EmployeeManager: delete employee

def test_delete_employee_not_found(employee_manager):
    cursor = make_cursor([None])
    attach_cursor_transaction(employee_manager, cursor)

    with pytest.raises(DatabaseError, match="not found"):
        employee_manager.delete_employee(999)


def test_delete_employee_with_reviews_or_assignments(employee_manager):
    cursor = make_cursor([
        {"employee_id": 10},
        {"n": 2},
    ])
    attach_cursor_transaction(employee_manager, cursor)

    with pytest.raises(DatabaseError, match="cannot be deleted"):
        employee_manager.delete_employee(123)


def test_delete_employee_success(employee_manager):
    cursor = make_cursor([
        {"employee_id": 10},
        {"n": 0},
    ])
    attach_cursor_transaction(employee_manager, cursor)

    assert employee_manager.delete_employee(123) is True
    assert cursor.execute.call_count == 4


# ProjectManager: create project

def test_create_project_success(project_manager, monkeypatch):
    import managers as managers_module

    cursor = make_cursor(lastrowid=77)
    attach_cursor_transaction(project_manager, cursor)
    monkeypatch.setattr(managers_module, "olap_db", lambda: "test_warehouse")

    project = Mock()
    project.to_db_row.return_value = ("Project A", 1, None, None, "Active")

    assert project_manager.create_project(project) == 77
    assert cursor.execute.call_count == 2


def test_create_project_unexpected_error(project_manager):
    cursor = make_cursor()
    attach_cursor_transaction(project_manager, cursor)

    project = Mock()
    project.to_db_row.side_effect = RuntimeError("insert failed")

    with pytest.raises(DatabaseError, match="Could not create project"):
        project_manager.create_project(project)


# ProjectManager: assignment validation

@pytest.mark.parametrize("allocation", [0, -1, 101])
def test_assign_employee_rejects_invalid_allocation(
    project_manager, allocation
):
    with pytest.raises(DatabaseError, match="Allocation"):
        project_manager.assign_employee(
            123, 1, "2026-01-01", "Developer", allocation
        )


def test_assign_employee_rejects_invalid_role(project_manager):
    with pytest.raises(DatabaseError):
        project_manager.assign_employee(
            123, 1, "2026-01-01", "Invalid Role", 50
        )


def test_assign_employee_employee_not_found(project_manager):
    cursor = make_cursor([None])
    attach_cursor_transaction(project_manager, cursor)

    with pytest.raises(DatabaseError, match="not found"):
        project_manager.assign_employee(
            123, 1, "2026-01-01", "Developer", 50
        )


# ReviewManager: review validation

def test_add_review_employee_not_found(review_manager):
    review_manager.query.return_value = []

    with pytest.raises(DatabaseError, match="not found"):
        review_manager.add_review(999, 4)


def test_add_review_invalid_rating(review_manager):
    review_manager.query.return_value = [{"employee_id": 10}]

    with pytest.raises(DatabaseError):
        review_manager.add_review(123, 10)



def test_list_projects_with_status(monkeypatch):
    from managers import ProjectManager

    manager = ProjectManager()
    captured = {}

    def fake_query(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(manager, "query", fake_query)

    assert manager.list_projects(status="Active") == []
    assert "WHERE p.status = %s" in captured["sql"]
    assert captured["params"] == ["Active"]


def test_list_assignments_with_both_filters(monkeypatch):
    from managers import ProjectManager

    manager = ProjectManager()
    captured = {}

    def fake_query(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(manager, "query", fake_query)

    assert manager.list_assignments(
        project_id=10, employee_number=2001, limit=50
    ) == []

    assert "a.project_id = %s AND e.employee_number = %s" in captured["sql"]
    assert captured["params"] == [10, 2001, 50]


def test_list_reviews_with_employee_filter(monkeypatch):
    from managers import ReviewManager

    manager = ReviewManager()
    captured = {}

    def fake_query(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(manager, "query", fake_query)

    assert manager.list_reviews(employee_number=2001, limit=25) == []
    assert "WHERE e.employee_number = %s" in captured["sql"]
    assert captured["params"] == [2001, 25]

def test_attrition_risk_top_with_department(monkeypatch):
    from managers import AnalyticsManager

    manager = AnalyticsManager()
    captured = {}

    def fake_query_df(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(manager, "query_df", fake_query_df)

    assert manager.attrition_risk_top(limit=10, department="Sales") == []
    assert "WHERE department_name = %s" in captured["sql"]
    assert captured["params"] == ["Sales", 10]


def test_overallocated_employees_uses_limit(monkeypatch):
    from managers import AnalyticsManager

    manager = AnalyticsManager()
    captured = {}

    def fake_query_df(sql, params=None):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(manager, "query_df", fake_query_df)

    assert manager.overallocated_employees(limit=15) == []
    assert "HAVING SUM(fa.allocation_percentage) > 100" in captured["sql"]
    assert captured["params"] == [15]

def test_update_employee_without_existing_history(monkeypatch):
    from datetime import date
    from managers import EmployeeManager

    manager = EmployeeManager()

    class FakeCursor:
        def __init__(self):
            self.calls = []
            self.results = [
                {
                    "department_id": 1,
                    "job_role_id": 1,
                    "job_level": 2,
                    "monthly_income": 3000,
                    "education_field_id": 1,
                },
                None,  # No existing SCD history
                {"new_key": 99},
            ]

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

        def fetchone(self):
            return self.results.pop(0)

    cursor = FakeCursor()

    class FakeTransaction:
        def __enter__(self):
            return cursor

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(manager, "transaction", lambda: FakeTransaction())

    result = manager.update_employee(1001, job_level=3)

    assert result["changed"] is True
    assert result["new_employee_key"] == 99
    assert any(
        "INSERT INTO employee_scd_history" in sql
        for sql, _ in cursor.calls
    )


def test_update_employee_wraps_unexpected_error(monkeypatch):
    from managers import EmployeeManager, DatabaseError

    manager = EmployeeManager()

    class BrokenTransaction:
        def __enter__(self):
            raise RuntimeError("database unavailable")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        manager, "transaction", lambda: BrokenTransaction()
    )

    import pytest
    with pytest.raises(DatabaseError, match="Could not update employee"):
        manager.update_employee(1001, job_level=3)

def test_assign_employee_project_not_found(monkeypatch):
    import pytest
    from managers import ProjectManager, DatabaseError

    manager = ProjectManager()

    class FakeCursor:
        def __init__(self):
            self.calls = 0

        def execute(self, sql, params=None):
            self.calls += 1

        def fetchone(self):
            if self.calls == 1:
                return {"employee_id": 101}
            return None

    cursor = FakeCursor()

    class FakeTransaction:
        def __enter__(self):
            return cursor

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(manager, "transaction", lambda: FakeTransaction())

    with pytest.raises(DatabaseError, match="Project 10 not found"):
        manager.assign_employee(1001, 10, "2026-10-13", "Developer", 50)


def test_assign_employee_already_assigned(monkeypatch):
    import pytest
    from managers import ProjectManager, DatabaseError

    manager = ProjectManager()

    class FakeCursor:
        def __init__(self):
            self.calls = 0

        def execute(self, sql, params=None):
            self.calls += 1

        def fetchone(self):
            if self.calls == 1:
                return {"employee_id": 101}
            if self.calls == 2:
                return {"ok": 1}
            return {"ok": 1}

    cursor = FakeCursor()

    class FakeTransaction:
        def __enter__(self):
            return cursor

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(manager, "transaction", lambda: FakeTransaction())

    with pytest.raises(DatabaseError, match="already assigned"):
        manager.assign_employee(1001, 10, "2026-10-13", "Developer", 50)


def test_assign_employee_wraps_unexpected_error(monkeypatch):
    import pytest
    from managers import ProjectManager, DatabaseError

    manager = ProjectManager()

    class BrokenTransaction:
        def __enter__(self):
            raise RuntimeError("database unavailable")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(manager, "transaction", lambda: BrokenTransaction())

    with pytest.raises(DatabaseError, match="Could not assign employee"):
        manager.assign_employee(1001, 10, "2026-10-13", "Developer", 50)
