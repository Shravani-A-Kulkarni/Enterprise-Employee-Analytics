# """My Profile page: linked account shows its own record, unlinked account gets a clear message."""
# import runpy
# import sys
# from unittest.mock import MagicMock

# import pytest

# import ui_helpers


# class StopPage(Exception):
#     """Stands in for st.stop() so the page script ends where Streamlit would end it."""


# def _run_page(monkeypatch, user, employee):
#     fake_st = MagicMock()
#     fake_st.session_state = {"user": user}
#     fake_st.stop.side_effect = StopPage
#     fake_st.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
#     fake_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
#     monkeypatch.setitem(sys.modules, "streamlit", fake_st)
#     monkeypatch.setattr(ui_helpers, "st", fake_st)

#     employees = MagicMock()
#     employees.get_employee.return_value = employee
#     employees.get_dimension_history.return_value = []
#     projects, reviews = MagicMock(), MagicMock()
#     projects.list_assignments.return_value = []
#     reviews.list_reviews.return_value = []
#     monkeypatch.setattr(ui_helpers, "EmployeeManager", lambda: employees)
#     monkeypatch.setattr(ui_helpers, "ProjectManager", lambda: projects)
#     monkeypatch.setattr(ui_helpers, "ReviewManager", lambda: reviews)

#     try:
#         runpy.run_path("app/pages/5_My_Profile.py")
#     except StopPage:
#         pass
#     return fake_st, employees


# def _employee(number=1, email=None):
#     return {"employee_number": number, "first_name": "Ann", "last_name": "Lee", "email": email,
#             "job_level": 2, "monthly_income": 5000, "department_name": "Sales",
#             "job_role_name": "Rep", "education_field_name": "Marketing",
#             "total_working_years": 5, "years_at_company": 3}


# def _user(number, email="employee1@company.com"):
#     return {"user_id": 1, "email": email, "role": "Employee", "display_name": "X", "employee_number": number}


# def test_linked_account_loads_its_own_employee_record(monkeypatch):
#     st, employees = _run_page(monkeypatch, _user(1), _employee(1))
#     employees.get_employee.assert_called_once_with(1)
#     assert not any("not been linked" in str(c) for c in st.info.call_args_list)
#     st.warning.assert_not_called()
#     assert any("employee1@company.com" in str(c) for c in st.write.call_args_list)   # NULL employee email -> login email


# def test_employee_email_is_shown_when_the_record_has_one(monkeypatch):
#     st, _ = _run_page(monkeypatch, _user(100026, "jus@gmail.com"), _employee(100026, "jus@gmail.com"))
#     assert any("jus@gmail.com" in str(c) for c in st.write.call_args_list)


# def test_unlinked_account_sees_clear_message_and_no_lookup(monkeypatch):
#     st, employees = _run_page(monkeypatch, _user(None, "testemployee101@example.com"), None)
#     message = st.info.call_args[0][0]
#     assert "testemployee101@example.com" in message
#     assert "not been linked to an employee profile" in message
#     employees.get_employee.assert_not_called()
#     st.stop.assert_called_once()


# def test_linked_to_missing_employee_shows_warning(monkeypatch):
#     st, _ = _run_page(monkeypatch, _user(999999), None)
#     assert "999999" in st.warning.call_args[0][0]
#     assert not any("not been linked" in str(c) for c in st.info.call_args_list)
"""My Profile page, run for real with a fake database.

Covers: linked account, email match (Justin), unlinked account, profile details, reviews,
project assignments, career history, and attempts to see someone else's data.
"""
import runpy
import sys
from unittest.mock import MagicMock

import pandas as pd
import pytest

import auth
import ui_helpers


class StopPage(Exception):
    """Stands in for st.stop() so the script ends where Streamlit would end it."""


# employee_number -> the Employee row (what get_employee returns)
def _emp(number, first, last, email=None):
    return {"employee_number": number, "first_name": first, "last_name": last, "email": email,
            "age": 33, "gender": "Male", "marital_status": "Single", "education": 3,
            "education_field_name": "Marketing", "distance_from_home": 5, "department_name": "Sales",
            "job_role_name": "Sales Executive", "job_level": 2, "business_travel": "Travel_Rarely",
            "overtime": "No", "total_working_years": 8, "years_at_company": 3,
            "monthly_income": 6500, "performance_rating": 3, "attrition": "No", "stock_option_level": None}


EMPLOYEES = {1: _emp(1, "Ann", "Lee"), 2: _emp(2, "Bob", "Ray"),
             100026: _emp(100026, "Justin", "Drew", "jus@gmail.com")}
