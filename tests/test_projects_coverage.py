from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import streamlit as st


PROJECTS = [{"project_id": 1, "project_name": "Analytics", "status": "Active"}]
EMPLOYEES = [{
    "employee_number": 10,
    "first_name": "Test",
    "last_name": "Employee",
    "email": "test@example.com",
}]
LOOKUPS = ({"HR": 1}, {"Developer": 1}, {"Other": 1})


def run_projects_page(
    manager,
    employee_manager=None,
    *,
    submissions=(False, False),
    has_end=False,
    show_team=False,
    project_side_effect=None,
    project_instance=None,
):
    """Execute the Projects page with its external dependencies mocked."""
    if employee_manager is None:
        employee_manager = MagicMock()
        employee_manager.list_directory.return_value = EMPLOYEES

    columns_2 = [MagicMock() for _ in range(2)]
    columns_3 = [MagicMock() for _ in range(3)]
    for col in columns_2 + columns_3:
        col.selectbox.side_effect = (
            lambda label, options, **kwargs:
            options[kwargs.get("index", 0)] if options else None
        )
        col.text_input.side_effect = (
            lambda label, value="", **kwargs:
            "Developer" if label == "Role on project" else value
        )
        col.date_input.return_value = __import__("datetime").date.today()
        col.slider.return_value = 50
        col.checkbox.return_value = has_end

    tabs = [MagicMock() for _ in range(3)]
    for tab in tabs:
        tab.__enter__.return_value = tab
    form = MagicMock()
    form.__enter__.return_value = form

    def fake_columns(spec, *args, **kwargs):
        return columns_3 if spec == 3 else columns_2

    def selectbox_value(label, options, **kwargs):
        if not options:
            return None
        if label == "Show team of project" and show_team and len(options) > 1:
            return options[1]
        return options[0]

    submission_values = iter(submissions)
    show_error_mock = MagicMock()
    warning_mock = MagicMock()

    project_kwargs = {}
    if project_side_effect is not None:
        project_kwargs["side_effect"] = project_side_effect
    elif project_instance is not None:
        project_kwargs["return_value"] = project_instance
    else:
        project_kwargs["return_value"] = MagicMock()

    with ExitStack() as stack:
        stack.enter_context(patch("ui_helpers.page_setup"))
        stack.enter_context(patch("ui_helpers.safe_lookup_options", return_value=LOOKUPS))
        stack.enter_context(patch("ui_helpers.ProjectManager", return_value=manager))
        stack.enter_context(patch("ui_helpers.EmployeeManager", return_value=employee_manager))
        stack.enter_context(patch("ui_helpers.clear_dashboard_cache"))
        stack.enter_context(patch("ui_helpers.show_error", new=show_error_mock))
        stack.enter_context(patch.object(st, "tabs", return_value=tabs))
        stack.enter_context(patch.object(st, "form", return_value=form))
        stack.enter_context(patch.object(st, "columns", side_effect=fake_columns))
        stack.enter_context(patch.object(
            st, "text_input",
            side_effect=lambda label, **kwargs: {
                "Project name": "Analytics",
                "Find employee (ID, name or email)": "",
            }.get(label, ""),
        ))
        stack.enter_context(patch.object(st, "selectbox", side_effect=selectbox_value))
        stack.enter_context(patch.object(
            st, "form_submit_button",
            side_effect=lambda *args, **kwargs: next(submission_values),
        ))
        stack.enter_context(patch.object(st, "dataframe"))
        stack.enter_context(patch.object(st, "success"))
        stack.enter_context(patch.object(st, "warning", new=warning_mock))
        stack.enter_context(patch.object(st, "info"))
        stack.enter_context(patch.object(st, "write"))
        stack.enter_context(patch("entities.Project", **project_kwargs))

        import runpy
        runpy.run_path("app/pages/2_Projects.py")

    return show_error_mock, warning_mock


def test_projects_page_loads():
    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.list_assignments.return_value = []
    manager.create_project.return_value = 1

    run_projects_page(manager)

    manager.list_projects.assert_called()


def test_create_project_success():
    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.create_project.return_value = 123
    project_instance = MagicMock()
    project_instance.project_name = "Analytics"

    run_projects_page(
        manager, submissions=(True, False), project_instance=project_instance
    )

    manager.create_project.assert_called_once_with(project_instance)


def test_create_project_validation_error():
    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS

    _, warning = run_projects_page(
        manager,
        submissions=(True, False),
        project_side_effect=ValueError("Invalid project"),
    )

    warning.assert_called_once_with("Invalid project")


def test_create_project_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.create_project.side_effect = DatabaseError("Create failed")

    show_error, _ = run_projects_page(manager, submissions=(True, False))

    show_error.assert_called_once()


def test_assign_employee_success_and_overallocation():
    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.assign_employee.return_value = {
        "assignment_id": 99, "total_allocation": 120
    }

    _, warning = run_projects_page(manager, submissions=(False, True))

    manager.assign_employee.assert_called_once()
    warning.assert_called_once()


def test_assign_employee_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.assign_employee.side_effect = DatabaseError("Assignment failed")

    show_error, _ = run_projects_page(manager, submissions=(False, True))

    show_error.assert_called_once()


def test_list_project_team():
    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    manager.list_assignments.return_value = [{"employee_number": 10}]

    run_projects_page(manager, show_team=True)

    manager.list_assignments.assert_called_once_with(1)


def test_list_projects_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.list_projects.side_effect = [
        DatabaseError("Project lookup failed"), PROJECTS
    ]

    show_error, _ = run_projects_page(manager)

    show_error.assert_called_once()


def test_employee_directory_database_error():
    from ui_helpers import DatabaseError

    manager = MagicMock()
    manager.list_projects.return_value = PROJECTS
    employee_manager = MagicMock()
    employee_manager.list_directory.side_effect = DatabaseError("Directory failed")

    show_error, _ = run_projects_page(manager, employee_manager)

    show_error.assert_called_once()
