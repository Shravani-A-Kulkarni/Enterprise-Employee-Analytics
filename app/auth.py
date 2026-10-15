# # """auth.py - password hashing, login lookup and role -> page access.

# # No Streamlit in here, so it can be tested on its own.
# # """
# # import hashlib
# # import hmac
# # import secrets

# # from db_manager import DatabaseConnection, DatabaseError
# # from entities import _check_email

# # ROLES = ("HR", "Manager", "Employee")
# # _ITERATIONS = 200_000

# # # Which sidebar pages each role can open. Change this table to change access.
# # # The names must match the page names registered in streamlit_app.py.
# # PAGE_ACCESS = {
# #     "HR":       ["Home", "Onboarding", "Projects", "Reviews", "Analytics"],
# #     "Manager":  ["Home", "Projects", "Reviews", "Analytics"],
# #     "Employee": ["Home", "My Profile"],
# # }


# # def hash_password(password, salt=None, iterations=_ITERATIONS):
# #     """Return 'pbkdf2_sha256$iterations$salt$hash' (salted, slow on purpose)."""
# #     salt = salt or secrets.token_hex(16)
# #     digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
# #     return f"pbkdf2_sha256${iterations}${salt}${digest}"


# # def verify_password(password, stored):
# #     try:
# #         algo, iterations, salt, digest = stored.split("$")
# #         if algo != "pbkdf2_sha256":
# #             return False
# #         candidate = hashlib.pbkdf2_hmac(
# #             "sha256", password.encode(), salt.encode(), int(iterations)).hex()
# #     except (ValueError, AttributeError):
# #         return False
# #     return hmac.compare_digest(candidate, digest)


# # _DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


# # class AuthManager(DatabaseConnection):
# #     DB_SETTING = "OLTP_DB"

# #     def authenticate(self, email, password):
# #         """Return the user dict if email + password are right, otherwise None."""
# #         email = (email or "").strip().lower()
# #         if not email or not password:
# #             return None
# #         rows = self.query(
# #             """SELECT user_id, email, password_hash, role, display_name, employee_number
# #                FROM AppUser WHERE email = %s AND is_active = 1""", (email,))
# #         stored = rows[0]["password_hash"] if rows else _DUMMY_HASH
# #         ok = verify_password(password, stored)
# #         if not rows or not ok:
# #             return None
# #         user = rows[0]
# #         return {"user_id": user["user_id"], "email": user["email"], "role": user["role"],
# #                 "display_name": user["display_name"], "employee_number": user["employee_number"]}

# #     def create_user(self, email, password, role, display_name, employee_number=None):
# #         """Add a login. Raises DatabaseError on bad input or a duplicate email."""
# #         try:
# #             email = _check_email(email)
# #         except ValueError as exc:
# #             raise DatabaseError(str(exc)) from exc
# #         if role not in ROLES:
# #             raise DatabaseError(f"Role must be one of {', '.join(ROLES)}")
# #         if len(password or "") < 8:
# #             raise DatabaseError("Password must be at least 8 characters")
# #         return self.execute(
# #             """INSERT INTO AppUser (email, password_hash, role, display_name, employee_number)
# #                VALUES (%s, %s, %s, %s, %s)""",
# #             (email, hash_password(password), role, display_name.strip(), employee_number))
# """auth.py - password hashing, login lookup and role -> page access.

# No Streamlit in here, so it can be tested on its own.
# """
# import hashlib
# import hmac
# import secrets

# from db_manager import DatabaseConnection, DatabaseError
# from entities import _check_email

# ROLES = ("HR", "Manager", "Employee")
# _ITERATIONS = 200_000
# SIGNUP_ROLE = "Employee"   # self sign-up can only ever create Employee accounts

# # Which sidebar pages each role can open. Change this table to change access.
# # The names must match the page names registered in streamlit_app.py.
# PAGE_ACCESS = {
#     "HR":       ["Home", "Onboarding", "Reviews", "Analytics"],
#     "Manager":  ["Home", "Projects", "Reviews", "Analytics"],
#     "Employee": ["Home", "My Profile"],
# }


# def hash_password(password, salt=None, iterations=_ITERATIONS):
#     """Return 'pbkdf2_sha256$iterations$salt$hash' (salted, slow on purpose)."""
#     salt = salt or secrets.token_hex(16)
#     digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
#     return f"pbkdf2_sha256${iterations}${salt}${digest}"


