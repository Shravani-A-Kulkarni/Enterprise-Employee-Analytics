"""Manager Employee Directory: query safety, page behaviour, role access, project assignment."""
import runpy
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock

import pytest

import auth
import ui_helpers
from managers import DatabaseError, EmployeeManager, ProjectManager

SENSITIVE = ("monthly_income", "age", "gender", "marital_status", "attrition",
             "performance_rating", "distance_from_home")

TOM = {"employee_number": 1471, "first_name": "Tom", "last_name": "Hardy", "email": "tom@gmail.com",
       "department_name": "Research & Development", "job_role_name": "Research Scientist",
       "job_level": 1, "employment_status": "Active"}
ANA = {"employee_number": 12, "first_name": "Ana", "last_name": "Lopez", "email": "ana@company.com",
       "department_name": "Sales", "job_role_name": "Sales Executive", "job_level": 3,
       "employment_status": "Active"}


class StopPage(Exception):
    """Stands in for st.stop()."""


# ----------------------------------------------------------------------------- manager SQL
@pytest.fixture
def em():
    manager = object.__new__(EmployeeManager)
    manager.query = Mock(return_value=[TOM])
    return manager


def test_directory_returns_rows_from_the_database(em):
    assert em.list_directory() == [TOM]
    em.query.assert_called_once()


def test_directory_query_has_basic_columns_and_no_sensitive_ones(em):
    em.list_directory()
    sql = em.query.call_args.args[0]
    for col in ("employee_number", "first_name", "last_name", "email", "department_name",
                "job_role_name", "job_level", "employment_status"):
        assert col in sql
    for col in SENSITIVE:
        assert col not in sql.replace("e.attrition = 'Yes'", "")   # status is derived, raw flag not returned
    assert "SELECT e.*" not in sql


def test_directory_is_read_only(em):
    em.execute = Mock()
    em.list_directory("tom")
    em.execute.assert_not_called()


def test_search_by_number_matches_exactly_and_email_is_searched(em):
    em.list_directory("1471")
    sql, params = em.query.call_args.args
    assert "e.employee_number = %s" in sql and "e.email LIKE %s" in sql
    assert 1471 in params


def test_search_by_name_or_email_is_parameterised_contains(em):
    em.list_directory("tom@gmail")
    sql, params = em.query.call_args.args
    assert "tom@gmail" not in sql                # never concatenated into the SQL
    assert params[:4] == ["%tom@gmail%"] * 4
    assert "employee_number = %s" not in sql     # not a pure number


def test_search_escapes_like_wildcards_and_injection(em):
    em.list_directory("a%_'; DROP TABLE Employee;--")
    sql, params = em.query.call_args.args
    assert "DROP" not in sql
    assert params[0].startswith("%a\\%\\_")


def test_department_filter(em):
    em.list_directory(department_id=3)
    sql, params = em.query.call_args.args
    assert "e.department_id = %s" in sql and 3 in params


def test_blank_search_adds_no_filter(em):
    em.list_directory("   ")
    sql, _ = em.query.call_args.args
    assert "LIKE" not in sql


def test_newly_onboarded_employee_appears_without_hardcoding():
    """An in-memory table shared by 'onboarding' and the directory: Tom shows up once added."""
    table = [dict(ANA)]
    manager = object.__new__(EmployeeManager)

    def fake_query(sql, params=()):
        like = [p for p in params if isinstance(p, str)]
        needle = like[0].strip("%").lower() if like else ""
        return [r for r in table if not needle or needle in (r["first_name"] + " " + r["last_name"] + r["email"]).lower()]

    manager.query = fake_query
    assert [r["first_name"] for r in manager.list_directory()] == ["Ana"]
    table.append(dict(TOM))                              # HR onboards Tom
    assert "Tom" in [r["first_name"] for r in manager.list_directory()]
    assert [r["email"] for r in manager.list_directory("tom")] == ["tom@gmail.com"]


# ----------------------------------------------------------------------------- assignment
def _pm(monkeypatch, employee_row, project_row=({"ok": 1})):
    manager = object.__new__(ProjectManager)
    cur = MagicMock()
    cur.fetchone.side_effect = [employee_row, project_row, None, {"total": 50}] if employee_row else [None]
    cur.lastrowid = 99

    @contextmanager
    def tx():
        yield cur

    manager.transaction = tx
    return manager, cur


def test_manager_can_assign_project_to_selected_employee(monkeypatch):
    pm, cur = _pm(monkeypatch, {"employee_id": 7})
    result = pm.assign_employee(1471, 5, "2026-10-14", "Developer", 50)
    assert result == {"assignment_id": 99, "total_allocation": 50}
    assert any("INSERT INTO Assignment" in c.args[0] for c in cur.execute.call_args_list)


