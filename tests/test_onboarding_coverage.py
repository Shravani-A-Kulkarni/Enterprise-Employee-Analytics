
import runpy
from unittest.mock import MagicMock, patch

import streamlit as st


LOOKUPS = (
    {"HR": 1, "IT": 2},
    {"Developer": 1, "Manager": 2},
    {"Other": 1, "Computer Science": 2},
)

EMPLOYEE = {
    "first_name": "Test",
    "last_name": "Employee",
    "department_name": "HR",
    "job_role_name": "Developer",
    "job_level": 1,
    "monthly_income": 5000,
}


def run_onboarding_page(
    manager,
    submissions=(False, False),
    delete_clicked=False,
    number_inputs=(42, 5000),
    slider_value=1,
    employee_class_patch=None,
):
    columns_3 = [MagicMock() for _ in range(3)]
    columns_2 = [MagicMock() for _ in range(2)]

    for col in columns_3 + columns_2:
        def text_input(label, **kwargs):
            return {
                "First name": "Test",
                "Last name": "Employee",
                "Email": "test@example.com",
                "Search by name or employee number": "",
            }.get(label, "")

        col.text_input.side_effect = text_input
        col.selectbox.side_effect = (
            lambda label, options, **kwargs:
            options[kwargs.get("index", 0)]
        )
        col.number_input.side_effect = lambda *args, **kwargs: 5000
        col.slider.return_value = slider_value
        col.radio.return_value = "No"

    tabs = [MagicMock() for _ in range(3)]
    for tab in tabs:
        tab.__enter__.return_value = tab

    form = MagicMock()
    form.__enter__.return_value = form

    def fake_columns(spec, *args, **kwargs):
        return columns_2 if spec == [2, 1] else columns_3

    number_values = iter(number_inputs)
    submission_values = iter(submissions)

    show_error_mock = MagicMock()
    warning_mock = MagicMock()

    # Patch dependencies before executing the page so its direct imports
    # receive the correct mocks.
    patches = [
        patch("ui_helpers.require_roles"),
        patch("ui_helpers.page_setup"),
        patch("ui_helpers.safe_lookup_options", return_value=LOOKUPS),
        patch("ui_helpers.EmployeeManager", return_value=manager),
        patch("ui_helpers.clear_dashboard_cache"),
        patch("ui_helpers.show_error", new=show_error_mock),
        patch.object(st, "tabs", return_value=tabs),
        patch.object(st, "form", return_value=form),
        patch.object(st, "columns", side_effect=fake_columns),
        patch.object(
            st,
            "number_input",
            side_effect=lambda *args, **kwargs: next(number_values),
        ),
        patch.object(
            st,
            "selectbox",
            side_effect=lambda label, options, **kwargs:
                options[kwargs.get("index", 0)],
        ),
        patch.object(st, "expander", return_value=form),
        patch.object(
            st,
            "form_submit_button",
            side_effect=lambda *args, **kwargs: next(submission_values),
        ),
        patch.object(st, "button", return_value=delete_clicked),
        patch.object(st, "dataframe"),
        patch.object(st, "write"),
        patch.object(st, "info"),
        patch.object(st, "success"),
        patch.object(st, "warning", new=warning_mock),
        patch.object(st, "caption"),
        patch.object(st, "markdown"),
    ]

    active_patches = []
    try:
        for patcher in patches:
            active_patches.append(patcher)
            patcher.start()

        if employee_class_patch is not None:
            employee_class_patch.start()
            active_patches.append(employee_class_patch)

        runpy.run_path("app/pages/1_Onboarding.py")
    finally:
        for patcher in reversed(active_patches):
            patcher.stop()

    return show_error_mock, warning_mock


def test_onboarding_page_loads():
    manager = MagicMock()
    manager.get_employee.return_value = None
    manager.search_employees.return_value = []

    run_onboarding_page(manager)

    manager.get_employee.assert_called_once_with(42)
    manager.search_employees.assert_called_once_with(None, None)