# def verify_password(password, stored):
#     try:
#         algo, iterations, salt, digest = stored.split("$")
#         if algo != "pbkdf2_sha256":
#             return False
#         candidate = hashlib.pbkdf2_hmac(
#             "sha256", password.encode(), salt.encode(), int(iterations)).hex()
#     except (ValueError, AttributeError):
#         return False
#     return hmac.compare_digest(candidate, digest)


# _DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


# def validate_signup(name, email, password, confirm_password):
#     """Check the sign-up form. Returns (clean_name, clean_email) or raises ValueError."""
#     name = " ".join((name or "").split())
#     if len(name) < 2:
#         raise ValueError("Please enter your full name (at least 2 characters)")
#     if len(name) > 150:
#         raise ValueError("Name must be at most 150 characters")
#     email = _check_email(email)
#     password = password or ""
#     if len(password) < 8:
#         raise ValueError("Password must be at least 8 characters")
#     if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
#         raise ValueError("Password must contain at least one letter and one number")
#     if password != confirm_password:
#         raise ValueError("Passwords do not match")
#     return name, email


# class AuthManager(DatabaseConnection):
#     DB_SETTING = "OLTP_DB"

#     def authenticate(self, email, password):
#         """Return the user dict if email + password are right, otherwise None."""
#         email = (email or "").strip().lower()
#         if not email or not password:
#             return None
#         rows = self.query(
#             """SELECT user_id, email, password_hash, role, display_name, employee_number
#                FROM AppUser WHERE email = %s AND is_active = 1""", (email,))
#         stored = rows[0]["password_hash"] if rows else _DUMMY_HASH
#         ok = verify_password(password, stored)
#         if not rows or not ok:
#             return None
#         user = rows[0]
#         return {"user_id": user["user_id"], "email": user["email"], "role": user["role"],
#                 "display_name": user["display_name"], "employee_number": user["employee_number"]}

#     def create_user(self, email, password, role, display_name, employee_number=None):
#         """Add a login. Raises DatabaseError on bad input or a duplicate email."""
#         try:
#             email = _check_email(email)
#         except ValueError as exc:
#             raise DatabaseError(str(exc)) from exc
#         if role not in ROLES:
#             raise DatabaseError(f"Role must be one of {', '.join(ROLES)}")
#         if len(password or "") < 8:
#             raise DatabaseError("Password must be at least 8 characters")
#         return self.execute(
#             """INSERT INTO AppUser (email, password_hash, role, display_name, employee_number)
#                VALUES (%s, %s, %s, %s, %s)""",
#             (email, hash_password(password), role, display_name.strip(), employee_number))

#     def email_exists(self, email):
#         """True if an account (active or not) already uses this email."""
#         email = (email or "").strip().lower()
#         return bool(self.query("SELECT 1 FROM AppUser WHERE email = %s", (email,)))

#     def sign_up(self, name, email, password, confirm_password):
#         """Self sign-up: validate, block duplicate emails, save an Employee login.

#         Raises ValueError for bad input / duplicate email, DatabaseError for DB problems.
#         Returns the new user_id.
#         """
#         name, email = validate_signup(name, email, password, confirm_password)
#         if self.email_exists(email):
#             raise ValueError("An account with this email already exists. Please sign in instead.")
#         try:
#             return self.create_user(email, password, SIGNUP_ROLE, name)
#         except DatabaseError as exc:
#             if "duplicate" in str(exc).lower():     # two people signed up at the same moment
#                 raise ValueError("An account with this email already exists. Please sign in instead.") from exc
#             raise
# """auth.py - password hashing, login lookup and role -> page access.

# No Streamlit in here, so it can be tested on its own.
# """
# import hashlib
# import hmac
# import secrets

# from db_manager import DatabaseConnection, DatabaseError
# from entities import _check_email

# ROLES = ("HR", "Manager", "Employee")
# _ITERATIONS = 200_000
# SIGNUP_ROLE = "Employee"   # self sign-up can only ever create Employee accounts

# # Which sidebar pages each role can open. Change this table to change access.
# # The names must match the page names registered in streamlit_app.py.
# PAGE_ACCESS = {
#     "HR":       ["Home", "Onboarding", "Reviews", "Analytics"],
#     "Manager":  ["Home", "Projects", "Reviews", "Analytics"],
#     "Employee": ["Home", "My Profile"],
# }