def test_nonexistent_employee_is_rejected_and_nothing_inserted(monkeypatch):
    pm, cur = _pm(monkeypatch, None)
    with pytest.raises(DatabaseError, match="not found"):
        pm.assign_employee(999999, 5, "2026-10-14", "Developer", 50)
    assert not any("INSERT" in c.args[0] for c in cur.execute.call_args_list)


@pytest.mark.parametrize("bad", [0, -4, "abc", "", None, "1; DROP TABLE Employee", 3.5 - 4])
def test_invalid_employee_ids_rejected_before_touching_the_database(bad):
    pm = object.__new__(ProjectManager)
    pm.transaction = Mock(side_effect=AssertionError("DB must not be used"))
    with pytest.raises(DatabaseError, match="Employee number"):
        pm.assign_employee(bad, 5, "2026-10-14", "Developer", 50)


# ----------------------------------------------------------------------------- access control
def test_manager_sees_directory_but_not_onboarding():
    assert "Employee Directory" in auth.PAGE_ACCESS["Manager"]
    assert "Onboarding" not in auth.PAGE_ACCESS["Manager"]
    assert "Employee Directory" not in auth.PAGE_ACCESS["Employee"]


def test_router_registers_directory_page_for_manager(monkeypatch):
    import streamlit as st
    titles = []
    monkeypatch.setattr(st, "session_state", {"user": {"email": "m@c.com", "role": "Manager",
                                                       "display_name": "M", "employee_number": None}})
    monkeypatch.setattr(st, "Page", lambda path, **kw: titles.append(kw.get("title")) or MagicMock())
    nav = MagicMock()
    navigation = MagicMock(return_value=nav)
    monkeypatch.setattr(st, "navigation", navigation)
    monkeypatch.setattr(st, "set_page_config", MagicMock())
    runpy.run_path("app/streamlit_app.py")
    shown = navigation.call_args.args[0]
    assert len(shown) == len(auth.PAGE_ACCESS["Manager"])
    assert "Employee Directory" in titles


def _fake_streamlit(monkeypatch, user, term="", dept="All"):
    fake = MagicMock()
    fake.session_state = {"user": user} if user else {}
    fake.stop.side_effect = StopPage
    c1, c2 = MagicMock(), MagicMock()
    c1.text_input.return_value = term
    c2.selectbox.return_value = dept
    fake.columns.side_effect = lambda spec: [c1, c2]
    fake.selectbox.side_effect = lambda label, options, **kw: list(options)[0]
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    monkeypatch.setattr(ui_helpers, "st", fake)
    return fake


def _run_directory(monkeypatch, user, rows, term="", dept="All"):
    fake = _fake_streamlit(monkeypatch, user, term, dept)
    seen = {}

    class Employees:
        def get_departments(self):
            return [{"department_id": 1, "department_name": "Sales"},
                    {"department_id": 2, "department_name": "Research & Development"}]

        def get_job_roles(self):
            return []

        def get_education_fields(self):
            return []

        def list_directory(self, term=None, department_id=None, limit=200):
            seen.update(term=term, department_id=department_id)
            return [r for r in rows if (not department_id or r["department_name"] == {1: "Sales", 2: "Research & Development"}[department_id])]

    monkeypatch.setattr(ui_helpers, "EmployeeManager", Employees)
    monkeypatch.setattr(ui_helpers, "lookup_options", lambda: ({"Sales": 1, "Research & Development": 2}, {}, {}))
    try:
        runpy.run_path("app/pages/6_Employee_Directory.py")
    except StopPage:
        pass
    return fake, seen


def _frames(fake):
    return [c.args[0] for c in fake.dataframe.call_args_list]


MANAGER = {"user_id": 1, "email": "m@c.com", "role": "Manager", "display_name": "Mia", "employee_number": None}


def test_manager_can_view_directory_with_ids_and_basic_details(monkeypatch):
    fake, _ = _run_directory(monkeypatch, MANAGER, [TOM, ANA])
    df = _frames(fake)[0]
    assert list(df.columns) == ["Employee ID", "First name", "Last name", "Email", "Department",
                                "Job role", "Job level", "Status"]
    assert 1471 in set(df["Employee ID"]) and "tom@gmail.com" in set(df["Email"])
    fake.error.assert_not_called()


def test_directory_page_shows_newly_onboarded_tom(monkeypatch):
    fake, _ = _run_directory(monkeypatch, MANAGER, [TOM])
    assert list(_frames(fake)[0]["First name"]) == ["Tom"]


def test_directory_page_passes_search_and_department_to_the_query(monkeypatch):
    fake, seen = _run_directory(monkeypatch, MANAGER, [TOM, ANA], term="ana", dept="Sales")
    assert seen == {"term": "ana", "department_id": 1}
    assert list(_frames(fake)[0]["First name"]) == ["Ana"]


def test_directory_page_has_copyable_id(monkeypatch):
    fake, _ = _run_directory(monkeypatch, MANAGER, [TOM])
    fake.code.assert_called_once_with("1471", language=None)


