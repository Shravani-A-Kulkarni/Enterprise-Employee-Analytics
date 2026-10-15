
import runpy
from unittest.mock import MagicMock, patch

import streamlit as st
from db_manager import DatabaseError


def run_signup(submitted, sign_up_side_effect=None):
    values = iter(["Test User", "test@example.com", "Password123", "Password123"])

    with (
        patch.object(st, "columns", return_value=[
            MagicMock(), MagicMock(), MagicMock()
        ]),
        patch.object(st, "form"),
        patch.object(st, "text_input", side_effect=lambda *a, **k: next(values)),
        patch.object(st, "form_submit_button", return_value=submitted),
        patch.object(st, "title"),
        patch.object(st, "subheader"),
        patch.object(st, "page_link"),
        patch.object(st, "warning") as warning,
        patch.object(st, "error") as error,
        patch.object(st, "success") as success,
        patch("auth.AuthManager") as auth_manager,
    ):
        auth_manager.return_value.sign_up.side_effect = sign_up_side_effect
        runpy.run_path("app/signup.py")
        return warning, error, success, auth_manager


def test_signup_form_renders():
    run_signup(False)


def test_signup_success():
    _, _, success, auth = run_signup(True)
    auth.return_value.sign_up.assert_called_once_with(
        "Test User", "test@example.com", "Password123", "Password123"
    )
    success.assert_called_once_with("Account created! You can now sign in.")


def test_signup_invalid_input():
    warning, _, _, _ = run_signup(True, ValueError("Invalid input"))
    warning.assert_called_once_with("Invalid input")


def test_signup_database_error():
    _, error, _, _ = run_signup(True, DatabaseError("Database unavailable"))
    error.assert_called_once_with("Database unavailable")
