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

# Which sidebar pages each role can open. Change this table to change access.
# The names must match the page names registered in streamlit_app.py.
PAGE_ACCESS = {
    "HR":       ["Home", "Onboarding", "Projects", "Reviews", "Analytics"],
    "Manager":  ["Home", "Projects", "Reviews", "Analytics"],
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
