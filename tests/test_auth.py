# # import pytest

# # from auth import AuthManager, PAGE_ACCESS, ROLES, hash_password, verify_password
# # from db_manager import DatabaseError


# # def test_hash_password_format_and_unique_salts():
# #     first = hash_password("StrongPass123")
# #     second = hash_password("StrongPass123")
# #     assert first.startswith("pbkdf2_sha256$")
# #     assert first != second
# #     assert len(first.split("$")) == 4


# # def test_verify_password_success_and_failure():
# #     stored = hash_password("StrongPass123")
# #     assert verify_password("StrongPass123", stored) is True
# #     assert verify_password("WrongPass123", stored) is False


# # @pytest.mark.parametrize("stored", [None, "", "bad", "other$100$abc$def", "pbkdf2_sha256$bad$salt$digest"])
# # def test_verify_password_handles_malformed_hash(stored):
# #     assert verify_password("password", stored) is False


# # def test_role_access_matrix():
# #     assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Projects", "Reviews", "Analytics"]
# #     assert PAGE_ACCESS["Manager"] == ["Home", "Projects", "Reviews", "Analytics"]
# #     assert PAGE_ACCESS["Employee"] == ["Home", "My Profile"]
# #     assert set(PAGE_ACCESS) == set(ROLES)


# # def test_authenticate_normalizes_email_and_returns_user(monkeypatch):
# #     manager = AuthManager()
# #     stored = hash_password("StrongPass123")
# #     monkeypatch.setattr(manager, "query", lambda sql, params: [{
# #         "user_id": 7, "email": "user@example.com", "password_hash": stored,
# #         "role": "Employee", "display_name": "Test User", "employee_number": 123,
# #     }])
# #     result = manager.authenticate(" USER@Example.COM ", "StrongPass123")
# #     assert result == {
# #         "user_id": 7, "email": "user@example.com", "role": "Employee",
# #         "display_name": "Test User", "employee_number": 123,
# #     }


# # @pytest.mark.parametrize("email,password", [("", "StrongPass123"), (None, "StrongPass123"), ("x@example.com", "")])
# # def test_authenticate_empty_credentials_returns_none_without_query(monkeypatch, email, password):
# #     manager = AuthManager()
# #     called = []
# #     monkeypatch.setattr(manager, "query", lambda *args: called.append(args))
# #     assert manager.authenticate(email, password) is None
# #     assert called == []


# # def test_authenticate_wrong_password_returns_none(monkeypatch):
# #     manager = AuthManager()
# #     monkeypatch.setattr(manager, "query", lambda *args: [{
# #         "user_id": 1, "email": "user@example.com", "password_hash": hash_password("CorrectPass123"),
# #         "role": "Employee", "display_name": "Test", "employee_number": 100,
# #     }])
# #     assert manager.authenticate("user@example.com", "WrongPass123") is None


# # def test_authenticate_unknown_user_returns_none(monkeypatch):
# #     manager = AuthManager()
# #     monkeypatch.setattr(manager, "query", lambda *args: [])
# #     assert manager.authenticate("missing@example.com", "WrongPass123") is None


# # def test_create_user_hashes_password_and_executes_insert(monkeypatch):
# #     manager = AuthManager()
# #     calls = []
# #     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append((sql, params)) or 42)
# #     result = manager.create_user(" USER@Example.COM ", "StrongPass123", "Employee", " Test User ", 123)
# #     assert result == 42
# #     sql, params = calls[0]
# #     assert "INSERT INTO AppUser" in sql
# #     assert params[0] == "user@example.com"
# #     assert verify_password("StrongPass123", params[1])
# #     assert params[2:] == ("Employee", "Test User", 123)


# # @pytest.mark.parametrize("email,password,role,display_name", [
# #     ("bad-email", "StrongPass123", "Employee", "User"),
# #     ("user@example.com", "short", "Employee", "User"),
# #     ("user@example.com", "StrongPass123", "Admin", "User"),
# # ])
# # def test_create_user_rejects_invalid_input_without_insert(monkeypatch, email, password, role, display_name):
# #     manager = AuthManager()
# #     calls = []
# #     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
# #     with pytest.raises(DatabaseError):
# #         manager.create_user(email, password, role, display_name)
# #     assert calls == []


# # def test_create_user_wraps_email_validation_error(monkeypatch):
# #     manager = AuthManager()
# #     with pytest.raises(DatabaseError, match="Email is required"):
# #         manager.create_user("", "StrongPass123", "Employee", "User")
# import pytest

# from auth import AuthManager, PAGE_ACCESS, ROLES, hash_password, verify_password
# from db_manager import DatabaseError