def test_onboarding_success():
    manager = MagicMock()
    manager.get_employee.return_value = None
    manager.search_employees.return_value = []
    manager.add_employee.return_value = {"employee_number": 101}

    employee_class = patch("entities.Employee")
    employee_mock = employee_class.new if employee_class.new is not None else None

    with patch("entities.Employee") as employee:
        employee.return_value.full_name.return_value = "Test Employee"
        run_onboarding_page(
            manager,
            submissions=(True, False),
        )
        manager.add_employee.assert_called_once_with(employee.return_value)


def test_onboarding_validation_error():
    manager = MagicMock()
    manager.get_employee.return_value = None
    manager.search_employees.return_value = []

    with patch("entities.Employee", side_effect=ValueError("Invalid employee")):
        _, warning = run_onboarding_page(
            manager,
            submissions=(True, False),
        )

    warning.assert_called_once_with("Invalid employee")


def test_onboarding_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.get_employee.return_value = None
    manager.search_employees.return_value = []
    manager.add_employee.side_effect = DatabaseError("Insert failed")

    with patch("entities.Employee"):
        show_error, _ = run_onboarding_page(
            manager,
            submissions=(True, False),
        )

    show_error.assert_called_once()


def test_update_employee_changed():
    manager = MagicMock()
    manager.get_employee.return_value = EMPLOYEE
    manager.update_employee.return_value = {
        "changed": True,
        "new_employee_key": 501,
        "effective_date": "2026-10-15",
    }
    manager.get_dimension_history.return_value = []
    manager.search_employees.return_value = []

    run_onboarding_page(
        manager,
        submissions=(False, True),
        number_inputs=(42, 5000),
        slider_value=1,
    )

    manager.update_employee.assert_called_once_with(42, 1, 1, 1, 5000)
    manager.get_dimension_history.assert_called_once_with(42)


def test_update_employee_unchanged():
    manager = MagicMock()
    manager.get_employee.return_value = EMPLOYEE
    manager.update_employee.return_value = {"changed": False}
    manager.get_dimension_history.return_value = []
    manager.search_employees.return_value = []

    run_onboarding_page(
        manager,
        submissions=(False, True),
        number_inputs=(42, 5000),
        slider_value=1,
    )

    manager.update_employee.assert_called_once()
    manager.delete_employee.assert_not_called()


def test_update_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.get_employee.return_value = EMPLOYEE
    manager.update_employee.side_effect = DatabaseError("Update failed")
    manager.get_dimension_history.side_effect = DatabaseError("History failed")
    manager.search_employees.return_value = []

    show_error, _ = run_onboarding_page(
        manager,
        submissions=(False, True),
        number_inputs=(42, 5000),
    )

    assert show_error.call_count == 2


def test_employee_lookup_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.get_employee.side_effect = DatabaseError("Lookup failed")
    manager.search_employees.return_value = []

    show_error, _ = run_onboarding_page(manager)

    show_error.assert_called_once()


def test_delete_employee_success():
    manager = MagicMock()
    manager.get_employee.return_value = EMPLOYEE
    manager.get_dimension_history.return_value = []
    manager.search_employees.return_value = []

    run_onboarding_page(manager, delete_clicked=True)

    manager.delete_employee.assert_called_once_with(42)


def test_delete_employee_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.get_employee.return_value = EMPLOYEE
    manager.get_dimension_history.return_value = []
    manager.delete_employee.side_effect = DatabaseError("Delete failed")
    manager.search_employees.return_value = []

    show_error, _ = run_onboarding_page(manager, delete_clicked=True)

    show_error.assert_called_once()


def test_directory_search_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.get_employee.return_value = None
    manager.search_employees.side_effect = DatabaseError("Search failed")

    show_error, _ = run_onboarding_page(manager)

    show_error.assert_called_once()
