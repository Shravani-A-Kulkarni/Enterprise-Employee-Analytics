import pytest
from unittest.mock import MagicMock

import ui_helpers


def test_current_user_returns_signed_in_user(monkeypatch):
    user = {"email": "hr@company.com", "role": "HR"}
    monkeypatch.setattr(ui_helpers.st, "session_state", {"user": user})

    assert ui_helpers.current_user() == user


def test_current_user_without_login_stops(monkeypatch):
    monkeypatch.setattr(ui_helpers.st, "session_state", {})
    monkeypatch.setattr(ui_helpers.st, "warning", MagicMock())
    monkeypatch.setattr(ui_helpers.st, "stop", MagicMock(side_effect=RuntimeError))

    with pytest.raises(RuntimeError):
        ui_helpers.current_user()


def test_show_error(monkeypatch):
    error = MagicMock()
    monkeypatch.setattr(ui_helpers.st, "error", error)

    ui_helpers.show_error(ValueError("Test error"))

    error.assert_called_once_with("Test error")


def test_page_setup(monkeypatch):
    config = MagicMock()
    title = MagicMock()
    monkeypatch.setattr(ui_helpers.st, "set_page_config", config)
    monkeypatch.setattr(ui_helpers.st, "title", title)

    ui_helpers.page_setup("Test", "ðŸ¢")

    config.assert_called_once()
    title.assert_called_once_with("ðŸ¢ Test")


def test_page_setup_survives_config_error(monkeypatch):
    monkeypatch.setattr(
        ui_helpers.st, "set_page_config",
        MagicMock(side_effect=RuntimeError("Already configured"))
    )
    title = MagicMock()
    monkeypatch.setattr(ui_helpers.st, "title", title)

    ui_helpers.page_setup("Test", "ðŸ¢")

    title.assert_called_once_with("ðŸ¢ Test")


def test_clear_dashboard_cache(monkeypatch):
    clear = MagicMock()
    monkeypatch.setattr(ui_helpers.st.cache_data, "clear", clear)

    ui_helpers.clear_dashboard_cache()

    clear.assert_called_once()

def test_lookup_options_returns_dropdown_mappings(monkeypatch):
    class FakeEmployeeManager:
        def get_departments(self):
            return [{"department_name": "HR", "department_id": 1}]

        def get_job_roles(self):
            return [{"job_role_name": "Engineer", "job_role_id": 2}]

        def get_education_fields(self):
            return [{"education_field_name": "Computer Science",
                     "education_field_id": 3}]

    monkeypatch.setattr(
        ui_helpers, "EmployeeManager", FakeEmployeeManager
    )

    departments, job_roles, education_fields = ui_helpers.lookup_options.__wrapped__()

    assert departments == {"HR": 1}
    assert job_roles == {"Engineer": 2}
    assert education_fields == {"Computer Science": 3}


def test_safe_lookup_options_returns_data(monkeypatch):
    expected = ({"HR": 1}, {"Engineer": 2}, {"Science": 3})
    monkeypatch.setattr(
        ui_helpers, "lookup_options", MagicMock(return_value=expected)
    )

    assert ui_helpers.safe_lookup_options() == expected


def test_safe_lookup_options_handles_database_error(monkeypatch):
    error = ui_helpers.DatabaseError("Database unavailable")
    show_error = MagicMock()
    stop = MagicMock(side_effect=RuntimeError("Streamlit stopped"))

    monkeypatch.setattr(
        ui_helpers, "lookup_options", MagicMock(side_effect=error)
    )
    monkeypatch.setattr(ui_helpers, "show_error", show_error)
    monkeypatch.setattr(ui_helpers.st, "stop", stop)

    with pytest.raises(RuntimeError, match="Streamlit stopped"):
        ui_helpers.safe_lookup_options()

    show_error.assert_called_once_with(error)
    stop.assert_called_once()