# def test_hash_password_format_and_unique_salts():
#     first = hash_password("StrongPass123")
#     second = hash_password("StrongPass123")
#     assert first.startswith("pbkdf2_sha256$")
#     assert first != second
#     assert len(first.split("$")) == 4


# def test_verify_password_success_and_failure():
#     stored = hash_password("StrongPass123")
#     assert verify_password("StrongPass123", stored) is True
#     assert verify_password("WrongPass123", stored) is False


# @pytest.mark.parametrize("stored", [None, "", "bad", "other$100$abc$def", "pbkdf2_sha256$bad$salt$digest"])
# def test_verify_password_handles_malformed_hash(stored):
#     assert verify_password("password", stored) is False


# def test_role_access_matrix():
#     assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Manager"] == ["Home", "Projects", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Employee"] == ["Home", "My Profile"]
#     assert set(PAGE_ACCESS) == set(ROLES)


# def test_authenticate_normalizes_email_and_returns_user(monkeypatch):
#     manager = AuthManager()
#     stored = hash_password("StrongPass123")
#     monkeypatch.setattr(manager, "query", lambda sql, params: [{
#         "user_id": 7, "email": "user@example.com", "password_hash": stored,
#         "role": "Employee", "display_name": "Test User", "employee_number": 123,
#     }])
#     result = manager.authenticate(" USER@Example.COM ", "StrongPass123")
#     assert result == {
#         "user_id": 7, "email": "user@example.com", "role": "Employee",
#         "display_name": "Test User", "employee_number": 123,
#     }


# @pytest.mark.parametrize("email,password", [("", "StrongPass123"), (None, "StrongPass123"), ("x@example.com", "")])
# def test_authenticate_empty_credentials_returns_none_without_query(monkeypatch, email, password):
#     manager = AuthManager()
#     called = []
#     monkeypatch.setattr(manager, "query", lambda *args: called.append(args))
#     assert manager.authenticate(email, password) is None
#     assert called == []


# def test_authenticate_wrong_password_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [{
#         "user_id": 1, "email": "user@example.com", "password_hash": hash_password("CorrectPass123"),
#         "role": "Employee", "display_name": "Test", "employee_number": 100,
#     }])
#     assert manager.authenticate("user@example.com", "WrongPass123") is None


# def test_authenticate_unknown_user_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     assert manager.authenticate("missing@example.com", "WrongPass123") is None


# def test_create_user_hashes_password_and_executes_insert(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append((sql, params)) or 42)
#     result = manager.create_user(" USER@Example.COM ", "StrongPass123", "Employee", " Test User ", 123)
#     assert result == 42
#     sql, params = calls[0]
#     assert "INSERT INTO AppUser" in sql
#     assert params[0] == "user@example.com"
#     assert verify_password("StrongPass123", params[1])
#     assert params[2:] == ("Employee", "Test User", 123)


# @pytest.mark.parametrize("email,password,role,display_name", [
#     ("bad-email", "StrongPass123", "Employee", "User"),
#     ("user@example.com", "short", "Employee", "User"),
#     ("user@example.com", "StrongPass123", "Admin", "User"),
# ])
# def test_create_user_rejects_invalid_input_without_insert(monkeypatch, email, password, role, display_name):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(DatabaseError):
#         manager.create_user(email, password, role, display_name)
#     assert calls == []


# def test_create_user_wraps_email_validation_error(monkeypatch):
#     manager = AuthManager()
#     with pytest.raises(DatabaseError, match="Email is required"):
#         manager.create_user("", "StrongPass123", "Employee", "User")


# # ---------------------------------------------------------------- sign-up
# from auth import validate_signup


# def test_validate_signup_cleans_name_and_email():
#     assert validate_signup("  Asha   Rao ", " ASHA@Example.com ", "Strong123", "Strong123") == \
#         ("Asha Rao", "asha@example.com")


# @pytest.mark.parametrize("name,email,password,confirm,message", [
#     ("", "a@example.com", "Strong123", "Strong123", "full name"),
#     ("Asha", "bad-email", "Strong123", "Strong123", "valid email"),
#     ("Asha", "a@example.com", "short1", "short1", "at least 8"),
#     ("Asha", "a@example.com", "onlyletters", "onlyletters", "letter and one number"),
#     ("Asha", "a@example.com", "12345678", "12345678", "letter and one number"),
#     ("Asha", "a@example.com", "Strong123", "Different123", "do not match"),
# ])
# def test_validate_signup_rejects_bad_input(name, email, password, confirm, message):
#     with pytest.raises(ValueError, match=message):
#         validate_signup(name, email, password, confirm)