REVIEWS = {1: [{"review_id": 1, "employee_number": 1, "employee_name": "Ann Lee",
                "review_date": "2025-06-01", "review_period": "2025-H1", "rating": 4, "comments": "Great"}],
           2: [{"review_id": 2, "employee_number": 2, "employee_name": "Bob Ray",
                "review_date": "2025-06-02", "review_period": "2025-H1", "rating": 2, "comments": "SECRET-BOB"}],
           100026: []}
ASSIGNMENTS = {1: [{"assignment_id": 1, "employee_number": 1, "employee_name": "Ann Lee",
                    "project_name": "Apollo", "role": "Dev", "allocation_percentage": 50,
                    "assigned_date": "2025-01-01"}],
               2: [{"assignment_id": 2, "employee_number": 2, "employee_name": "Bob Ray",
                    "project_name": "SECRET-PROJECT", "role": "Lead", "allocation_percentage": 100,
                    "assigned_date": "2025-01-01"}],
               100026: []}
HISTORY = {1: [{"employee_key": 7, "department_name": "Sales", "job_role_name": "Sales Executive",
                "job_level": 2, "monthly_income": 6500, "effective_start_date": "2025-01-01",
                "effective_end_date": None, "is_current": 1}]}


def _run_page(monkeypatch, user, appuser_row="auto", employee_emails=None, claimed=(), query_params=None):
    """Run app/pages/5_My_Profile.py as `user`. Returns (fake_st, calls)."""
    calls = {"get_employee": [], "list_reviews": [], "list_assignments": [], "history": [], "writes": []}

    # --- fake Streamlit -------------------------------------------------------
    fake_st = MagicMock()
    fake_st.session_state = {"user": user}
    fake_st.query_params = query_params or {}
    fake_st.stop.side_effect = StopPage
    fake_st.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    fake_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setattr(ui_helpers, "st", fake_st)

    # --- fake AppUser / Employee lookups used by AuthManager ------------------
    if appuser_row == "auto":
        appuser_row = {"employee_number": user.get("employee_number"), "email": user["email"]}
    emails = employee_emails or {}

    def query(sql, params=()):
        if "FROM AppUser WHERE user_id" in sql:
            return [appuser_row] if appuser_row else []
        if "FROM Employee WHERE email" in sql:
            return [{"employee_number": emails[params[0]]}] if params[0] in emails else []
        if "FROM AppUser WHERE employee_number" in sql:
            return [{"1": 1}] if params[0] in claimed else []
        raise AssertionError(f"unexpected query: {sql}")

    # AuthManager is a Singleton: patch the one shared instance the page will get back
    manager = auth.AuthManager()
    monkeypatch.setattr(manager, "query", query)
    monkeypatch.setattr(manager, "execute", lambda *a: calls["writes"].append(a))

    # --- fake data managers ---------------------------------------------------
    class Employees:
        def get_employee(self, n):
            calls["get_employee"].append(n)
            return EMPLOYEES.get(n)

        def get_dimension_history(self, n):
            calls["history"].append(n)
            return HISTORY.get(n, [])

    class Projects:
        def list_assignments(self, project_id=None, limit=200, employee_number=None):
            calls["list_assignments"].append(employee_number)
            return ASSIGNMENTS.get(employee_number, [])

    class Reviews:
        def list_reviews(self, employee_number=None, limit=100):
            calls["list_reviews"].append(employee_number)
            return REVIEWS.get(employee_number, [])

    monkeypatch.setattr(ui_helpers, "EmployeeManager", Employees)
    monkeypatch.setattr(ui_helpers, "ProjectManager", Projects)
    monkeypatch.setattr(ui_helpers, "ReviewManager", Reviews)

    try:
        runpy.run_path("app/pages/5_My_Profile.py")
    except StopPage:
        pass
    return fake_st, calls


def _user(number, email="employee1@company.com", role="Employee", user_id=1):
    return {"user_id": user_id, "email": email, "role": role, "display_name": "X", "employee_number": number}


def _tables(st):
    """Every DataFrame the page displayed."""
    return [c[0][0] for c in st.dataframe.call_args_list if isinstance(c[0][0], pd.DataFrame)]


def _text(st):
    return " ".join(str(c) for c in st.method_calls)


def _nothing_looked_up(calls):
    return not (calls["get_employee"] or calls["list_reviews"] or calls["list_assignments"] or calls["history"])


# ------------------------------------------------------------------ linked account
def test_linked_account_shows_its_own_profile(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1))
    assert calls["get_employee"] == [1]
    assert not any("not been linked" in str(c) for c in st.info.call_args_list)
    assert "employee1@company.com" in _text(st)           # employee email is NULL -> login email shown
    assert calls["writes"] == []                           # the page never writes to the database