# def hash_password(password, salt=None, iterations=_ITERATIONS):
#     """Return 'pbkdf2_sha256$iterations$salt$hash' (salted, slow on purpose)."""
#     salt = salt or secrets.token_hex(16)
#     digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
#     return f"pbkdf2_sha256${iterations}${salt}${digest}"


# def verify_password(password, stored):
#     try:
#         algo, iterations, salt, digest = stored.split("$")
#         if algo != "pbkdf2_sha256":
#             return False
#         candidate = hashlib.pbkdf2_hmac(
#             "sha256", password.encode(), salt.encode(), int(iterations)).hex()
#     except (ValueError, AttributeError):
#         return False
#     return hmac.compare_digest(candidate, digest)


# _DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


# def validate_signup(name, email, password, confirm_password):
#     """Check the sign-up form. Returns (clean_name, clean_email) or raises ValueError."""
#     name = " ".join((name or "").split())
#     if len(name) < 2:
#         raise ValueError("Please enter your full name (at least 2 characters)")
#     if len(name) > 150:
#         raise ValueError("Name must be at most 150 characters")
#     email = _check_email(email)
#     password = password or ""
#     if len(password) < 8:
#         raise ValueError("Password must be at least 8 characters")
#     if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
#         raise ValueError("Password must contain at least one letter and one number")
#     if password != confirm_password:
#         raise ValueError("Passwords do not match")
#     return name, email


# class AuthManager(DatabaseConnection):
#     DB_SETTING = "OLTP_DB"

#     def authenticate(self, email, password):
#         """Return the user dict if email + password are right, otherwise None."""
#         email = (email or "").strip().lower()
#         if not email or not password:
#             return None
#         rows = self.query(
#             """SELECT user_id, email, password_hash, role, display_name, employee_number
#                FROM AppUser WHERE email = %s AND is_active = 1""", (email,))
#         stored = rows[0]["password_hash"] if rows else _DUMMY_HASH
#         ok = verify_password(password, stored)
#         if not rows or not ok:
#             return None
#         user = rows[0]
#         return {"user_id": user["user_id"], "email": user["email"], "role": user["role"],
#                 "display_name": user["display_name"], "employee_number": user["employee_number"]}

#     def create_user(self, email, password, role, display_name, employee_number=None):
#         """Add a login. Raises DatabaseError on bad input or a duplicate email."""
#         try:
#             email = _check_email(email)
#         except ValueError as exc:
#             raise DatabaseError(str(exc)) from exc
#         if role not in ROLES:
#             raise DatabaseError(f"Role must be one of {', '.join(ROLES)}")
#         if len(password or "") < 8:
#             raise DatabaseError("Password must be at least 8 characters")
#         return self.execute(
#             """INSERT INTO AppUser (email, password_hash, role, display_name, employee_number)
#                VALUES (%s, %s, %s, %s, %s)""",
#             (email, hash_password(password), role, display_name.strip(), employee_number))

#     def email_exists(self, email):
#         """True if an account (active or not) already uses this email."""
#         email = (email or "").strip().lower()
#         return bool(self.query("SELECT 1 FROM AppUser WHERE email = %s", (email,)))

#     def linkable_employee_number(self, email):
#         """Employee number whose Employee.email is EXACTLY this email, or None.

#         Returns None (so the new login stays unlinked) when no employee has that email,
#         or when another login is already linked to that employee. Nothing is guessed
#         from names, and no existing row is changed.
#         """
#         email = (email or "").strip().lower()
#         rows = self.query("SELECT employee_number FROM Employee WHERE email = %s", (email,))
#         if len(rows) != 1:
#             return None
#         number = rows[0]["employee_number"]
#         if self.query("SELECT 1 FROM AppUser WHERE employee_number = %s", (number,)):
#             return None
#         return number

#     def sign_up(self, name, email, password, confirm_password):
#         """Self sign-up: validate, block duplicate emails, save an Employee login.

#         If an employee record with the same email already exists (and is not claimed by
#         another login) the new login is linked to it. Otherwise it stays unlinked and
#         no Employee record is created.