# def test_sign_up_creates_employee_account(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append(params) or 9)
#     assert manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123") == 9
#     params = calls[0]
#     assert params[0] == "asha@example.com"
#     assert params[1] != "Strong123" and verify_password("Strong123", params[1])   # hashed, not plain
#     assert params[2:] == ("Employee", "Asha Rao", None)


# def test_sign_up_blocks_duplicate_email(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [{"1": 1}])
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")
#     assert calls == []


# def test_sign_up_handles_duplicate_race(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda *a: (_ for _ in ()).throw(
#         DatabaseError("Statement failed: 1062 (23000): Duplicate entry")))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")
# import pytest

# from auth import AuthManager, PAGE_ACCESS, ROLES, hash_password, verify_password
# from db_manager import DatabaseError


# def test_hash_password_format_and_unique_salts():
#     first = hash_password("StrongPass123")
#     second = hash_password("StrongPass123")
#     assert first.startswith("pbkdf2_sha256$")
#     assert first != second
#     assert len(first.split("$")) == 4


# def test_verify_password_success_and_failure():
#     stored = hash_password("StrongPass123")
#     assert verify_password("StrongPass123", stored) is True
#     assert verify_password("WrongPass123", stored) is False


# @pytest.mark.parametrize("stored", [None, "", "bad", "other$100$abc$def", "pbkdf2_sha256$bad$salt$digest"])
# def test_verify_password_handles_malformed_hash(stored):
#     assert verify_password("password", stored) is False


# def test_role_access_matrix():
#     assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Manager"] == ["Home", "Projects", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Employee"] == ["Home", "My Profile"]
#     assert set(PAGE_ACCESS) == set(ROLES)


# def test_authenticate_normalizes_email_and_returns_user(monkeypatch):
#     manager = AuthManager()
#     stored = hash_password("StrongPass123")
#     monkeypatch.setattr(manager, "query", lambda sql, params: [{
#         "user_id": 7, "email": "user@example.com", "password_hash": stored,
#         "role": "Employee", "display_name": "Test User", "employee_number": 123,
#     }])
#     result = manager.authenticate(" USER@Example.COM ", "StrongPass123")
#     assert result == {
#         "user_id": 7, "email": "user@example.com", "role": "Employee",
#         "display_name": "Test User", "employee_number": 123,
#     }


# @pytest.mark.parametrize("email,password", [("", "StrongPass123"), (None, "StrongPass123"), ("x@example.com", "")])
# def test_authenticate_empty_credentials_returns_none_without_query(monkeypatch, email, password):
#     manager = AuthManager()
#     called = []
#     monkeypatch.setattr(manager, "query", lambda *args: called.append(args))
#     assert manager.authenticate(email, password) is None
#     assert called == []


# def test_authenticate_wrong_password_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [{
#         "user_id": 1, "email": "user@example.com", "password_hash": hash_password("CorrectPass123"),
#         "role": "Employee", "display_name": "Test", "employee_number": 100,
#     }])
#     assert manager.authenticate("user@example.com", "WrongPass123") is None


# def test_authenticate_unknown_user_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     assert manager.authenticate("missing@example.com", "WrongPass123") is None


# def test_create_user_hashes_password_and_executes_insert(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append((sql, params)) or 42)
#     result = manager.create_user(" USER@Example.COM ", "StrongPass123", "Employee", " Test User ", 123)
#     assert result == 42
#     sql, params = calls[0]
#     assert "INSERT INTO AppUser" in sql
#     assert params[0] == "user@example.com"
#     assert verify_password("StrongPass123", params[1])
#     assert params[2:] == ("Employee", "Test User", 123)


# @pytest.mark.parametrize("email,password,role,display_name", [
#     ("bad-email", "StrongPass123", "Employee", "User"),
#     ("user@example.com", "short", "Employee", "User"),
#     ("user@example.com", "StrongPass123", "Admin", "User"),
# ])
# def test_create_user_rejects_invalid_input_without_insert(monkeypatch, email, password, role, display_name):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(DatabaseError):
#         manager.create_user(email, password, role, display_name)
#     assert calls == []


# def test_create_user_wraps_email_validation_error(monkeypatch):
#     manager = AuthManager()
#     with pytest.raises(DatabaseError, match="Email is required"):
#         manager.create_user("", "StrongPass123", "Employee", "User")


# # ---------------------------------------------------------------- sign-up
# from auth import validate_signup


# def test_validate_signup_cleans_name_and_email():
#     assert validate_signup("  Asha   Rao ", " ASHA@Example.com ", "Strong123", "Strong123") == \
#         ("Asha Rao", "asha@example.com")


