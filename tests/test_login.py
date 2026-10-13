import importlib
import sys
from unittest.mock import MagicMock

import pytest

from db_manager import DatabaseError


@pytest.fixture
def login_page(monkeypatch):
    import streamlit as st
    import auth
    import db_manager

    columns = [MagicMock(), MagicMock(), MagicMock()]
    monkeypatch.setattr(st, "columns", lambda *args, **kwargs: columns)

    form = MagicMock()
    form.__enter__ = lambda self: self
    form.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(st, "form", lambda *args, **kwargs: form)
    monkeypatch.setattr(st, "text_input", MagicMock(side_effect=["hr@company.com", "Demo@123"]))
    monkeypatch.setattr(st, "form_submit_button", lambda *args, **kwargs: True)
    monkeypatch.setattr(st, "title", MagicMock())
    monkeypatch.setattr(st, "subheader", MagicMock())
    monkeypatch.setattr(st, "expander", lambda *args, **kwargs: form)
    monkeypatch.setattr(st, "markdown", MagicMock())
    monkeypatch.setattr(st, "error", MagicMock())
    monkeypatch.setattr(st, "rerun", MagicMock())
    monkeypatch.setattr(st, "session_state", {})

    monkeypatch.setattr(db_manager, "get_setting", lambda *args: "0")
    monkeypatch.setattr(auth.AuthManager, "authenticate", lambda *args: None)

    sys.modules.pop("login", None)
    yield st
    sys.modules.pop("login", None)


def test_login_invalid_credentials(login_page):
    import login
    login_page.error.assert_called_once_with("Invalid email or password.")


def test_login_database_error(login_page, monkeypatch):
    import auth

    monkeypatch.setattr(
        auth.AuthManager,
        "authenticate",
        lambda *args: (_ for _ in ()).throw(DatabaseError("Database unavailable")),
    )

    sys.modules.pop("login", None)
    import login

    login_page.error.assert_called_with("Database unavailable")


def test_login_success(login_page, monkeypatch):
    import auth

    user = {
        "email": "hr@company.com",
        "role": "HR",
        "display_name": "HR User",
        "employee_number": None,
    }
    monkeypatch.setattr(auth.AuthManager, "authenticate", lambda *args: user)

    sys.modules.pop("login", None)
    import login

    assert login_page.session_state["user"] == user
    login_page.rerun.assert_called_once()