#         Raises ValueError for bad input / duplicate email, DatabaseError for DB problems.
#         Returns the new user_id.
#         """
#         name, email = validate_signup(name, email, password, confirm_password)
#         if self.email_exists(email):
#             raise ValueError("An account with this email already exists. Please sign in instead.")
#         employee_number = self.linkable_employee_number(email)   # None when there is no safe match
#         try:
#             return self.create_user(email, password, SIGNUP_ROLE, name, employee_number)
#         except DatabaseError as exc:
#             if "duplicate" in str(exc).lower():     # two people signed up at the same moment
#                 raise ValueError("An account with this email already exists. Please sign in instead.") from exc
#             raise


# """auth.py - password hashing, login lookup and role -> page access.

# No Streamlit in here, so it can be tested on its own.
# """
# import hashlib
# import hmac
# import secrets

# from db_manager import DatabaseConnection, DatabaseError
# from entities import _check_email

# ROLES = ("HR", "Manager", "Employee")
# _ITERATIONS = 200_000
# SIGNUP_ROLE = "Employee"   # self sign-up can only ever create Employee accounts

# # Which sidebar pages each role can open. Change this table to change access.
# # The names must match the page names registered in streamlit_app.py.
# PAGE_ACCESS = {
#     "HR":       ["Home", "Onboarding", "Reviews", "Analytics"],
#     "Manager":  ["Home", "Projects", "Reviews", "Analytics"],
#     "Employee": ["Home", "My Profile"],
# }


# def hash_password(password, salt=None, iterations=_ITERATIONS):
#     """Return 'pbkdf2_sha256$iterations$salt$hash' (salted, slow on purpose)."""
#     salt = salt or secrets.token_hex(16)
#     digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
#     return f"pbkdf2_sha256${iterations}${salt}${digest}"


# def verify_password(password, stored):
#     try:
#         algo, iterations, salt, digest = stored.split("$")
#         if algo != "pbkdf2_sha256":
#             return False
#         candidate = hashlib.pbkdf2_hmac(
#             "sha256", password.encode(), salt.encode(), int(iterations)).hex()
#     except (ValueError, AttributeError):
#         return False
#     return hmac.compare_digest(candidate, digest)


# _DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


# def validate_signup(name, email, password, confirm_password):
#     """Check the sign-up form. Returns (clean_name, clean_email) or raises ValueError."""
#     name = " ".join((name or "").split())
#     if len(name) < 2:
#         raise ValueError("Please enter your full name (at least 2 characters)")
#     if len(name) > 150:
#         raise ValueError("Name must be at most 150 characters")
#     email = _check_email(email)
#     password = password or ""
#     if len(password) < 8:
#         raise ValueError("Password must be at least 8 characters")
#     if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
#         raise ValueError("Password must contain at least one letter and one number")
#     if password != confirm_password:
#         raise ValueError("Passwords do not match")
#     return name, email


# class AuthManager(DatabaseConnection):
#     DB_SETTING = "OLTP_DB"

#     def authenticate(self, email, password):
#         """Return the user dict if email + password are right, otherwise None."""
#         email = (email or "").strip().lower()
#         if not email or not password:
#             return None
#         rows = self.query(
#             """SELECT user_id, email, password_hash, role, display_name, employee_number
#                FROM AppUser WHERE email = %s AND is_active = 1""", (email,))
#         stored = rows[0]["password_hash"] if rows else _DUMMY_HASH
#         ok = verify_password(password, stored)
#         if not rows or not ok:
#             return None
#         user = rows[0]
#         return {"user_id": user["user_id"], "email": user["email"], "role": user["role"],
#                 "display_name": user["display_name"], "employee_number": user["employee_number"]}

#     def create_user(self, email, password, role, display_name, employee_number=None):
#         """Add a login. Raises DatabaseError on bad input or a duplicate email."""
#         try:
#             email = _check_email(email)
#         except ValueError as exc:
#             raise DatabaseError(str(exc)) from exc
#         if role not in ROLES:
#             raise DatabaseError(f"Role must be one of {', '.join(ROLES)}")
#         if len(password or "") < 8:
#             raise DatabaseError("Password must be at least 8 characters")
#         return self.execute(
#             """INSERT INTO AppUser (email, password_hash, role, display_name, employee_number)
#                VALUES (%s, %s, %s, %s, %s)""",
#             (email, hash_password(password), role, display_name.strip(), employee_number))