# @pytest.mark.parametrize("name,email,password,confirm,message", [
#     ("", "a@example.com", "Strong123", "Strong123", "full name"),
#     ("Asha", "bad-email", "Strong123", "Strong123", "valid email"),
#     ("Asha", "a@example.com", "short1", "short1", "at least 8"),
#     ("Asha", "a@example.com", "onlyletters", "onlyletters", "letter and one number"),
#     ("Asha", "a@example.com", "12345678", "12345678", "letter and one number"),
#     ("Asha", "a@example.com", "Strong123", "Different123", "do not match"),
# ])
# def test_validate_signup_rejects_bad_input(name, email, password, confirm, message):
#     with pytest.raises(ValueError, match=message):
#         validate_signup(name, email, password, confirm)


# def test_sign_up_creates_employee_account(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append(params) or 9)
#     assert manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123") == 9
#     params = calls[0]
#     assert params[0] == "asha@example.com"
#     assert params[1] != "Strong123" and verify_password("Strong123", params[1])   # hashed, not plain
#     assert params[2:] == ("Employee", "Asha Rao", None)


# def test_sign_up_blocks_duplicate_email(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [{"1": 1}])
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")
#     assert calls == []


# def test_sign_up_handles_duplicate_race(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda *a: (_ for _ in ()).throw(
#         DatabaseError("Statement failed: 1062 (23000): Duplicate entry")))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")


# # ------------------------------------------------- linking logins to employees
# def _fake_db(manager, monkeypatch, employees=(), linked=()):
#     """Fake query/execute. employees = {email: employee_number}, linked = employee numbers already used."""
#     inserts = []

#     def query(sql, params=()):
#         if "FROM Employee" in sql:
#             number = dict(employees).get(params[0])
#             return [{"employee_number": number}] if number is not None else []
#         if "FROM AppUser WHERE employee_number" in sql:
#             return [{"1": 1}] if params[0] in linked else []
#         return []          # email_exists -> no account yet

#     monkeypatch.setattr(manager, "query", query)
#     monkeypatch.setattr(manager, "execute", lambda sql, params: inserts.append((sql, params)) or 5)
#     return inserts


# def test_sign_up_links_to_employee_with_same_email(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026})
#     manager.sign_up("Justin Drew", "Jus@Gmail.com", "Strong123", "Strong123")
#     assert len(inserts) == 1                                  # only the new login is written
#     assert "INSERT INTO AppUser" in inserts[0][0]
#     assert inserts[0][1][0] == "jus@gmail.com" and inserts[0][1][-1] == 100026


# def test_sign_up_without_employee_record_stays_unlinked(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"someone@else.com": 7})
#     manager.sign_up("Test Employee", "testemployee101@example.com", "Strong123", "Strong123")
#     assert inserts[0][1][-1] is None
#     assert len(inserts) == 1                                  # no Employee row was created


# def test_sign_up_does_not_link_employee_already_claimed(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026}, linked=[100026])
#     manager.sign_up("Justin Drew", "jus@gmail.com", "Strong123", "Strong123")
#     assert inserts[0][1][-1] is None


# def test_linkable_employee_number_never_matches_blank_email(monkeypatch):
#     manager = AuthManager()
#     _fake_db(manager, monkeypatch, employees={})
#     assert manager.linkable_employee_number("") is None
#     assert manager.linkable_employee_number(None) is None


# def test_authenticate_returns_employee_number_for_linked_account(monkeypatch):
#     manager = AuthManager()
#     row = {"user_id": 3, "email": "employee1@company.com", "password_hash": hash_password("Demo@123"),
#            "role": "Employee", "display_name": "Emp One", "employee_number": 1}
#     monkeypatch.setattr(manager, "query", lambda *a: [row])
#     assert manager.authenticate("employee1@company.com", "Demo@123")["employee_number"] == 1


# def test_authenticate_keeps_unlinked_account_unlinked(monkeypatch):
#     manager = AuthManager()
#     row = {"user_id": 9, "email": "jus@gmail.com", "password_hash": hash_password("Strong123"),
#            "role": "Employee", "display_name": "Justin Drew", "employee_number": None}
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *a: [row])
#     monkeypatch.setattr(manager, "execute", lambda *a: calls.append(a))
#     assert manager.authenticate("jus@gmail.com", "Strong123")["employee_number"] is None
#     assert calls == []                                        # login never writes to the database
# import pytest

# from auth import AuthManager, PAGE_ACCESS, ROLES, hash_password, verify_password
# from db_manager import DatabaseError


# def test_hash_password_format_and_unique_salts():
#     first = hash_password("StrongPass123")
#     second = hash_password("StrongPass123")
#     assert first.startswith("pbkdf2_sha256$")
#     assert first != second
#     assert len(first.split("$")) == 4