def test_directory_page_no_results_message(monkeypatch):
    fake, _ = _run_directory(monkeypatch, MANAGER, [], term="nobody")
    fake.info.assert_called_once()
    fake.dataframe.assert_not_called()


@pytest.mark.parametrize("role", ["Employee", "Intern", None])
def test_directory_page_denied_to_other_roles(monkeypatch, role):
    user = {"user_id": 2, "email": "e@c.com", "role": role, "display_name": "E", "employee_number": 5}
    fake, seen = _run_directory(monkeypatch, user, [TOM])
    fake.error.assert_called_once()
    fake.dataframe.assert_not_called()
    assert seen == {}                        # data was never queried


def test_directory_page_requires_login(monkeypatch):
    fake, seen = _run_directory(monkeypatch, None, [TOM])
    fake.warning.assert_called_once()
    assert seen == {}


def test_manager_cannot_use_hr_onboarding_page(monkeypatch):
    fake = _fake_streamlit(monkeypatch, MANAGER)
    em = MagicMock()
    monkeypatch.setattr(ui_helpers, "EmployeeManager", lambda: em)
    with pytest.raises(StopPage):
        runpy.run_path("app/pages/1_Onboarding.py")
    fake.error.assert_called_once()
    em.add_employee.assert_not_called()
    em.update_employee.assert_not_called()
    em.delete_employee.assert_not_called()


def test_hr_can_still_open_onboarding(monkeypatch):
    hr = {"user_id": 3, "email": "hr@c.com", "role": "HR", "display_name": "H", "employee_number": None}
    fake = _fake_streamlit(monkeypatch, hr)
    fake.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    fake.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
    fake.form_submit_button.return_value = False
    fake.number_input.return_value = 1
    em = MagicMock()
    em.get_employee.return_value = None
    monkeypatch.setattr(ui_helpers, "EmployeeManager", lambda: em)
    monkeypatch.setattr(ui_helpers, "lookup_options", lambda: ({"Sales": 1}, {"Role": 1}, {"Field": 1}))
    runpy.run_path("app/pages/1_Onboarding.py")
    fake.error.assert_not_called()


# ----------------------------------------------------------------------------- Projects page
def _run_projects(monkeypatch, picked_employee, rows=(TOM, ANA), assign_error=None):
    fake = _fake_streamlit(monkeypatch, MANAGER)
    fake.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    fake.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
    fake.text_input.return_value = ""
    fake.slider.return_value = 50
    fake.form_submit_button.side_effect = lambda label, **kw: label == "Assign"
    fake.selectbox.side_effect = lambda label, options, **kw: (
        picked_employee if label == "Employee" and picked_employee else list(options)[0] if list(options) else None)
    calls = {}

    class Employees:
        def get_departments(self):
            return [{"department_id": 1, "department_name": "Sales"}]

        def get_job_roles(self):
            return []

        def get_education_fields(self):
            return []

        def list_directory(self, term=None, department_id=None, limit=200):
            calls["limit"] = limit
            return list(rows)

    class Projects:
        def list_projects(self, status=None):
            return [{"project_id": 5, "project_name": "Apollo", "status": "Active", "department_name": "Sales",
                     "start_date": None, "end_date": None, "team_size": 0}]

        def list_assignments(self, *a, **k):
            return []

        def assign_employee(self, number, project_id, assigned, role, allocation):
            calls["assign"] = (number, project_id)
            if assign_error:
                raise DatabaseError(assign_error)
            return {"assignment_id": 77, "total_allocation": 50}

    monkeypatch.setattr(ui_helpers, "EmployeeManager", Employees)
    monkeypatch.setattr(ui_helpers, "ProjectManager", Projects)
    monkeypatch.setattr(ui_helpers, "lookup_options", lambda: ({"Sales": 1}, {}, {}))
    runpy.run_path("app/pages/2_Projects.py")
    return fake, calls


def test_projects_page_assigns_the_employee_picked_from_the_dropdown(monkeypatch):
    fake, calls = _run_projects(monkeypatch, "Tom Hardy - ID 1471")
    assert calls["assign"] == (1471, 5)
    fake.success.assert_called()
    assert "Tom Hardy" in fake.success.call_args.args[0]
    fake.number_input.assert_not_called()          # no manual ID typing any more


def test_projects_page_shows_clear_error_for_rejected_employee(monkeypatch):
    fake, calls = _run_projects(monkeypatch, "Tom Hardy - ID 1471", assign_error="Employee 1471 not found")
    fake.error.assert_called_once_with("Employee 1471 not found")


def test_projects_page_with_no_employees_does_not_assign(monkeypatch):
    fake, calls = _run_projects(monkeypatch, None, rows=())
    assert "assign" not in calls
    fake.error.assert_called()