#     def email_exists(self, email):
#         """True if an account (active or not) already uses this email."""
#         email = (email or "").strip().lower()
#         return bool(self.query("SELECT 1 FROM AppUser WHERE email = %s", (email,)))

#     def linkable_employee_number(self, email):
#         """Employee number whose Employee.email is EXACTLY this email, or None.

#         Returns None (so the new login stays unlinked) when no employee has that email,
#         or when another login is already linked to that employee. Nothing is guessed
#         from names, and no existing row is changed.
#         """
#         email = (email or "").strip().lower()
#         rows = self.query("SELECT employee_number FROM Employee WHERE email = %s", (email,))
#         if len(rows) != 1:
#             return None
#         number = rows[0]["employee_number"]
#         if self.query("SELECT 1 FROM AppUser WHERE employee_number = %s", (number,)):
#             return None
#         return number

#     def find_employee_for_user(self, user):
#         """Which employee record may this signed-in user see? Returns (employee_number, source).

#         The answer comes from the AppUser row in the database (found by the user_id stored
#         at login) - never from the URL, a form, or a value the browser could change.
#           1. AppUser.employee_number is set          -> (number, "linked")
#           2. it is NULL: Employee.email is EXACTLY this account's email, exactly one employee
#              has it and no other login is linked to that employee -> (number, "email")
#           3. anything else (no match, not an Employee login, inactive)  -> (None, None)
#         Read-only: nothing is written to the database.
#         """
#         if (user or {}).get("role") != "Employee":
#             return None, None
#         rows = self.query(
#             "SELECT employee_number, email FROM AppUser WHERE user_id = %s AND is_active = 1",
#             (user.get("user_id"),))
#         if not rows:
#             return None, None
#         if rows[0]["employee_number"]:
#             return int(rows[0]["employee_number"]), "linked"
#         number = self.linkable_employee_number(rows[0]["email"])
#         return (number, "email") if number else (None, None)

#     def sign_up(self, name, email, password, confirm_password):
#         """Self sign-up: validate, block duplicate emails, save an Employee login.

#         If an employee record with the same email already exists (and is not claimed by
#         another login) the new login is linked to it. Otherwise it stays unlinked and
#         no Employee record is created.

#         Raises ValueError for bad input / duplicate email, DatabaseError for DB problems.
#         Returns the new user_id.
#         """
#         name, email = validate_signup(name, email, password, confirm_password)
#         if self.email_exists(email):
#             raise ValueError("An account with this email already exists. Please sign in instead.")
#         employee_number = self.linkable_employee_number(email)   # None when there is no safe match
#         try:
#             return self.create_user(email, password, SIGNUP_ROLE, name, employee_number)
#         except DatabaseError as exc:
#             if "duplicate" in str(exc).lower():     # two people signed up at the same moment
#                 raise ValueError("An account with this email already exists. Please sign in instead.") from exc
#             raise

"""auth.py - password hashing, login lookup and role -> page access.

No Streamlit in here, so it can be tested on its own.
"""
import hashlib
import hmac
import secrets

from db_manager import DatabaseConnection, DatabaseError
from entities import _check_email

ROLES = ("HR", "Manager", "Employee")
_ITERATIONS = 200_000
SIGNUP_ROLE = "Employee"   # self sign-up can only ever create Employee accounts

# Which sidebar pages each role can open. Change this table to change access.
# The names must match the page names registered in streamlit_app.py.
PAGE_ACCESS = {
    "HR":       ["Home", "Onboarding", "Reviews", "Analytics"],
    "Manager":  ["Home", "Employee Directory", "Projects", "Reviews", "Analytics"],
    "Employee": ["Home", "My Profile"],
}