# def test_verify_password_success_and_failure():
#     stored = hash_password("StrongPass123")
#     assert verify_password("StrongPass123", stored) is True
#     assert verify_password("WrongPass123", stored) is False


# @pytest.mark.parametrize("stored", [None, "", "bad", "other$100$abc$def", "pbkdf2_sha256$bad$salt$digest"])
# def test_verify_password_handles_malformed_hash(stored):
#     assert verify_password("password", stored) is False


# def test_role_access_matrix():
#     assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Manager"] == ["Home", "Projects", "Reviews", "Analytics"]
#     assert PAGE_ACCESS["Employee"] == ["Home", "My Profile"]
#     assert set(PAGE_ACCESS) == set(ROLES)


# def test_authenticate_normalizes_email_and_returns_user(monkeypatch):
#     manager = AuthManager()
#     stored = hash_password("StrongPass123")
#     monkeypatch.setattr(manager, "query", lambda sql, params: [{
#         "user_id": 7, "email": "user@example.com", "password_hash": stored,
#         "role": "Employee", "display_name": "Test User", "employee_number": 123,
#     }])
#     result = manager.authenticate(" USER@Example.COM ", "StrongPass123")
#     assert result == {
#         "user_id": 7, "email": "user@example.com", "role": "Employee",
#         "display_name": "Test User", "employee_number": 123,
#     }


# @pytest.mark.parametrize("email,password", [("", "StrongPass123"), (None, "StrongPass123"), ("x@example.com", "")])
# def test_authenticate_empty_credentials_returns_none_without_query(monkeypatch, email, password):
#     manager = AuthManager()
#     called = []
#     monkeypatch.setattr(manager, "query", lambda *args: called.append(args))
#     assert manager.authenticate(email, password) is None
#     assert called == []


# def test_authenticate_wrong_password_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [{
#         "user_id": 1, "email": "user@example.com", "password_hash": hash_password("CorrectPass123"),
#         "role": "Employee", "display_name": "Test", "employee_number": 100,
#     }])
#     assert manager.authenticate("user@example.com", "WrongPass123") is None


# def test_authenticate_unknown_user_returns_none(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     assert manager.authenticate("missing@example.com", "WrongPass123") is None


# def test_create_user_hashes_password_and_executes_insert(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append((sql, params)) or 42)
#     result = manager.create_user(" USER@Example.COM ", "StrongPass123", "Employee", " Test User ", 123)
#     assert result == 42
#     sql, params = calls[0]
#     assert "INSERT INTO AppUser" in sql
#     assert params[0] == "user@example.com"
#     assert verify_password("StrongPass123", params[1])
#     assert params[2:] == ("Employee", "Test User", 123)


# @pytest.mark.parametrize("email,password,role,display_name", [
#     ("bad-email", "StrongPass123", "Employee", "User"),
#     ("user@example.com", "short", "Employee", "User"),
#     ("user@example.com", "StrongPass123", "Admin", "User"),
# ])
# def test_create_user_rejects_invalid_input_without_insert(monkeypatch, email, password, role, display_name):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(DatabaseError):
#         manager.create_user(email, password, role, display_name)
#     assert calls == []


# def test_create_user_wraps_email_validation_error(monkeypatch):
#     manager = AuthManager()
#     with pytest.raises(DatabaseError, match="Email is required"):
#         manager.create_user("", "StrongPass123", "Employee", "User")


# # ---------------------------------------------------------------- sign-up
# from auth import validate_signup


# def test_validate_signup_cleans_name_and_email():
#     assert validate_signup("  Asha   Rao ", " ASHA@Example.com ", "Strong123", "Strong123") == \
#         ("Asha Rao", "asha@example.com")


# @pytest.mark.parametrize("name,email,password,confirm,message", [
#     ("", "a@example.com", "Strong123", "Strong123", "full name"),
#     ("Asha", "bad-email", "Strong123", "Strong123", "valid email"),
#     ("Asha", "a@example.com", "short1", "short1", "at least 8"),
#     ("Asha", "a@example.com", "onlyletters", "onlyletters", "letter and one number"),
#     ("Asha", "a@example.com", "12345678", "12345678", "letter and one number"),
#     ("Asha", "a@example.com", "Strong123", "Different123", "do not match"),
# ])
# def test_validate_signup_rejects_bad_input(name, email, password, confirm, message):
#     with pytest.raises(ValueError, match=message):
#         validate_signup(name, email, password, confirm)


