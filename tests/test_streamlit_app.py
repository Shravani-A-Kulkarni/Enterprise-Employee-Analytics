import runpy
from unittest.mock import MagicMock

import auth


def test_router_shows_login_when_signed_out(monkeypatch):
    import streamlit as st

    monkeypatch.setattr(st, "session_state", {})
    page = MagicMock()
    monkeypatch.setattr(st, "Page", lambda *args, **kwargs: page)
    navigation = MagicMock()
    navigation.run = MagicMock()
    mock_navigation = MagicMock(return_value=navigation)
    monkeypatch.setattr(st, "navigation", mock_navigation)
    monkeypatch.setattr(st, "set_page_config", MagicMock())

    runpy.run_path("app/streamlit_app.py")

    mock_navigation.assert_called_once()
    navigation.run.assert_called_once()


def test_router_uses_allowed_pages_for_hr(monkeypatch):
    import streamlit as st

    user = {
        "email": "hr@company.com",
        "role": "HR",
        "display_name": "HR User",
        "employee_number": None,
    }
    monkeypatch.setattr(st, "session_state", {"user": user})
    monkeypatch.setattr(st, "Page", lambda *args, **kwargs: MagicMock())
    navigation = MagicMock()
    navigation.run = MagicMock()
    mock_navigation = MagicMock(return_value=navigation)
    monkeypatch.setattr(st, "navigation", mock_navigation)
    monkeypatch.setattr(st, "set_page_config", MagicMock())

    runpy.run_path("app/streamlit_app.py")

    navigation.run.assert_called_once()
    mock_navigation.assert_called_once()
    pages = mock_navigation.call_args.args[0]
    assert len(pages) > 0


def test_hr_has_onboarding_access():
    assert "Onboarding" in auth.PAGE_ACCESS["HR"]


def test_employee_has_profile_access():
    assert "My Profile" in auth.PAGE_ACCESS["Employee"]