def hash_password(password, salt=None, iterations=_ITERATIONS):
    """Return 'pbkdf2_sha256$iterations$salt$hash' (salted, slow on purpose)."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password, stored):
    try:
        algo, iterations, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(iterations)).hex()
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(candidate, digest)


_DUMMY_HASH = hash_password("not-a-real-password")   # used so unknown emails take the same time


def validate_signup(name, email, password, confirm_password):
    """Check the sign-up form. Returns (clean_name, clean_email) or raises ValueError."""
    name = " ".join((name or "").split())
    if len(name) < 2:
        raise ValueError("Please enter your full name (at least 2 characters)")
    if len(name) > 150:
        raise ValueError("Name must be at most 150 characters")
    email = _check_email(email)
    password = password or ""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one letter and one number")
    if password != confirm_password:
        raise ValueError("Passwords do not match")
    return name, email


class AuthManager(DatabaseConnection):
    DB_SETTING = "OLTP_DB"

    def authenticate(self, email, password):
        """Return the user dict if email + password are right, otherwise None."""
        email = (email or "").strip().lower()
        if not email or not password:
            return None
        rows = self.query(
            """SELECT user_id, email, password_hash, role, display_name, employee_number
               FROM AppUser WHERE email = %s AND is_active = 1""", (email,))
        stored = rows[0]["password_hash"] if rows else _DUMMY_HASH
        ok = verify_password(password, stored)
        if not rows or not ok:
            return None
        user = rows[0]
        return {"user_id": user["user_id"], "email": user["email"], "role": user["role"],
                "display_name": user["display_name"], "employee_number": user["employee_number"]}

    def create_user(self, email, password, role, display_name, employee_number=None):
        """Add a login. Raises DatabaseError on bad input or a duplicate email."""
        try:
            email = _check_email(email)
        except ValueError as exc:
            raise DatabaseError(str(exc)) from exc
        if role not in ROLES:
            raise DatabaseError(f"Role must be one of {', '.join(ROLES)}")
        if len(password or "") < 8:
            raise DatabaseError("Password must be at least 8 characters")
        return self.execute(
            """INSERT INTO AppUser (email, password_hash, role, display_name, employee_number)
               VALUES (%s, %s, %s, %s, %s)""",
            (email, hash_password(password), role, display_name.strip(), employee_number))

    def email_exists(self, email):
        """True if an account (active or not) already uses this email."""
        email = (email or "").strip().lower()
        return bool(self.query("SELECT 1 FROM AppUser WHERE email = %s", (email,)))

    def linkable_employee_number(self, email):
        """Employee number whose Employee.email is EXACTLY this email, or None.

        Returns None (so the new login stays unlinked) when no employee has that email,
        or when another login is already linked to that employee. Nothing is guessed
        from names, and no existing row is changed.
        """
        email = (email or "").strip().lower()
        rows = self.query("SELECT employee_number FROM Employee WHERE email = %s", (email,))
        if len(rows) != 1:
            return None
        number = rows[0]["employee_number"]
        if self.query("SELECT 1 FROM AppUser WHERE employee_number = %s", (number,)):
            return None
        return number

    def find_employee_for_user(self, user):
        """Which employee record may this signed-in user see? Returns (employee_number, source).

        The answer comes from the AppUser row in the database (found by the user_id stored
        at login) - never from the URL, a form, or a value the browser could change.
          1. AppUser.employee_number is set          -> (number, "linked")
          2. it is NULL: Employee.email is EXACTLY this account's email, exactly one employee
             has it and no other login is linked to that employee -> (number, "email")
          3. anything else (no match, not an Employee login, inactive)  -> (None, None)
        Read-only: nothing is written to the database.
        """
        if (user or {}).get("role") != "Employee":
            return None, None
        rows = self.query(
            "SELECT employee_number, email FROM AppUser WHERE user_id = %s AND is_active = 1",
            (user.get("user_id"),))
        if not rows:
            return None, None
        if rows[0]["employee_number"]:
            return int(rows[0]["employee_number"]), "linked"
        number = self.linkable_employee_number(rows[0]["email"])
        return (number, "email") if number else (None, None)

    def sign_up(self, name, email, password, confirm_password):
        """Self sign-up: validate, block duplicate emails, save an Employee login.

        If an employee record with the same email already exists (and is not claimed by
        another login) the new login is linked to it. Otherwise it stays unlinked and
        no Employee record is created.

        Raises ValueError for bad input / duplicate email, DatabaseError for DB problems.
        Returns the new user_id.
        """
        name, email = validate_signup(name, email, password, confirm_password)
        if self.email_exists(email):
            raise ValueError("An account with this email already exists. Please sign in instead.")
        employee_number = self.linkable_employee_number(email)   # None when there is no safe match
        try:
            return self.create_user(email, password, SIGNUP_ROLE, name, employee_number)
        except DatabaseError as exc:
            if "duplicate" in str(exc).lower():     # two people signed up at the same moment
                raise ValueError("An account with this email already exists. Please sign in instead.") from exc
            raise