# def test_sign_up_creates_employee_account(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append(params) or 9)
#     assert manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123") == 9
#     params = calls[0]
#     assert params[0] == "asha@example.com"
#     assert params[1] != "Strong123" and verify_password("Strong123", params[1])   # hashed, not plain
#     assert params[2:] == ("Employee", "Asha Rao", None)


# def test_sign_up_blocks_duplicate_email(monkeypatch):
#     manager = AuthManager()
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *args: [{"1": 1}])
#     monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")
#     assert calls == []


# def test_sign_up_handles_duplicate_race(monkeypatch):
#     manager = AuthManager()
#     monkeypatch.setattr(manager, "query", lambda *args: [])
#     monkeypatch.setattr(manager, "execute", lambda *a: (_ for _ in ()).throw(
#         DatabaseError("Statement failed: 1062 (23000): Duplicate entry")))
#     with pytest.raises(ValueError, match="already exists"):
#         manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")


# # ------------------------------------------------- linking logins to employees
# def _fake_db(manager, monkeypatch, employees=(), linked=()):
#     """Fake query/execute. employees = {email: employee_number}, linked = employee numbers already used."""
#     inserts = []

#     def query(sql, params=()):
#         if "FROM Employee" in sql:
#             number = dict(employees).get(params[0])
#             return [{"employee_number": number}] if number is not None else []
#         if "FROM AppUser WHERE employee_number" in sql:
#             return [{"1": 1}] if params[0] in linked else []
#         return []          # email_exists -> no account yet

#     monkeypatch.setattr(manager, "query", query)
#     monkeypatch.setattr(manager, "execute", lambda sql, params: inserts.append((sql, params)) or 5)
#     return inserts


# def test_sign_up_links_to_employee_with_same_email(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026})
#     manager.sign_up("Justin Drew", "Jus@Gmail.com", "Strong123", "Strong123")
#     assert len(inserts) == 1                                  # only the new login is written
#     assert "INSERT INTO AppUser" in inserts[0][0]
#     assert inserts[0][1][0] == "jus@gmail.com" and inserts[0][1][-1] == 100026


# def test_sign_up_without_employee_record_stays_unlinked(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"someone@else.com": 7})
#     manager.sign_up("Test Employee", "testemployee101@example.com", "Strong123", "Strong123")
#     assert inserts[0][1][-1] is None
#     assert len(inserts) == 1                                  # no Employee row was created


# def test_sign_up_does_not_link_employee_already_claimed(monkeypatch):
#     manager = AuthManager()
#     inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026}, linked=[100026])
#     manager.sign_up("Justin Drew", "jus@gmail.com", "Strong123", "Strong123")
#     assert inserts[0][1][-1] is None


# def test_linkable_employee_number_never_matches_blank_email(monkeypatch):
#     manager = AuthManager()
#     _fake_db(manager, monkeypatch, employees={})
#     assert manager.linkable_employee_number("") is None
#     assert manager.linkable_employee_number(None) is None


# def test_authenticate_returns_employee_number_for_linked_account(monkeypatch):
#     manager = AuthManager()
#     row = {"user_id": 3, "email": "employee1@company.com", "password_hash": hash_password("Demo@123"),
#            "role": "Employee", "display_name": "Emp One", "employee_number": 1}
#     monkeypatch.setattr(manager, "query", lambda *a: [row])
#     assert manager.authenticate("employee1@company.com", "Demo@123")["employee_number"] == 1


# def test_authenticate_keeps_unlinked_account_unlinked(monkeypatch):
#     manager = AuthManager()
#     row = {"user_id": 9, "email": "jus@gmail.com", "password_hash": hash_password("Strong123"),
#            "role": "Employee", "display_name": "Justin Drew", "employee_number": None}
#     calls = []
#     monkeypatch.setattr(manager, "query", lambda *a: [row])
#     monkeypatch.setattr(manager, "execute", lambda *a: calls.append(a))
#     assert manager.authenticate("jus@gmail.com", "Strong123")["employee_number"] is None
#     assert calls == []                                        # login never writes to the database


# # ------------------------------------------- which employee may this login see?
# def _lookup_db(manager, monkeypatch, appuser, employees=None, claimed=()):
#     def query(sql, params=()):
#         if "FROM AppUser WHERE user_id" in sql:
#             return [appuser] if appuser else []
#         if "FROM Employee WHERE email" in sql:
#             n = (employees or {}).get(params[0])
#             return [{"employee_number": n}] if n else []
#         return [{"1": 1}] if params[0] in claimed else []
#     monkeypatch.setattr(manager, "query", query)
#     monkeypatch.setattr(manager, "execute", lambda *a: pytest.fail("must not write"))


