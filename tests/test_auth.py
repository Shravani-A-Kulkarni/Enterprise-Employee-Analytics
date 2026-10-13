import pytest

from auth import AuthManager, PAGE_ACCESS, ROLES, hash_password, verify_password
from db_manager import DatabaseError


def test_hash_password_format_and_unique_salts():
    first = hash_password("StrongPass123")
    second = hash_password("StrongPass123")
    assert first.startswith("pbkdf2_sha256$")
    assert first != second
    assert len(first.split("$")) == 4


def test_verify_password_success_and_failure():
    stored = hash_password("StrongPass123")
    assert verify_password("StrongPass123", stored) is True
    assert verify_password("WrongPass123", stored) is False


@pytest.mark.parametrize("stored", [None, "", "bad", "other$100$abc$def", "pbkdf2_sha256$bad$salt$digest"])
def test_verify_password_handles_malformed_hash(stored):
    assert verify_password("password", stored) is False


def test_role_access_matrix():
    assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Projects", "Reviews", "Analytics"]
    assert PAGE_ACCESS["Manager"] == ["Home", "Projects", "Reviews", "Analytics"]
    assert PAGE_ACCESS["Employee"] == ["Home", "My Profile"]
    assert set(PAGE_ACCESS) == set(ROLES)


def test_authenticate_normalizes_email_and_returns_user(monkeypatch):
    manager = AuthManager()
    stored = hash_password("StrongPass123")
    monkeypatch.setattr(manager, "query", lambda sql, params: [{
        "user_id": 7, "email": "user@example.com", "password_hash": stored,
        "role": "Employee", "display_name": "Test User", "employee_number": 123,
    }])
    result = manager.authenticate(" USER@Example.COM ", "StrongPass123")
    assert result == {
        "user_id": 7, "email": "user@example.com", "role": "Employee",
        "display_name": "Test User", "employee_number": 123,
    }


@pytest.mark.parametrize("email,password", [("", "StrongPass123"), (None, "StrongPass123"), ("x@example.com", "")])
def test_authenticate_empty_credentials_returns_none_without_query(monkeypatch, email, password):
    manager = AuthManager()
    called = []
    monkeypatch.setattr(manager, "query", lambda *args: called.append(args))
    assert manager.authenticate(email, password) is None
    assert called == []


def test_authenticate_wrong_password_returns_none(monkeypatch):
    manager = AuthManager()
    monkeypatch.setattr(manager, "query", lambda *args: [{
        "user_id": 1, "email": "user@example.com", "password_hash": hash_password("CorrectPass123"),
        "role": "Employee", "display_name": "Test", "employee_number": 100,
    }])
    assert manager.authenticate("user@example.com", "WrongPass123") is None


def test_authenticate_unknown_user_returns_none(monkeypatch):
    manager = AuthManager()
    monkeypatch.setattr(manager, "query", lambda *args: [])
    assert manager.authenticate("missing@example.com", "WrongPass123") is None


def test_create_user_hashes_password_and_executes_insert(monkeypatch):
    manager = AuthManager()
    calls = []
    monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append((sql, params)) or 42)
    result = manager.create_user(" USER@Example.COM ", "StrongPass123", "Employee", " Test User ", 123)
    assert result == 42
    sql, params = calls[0]
    assert "INSERT INTO AppUser" in sql
    assert params[0] == "user@example.com"
    assert verify_password("StrongPass123", params[1])
    assert params[2:] == ("Employee", "Test User", 123)


@pytest.mark.parametrize("email,password,role,display_name", [
    ("bad-email", "StrongPass123", "Employee", "User"),
    ("user@example.com", "short", "Employee", "User"),
    ("user@example.com", "StrongPass123", "Admin", "User"),
])
def test_create_user_rejects_invalid_input_without_insert(monkeypatch, email, password, role, display_name):
    manager = AuthManager()
    calls = []
    monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
    with pytest.raises(DatabaseError):
        manager.create_user(email, password, role, display_name)
    assert calls == []


def test_create_user_wraps_email_validation_error(monkeypatch):
    manager = AuthManager()
    with pytest.raises(DatabaseError, match="Email is required"):
        manager.create_user("", "StrongPass123", "Employee", "User")