def test_profile_details_show_all_available_information(monkeypatch):
    st, _ = _run_page(monkeypatch, _user(1))
    details = next(t for t in _tables(st) if list(t.columns) == ["Detail", "Value"])
    shown = dict(zip(details["Detail"], details["Value"]))
    assert shown["Department"] == "Sales" and shown["Job role"] == "Sales Executive"
    assert shown["Job level"] == "2" and shown["Monthly income"] == "6500"
    assert shown["Age"] == "33" and shown["Years at company"] == "3" and shown["Attrition"] == "No"
    assert "Stock option level" not in shown               # empty values are skipped


def test_review_history_has_dates_periods_ratings_and_comments(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1))
    assert calls["list_reviews"] == [1]
    table = next(t for t in _tables(st) if "rating" in t.columns)
    assert list(table.columns) == ["review_date", "review_period", "rating", "comments"]
    assert table.iloc[0].tolist() == ["2025-06-01", "2025-H1", 4, "Great"]


def test_project_assignments_are_shown(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1))
    assert calls["list_assignments"] == [1]
    table = next(t for t in _tables(st) if "project_name" in t.columns)
    assert table["project_name"].tolist() == ["Apollo"]
    assert "employee_number" not in table.columns


def test_career_history_is_shown(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1))
    assert calls["history"] == [1]
    table = next(t for t in _tables(st) if "is_current" in t.columns)
    assert table["monthly_income"].tolist() == [6500]
    assert "employee_key" not in table.columns


# ------------------------------------------------------------------ Justin: email match
def test_unlinked_account_with_exact_email_match_loads_that_employee(monkeypatch):
    user = _user(None, "jus@gmail.com", user_id=9)
    st, calls = _run_page(monkeypatch, user, employee_emails={"jus@gmail.com": 100026})
    assert calls["get_employee"] == [100026]
    assert calls["list_reviews"] == [100026] and calls["list_assignments"] == [100026]
    assert "Justin" in _text(st) and "Drew" in _text(st)
    assert "matching your login email" in _text(st)         # tells the user how it was found
    assert calls["writes"] == []                            # no automatic data change


def test_email_match_is_not_used_when_employee_already_linked_to_another_login(monkeypatch):
    user = _user(None, "jus@gmail.com", user_id=9)
    st, calls = _run_page(monkeypatch, user, employee_emails={"jus@gmail.com": 100026}, claimed=[100026])
    assert _nothing_looked_up(calls)
    assert "not been linked" in st.info.call_args[0][0]


# ------------------------------------------------------------------ unlinked account
def test_unlinked_account_gets_clear_message_and_no_data(monkeypatch):
    user = _user(None, "testemployee101@example.com", user_id=8)
    st, calls = _run_page(monkeypatch, user, employee_emails={"jus@gmail.com": 100026})
    message = st.info.call_args[0][0]
    assert "testemployee101@example.com" in message
    assert "not been linked to an employee profile" in message
    assert _nothing_looked_up(calls)                        # no fallback to anyone else's data
    st.stop.assert_called_once()


def test_linked_to_missing_employee_shows_warning_only(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(999999))
    assert "999999" in st.warning.call_args[0][0]
    assert calls["list_reviews"] == [] and calls["list_assignments"] == [] and calls["history"] == []


# ------------------------------------------------------------------ unauthorized access
def test_url_parameters_cannot_select_another_employee(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1), query_params={"employee_number": "2", "employee": "2"})
    assert calls["get_employee"] == [1]
    assert calls["list_reviews"] == [1] and calls["list_assignments"] == [1] and calls["history"] == [1]
    assert "SECRET-BOB" not in _text(st) and "SECRET-PROJECT" not in _text(st)
    assert not any(t.astype(str).apply(lambda col: col.str.contains("SECRET")).any().any() for t in _tables(st))


def test_identity_comes_from_the_database_not_from_a_changed_session_value(monkeypatch):
    # session claims employee 2, but the AppUser row says this login belongs to employee 1
    user = _user(2)
    st, calls = _run_page(monkeypatch, user, appuser_row={"employee_number": 1, "email": user["email"]})
    assert calls["get_employee"] == [1]
    assert calls["list_reviews"] == [1] and calls["list_assignments"] == [1]


def test_deactivated_or_deleted_account_sees_nothing(monkeypatch):
    st, calls = _run_page(monkeypatch, _user(1), appuser_row=None)
    assert _nothing_looked_up(calls)
    assert "not been linked" in st.info.call_args[0][0]


@pytest.mark.parametrize("role", ["HR", "Manager"])
def test_hr_and_manager_logins_never_get_a_personal_profile(monkeypatch, role):
    st, calls = _run_page(monkeypatch, _user(1, "hr@company.com", role=role))
    assert _nothing_looked_up(calls)