# def test_find_employee_uses_linked_number(monkeypatch):
#     m = AuthManager()
#     _lookup_db(m, monkeypatch, {"employee_number": 1, "email": "employee1@company.com"})
#     assert m.find_employee_for_user({"user_id": 3, "role": "Employee"}) == (1, "linked")


# def test_find_employee_falls_back_to_exact_email(monkeypatch):
#     m = AuthManager()
#     _lookup_db(m, monkeypatch, {"employee_number": None, "email": "jus@gmail.com"}, {"jus@gmail.com": 100026})
#     assert m.find_employee_for_user({"user_id": 9, "role": "Employee"}) == (100026, "email")


# def test_find_employee_returns_nothing_when_unmatched_claimed_inactive_or_not_employee(monkeypatch):
#     m = AuthManager()
#     _lookup_db(m, monkeypatch, {"employee_number": None, "email": "x@example.com"}, {})
#     assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
#     _lookup_db(m, monkeypatch, {"employee_number": None, "email": "jus@gmail.com"}, {"jus@gmail.com": 5}, claimed=[5])
#     assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
#     _lookup_db(m, monkeypatch, None)
#     assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
#     _lookup_db(m, monkeypatch, {"employee_number": 1, "email": "hr@company.com"})
#     assert m.find_employee_for_user({"user_id": 1, "role": "HR"}) == (None, None)
#     assert m.find_employee_for_user(None) == (None, None)
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
    assert PAGE_ACCESS["HR"] == ["Home", "Onboarding", "Reviews", "Analytics"]
    assert PAGE_ACCESS["Manager"] == ["Home", "Employee Directory", "Projects", "Reviews", "Analytics"]
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


# ---------------------------------------------------------------- sign-up
from auth import validate_signup


def test_validate_signup_cleans_name_and_email():
    assert validate_signup("  Asha   Rao ", " ASHA@Example.com ", "Strong123", "Strong123") == \
        ("Asha Rao", "asha@example.com")


@pytest.mark.parametrize("name,email,password,confirm,message", [
    ("", "a@example.com", "Strong123", "Strong123", "full name"),
    ("Asha", "bad-email", "Strong123", "Strong123", "valid email"),
    ("Asha", "a@example.com", "short1", "short1", "at least 8"),
    ("Asha", "a@example.com", "onlyletters", "onlyletters", "letter and one number"),
    ("Asha", "a@example.com", "12345678", "12345678", "letter and one number"),
    ("Asha", "a@example.com", "Strong123", "Different123", "do not match"),
])
def test_validate_signup_rejects_bad_input(name, email, password, confirm, message):
    with pytest.raises(ValueError, match=message):
        validate_signup(name, email, password, confirm)


def test_sign_up_creates_employee_account(monkeypatch):
    manager = AuthManager()
    calls = []
    monkeypatch.setattr(manager, "query", lambda *args: [])
    monkeypatch.setattr(manager, "execute", lambda sql, params: calls.append(params) or 9)
    assert manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123") == 9
    params = calls[0]
    assert params[0] == "asha@example.com"
    assert params[1] != "Strong123" and verify_password("Strong123", params[1])   # hashed, not plain
    assert params[2:] == ("Employee", "Asha Rao", None)


def test_sign_up_blocks_duplicate_email(monkeypatch):
    manager = AuthManager()
    calls = []
    monkeypatch.setattr(manager, "query", lambda *args: [{"1": 1}])
    monkeypatch.setattr(manager, "execute", lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="already exists"):
        manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")
    assert calls == []


def test_sign_up_handles_duplicate_race(monkeypatch):
    manager = AuthManager()
    monkeypatch.setattr(manager, "query", lambda *args: [])
    monkeypatch.setattr(manager, "execute", lambda *a: (_ for _ in ()).throw(
        DatabaseError("Statement failed: 1062 (23000): Duplicate entry")))
    with pytest.raises(ValueError, match="already exists"):
        manager.sign_up("Asha Rao", "asha@example.com", "Strong123", "Strong123")


# ------------------------------------------------- linking logins to employees
def _fake_db(manager, monkeypatch, employees=(), linked=()):
    """Fake query/execute. employees = {email: employee_number}, linked = employee numbers already used."""
    inserts = []

    def query(sql, params=()):
        if "FROM Employee" in sql:
            number = dict(employees).get(params[0])
            return [{"employee_number": number}] if number is not None else []
        if "FROM AppUser WHERE employee_number" in sql:
            return [{"1": 1}] if params[0] in linked else []
        return []          # email_exists -> no account yet

    monkeypatch.setattr(manager, "query", query)
    monkeypatch.setattr(manager, "execute", lambda sql, params: inserts.append((sql, params)) or 5)
    return inserts


def test_sign_up_links_to_employee_with_same_email(monkeypatch):
    manager = AuthManager()
    inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026})
    manager.sign_up("Justin Drew", "Jus@Gmail.com", "Strong123", "Strong123")
    assert len(inserts) == 1                                  # only the new login is written
    assert "INSERT INTO AppUser" in inserts[0][0]
    assert inserts[0][1][0] == "jus@gmail.com" and inserts[0][1][-1] == 100026


def test_sign_up_without_employee_record_stays_unlinked(monkeypatch):
    manager = AuthManager()
    inserts = _fake_db(manager, monkeypatch, employees={"someone@else.com": 7})
    manager.sign_up("Test Employee", "testemployee101@example.com", "Strong123", "Strong123")
    assert inserts[0][1][-1] is None
    assert len(inserts) == 1                                  # no Employee row was created


def test_sign_up_does_not_link_employee_already_claimed(monkeypatch):
    manager = AuthManager()
    inserts = _fake_db(manager, monkeypatch, employees={"jus@gmail.com": 100026}, linked=[100026])
    manager.sign_up("Justin Drew", "jus@gmail.com", "Strong123", "Strong123")
    assert inserts[0][1][-1] is None


def test_linkable_employee_number_never_matches_blank_email(monkeypatch):
    manager = AuthManager()
    _fake_db(manager, monkeypatch, employees={})
    assert manager.linkable_employee_number("") is None
    assert manager.linkable_employee_number(None) is None


def test_authenticate_returns_employee_number_for_linked_account(monkeypatch):
    manager = AuthManager()
    row = {"user_id": 3, "email": "employee1@company.com", "password_hash": hash_password("Demo@123"),
           "role": "Employee", "display_name": "Emp One", "employee_number": 1}
    monkeypatch.setattr(manager, "query", lambda *a: [row])
    assert manager.authenticate("employee1@company.com", "Demo@123")["employee_number"] == 1


def test_authenticate_keeps_unlinked_account_unlinked(monkeypatch):
    manager = AuthManager()
    row = {"user_id": 9, "email": "jus@gmail.com", "password_hash": hash_password("Strong123"),
           "role": "Employee", "display_name": "Justin Drew", "employee_number": None}
    calls = []
    monkeypatch.setattr(manager, "query", lambda *a: [row])
    monkeypatch.setattr(manager, "execute", lambda *a: calls.append(a))
    assert manager.authenticate("jus@gmail.com", "Strong123")["employee_number"] is None
    assert calls == []                                        # login never writes to the database


# ------------------------------------------- which employee may this login see?
def _lookup_db(manager, monkeypatch, appuser, employees=None, claimed=()):
    def query(sql, params=()):
        if "FROM AppUser WHERE user_id" in sql:
            return [appuser] if appuser else []
        if "FROM Employee WHERE email" in sql:
            n = (employees or {}).get(params[0])
            return [{"employee_number": n}] if n else []
        return [{"1": 1}] if params[0] in claimed else []
    monkeypatch.setattr(manager, "query", query)
    monkeypatch.setattr(manager, "execute", lambda *a: pytest.fail("must not write"))


def test_find_employee_uses_linked_number(monkeypatch):
    m = AuthManager()
    _lookup_db(m, monkeypatch, {"employee_number": 1, "email": "employee1@company.com"})
    assert m.find_employee_for_user({"user_id": 3, "role": "Employee"}) == (1, "linked")


def test_find_employee_falls_back_to_exact_email(monkeypatch):
    m = AuthManager()
    _lookup_db(m, monkeypatch, {"employee_number": None, "email": "jus@gmail.com"}, {"jus@gmail.com": 100026})
    assert m.find_employee_for_user({"user_id": 9, "role": "Employee"}) == (100026, "email")


def test_find_employee_returns_nothing_when_unmatched_claimed_inactive_or_not_employee(monkeypatch):
    m = AuthManager()
    _lookup_db(m, monkeypatch, {"employee_number": None, "email": "x@example.com"}, {})
    assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
    _lookup_db(m, monkeypatch, {"employee_number": None, "email": "jus@gmail.com"}, {"jus@gmail.com": 5}, claimed=[5])
    assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
    _lookup_db(m, monkeypatch, None)
    assert m.find_employee_for_user({"user_id": 1, "role": "Employee"}) == (None, None)
    _lookup_db(m, monkeypatch, {"employee_number": 1, "email": "hr@company.com"})
    assert m.find_employee_for_user({"user_id": 1, "role": "HR"}) == (None, None)
    assert m.find_employee_for_user(None) == (None, None)
