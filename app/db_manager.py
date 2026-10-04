# """db_manager.py - Singleton MySQL connection manager.

# Design notes (good points to mention in your viva / documentation):
#   * Singleton: each connection class is created ONCE per process; every call to
#     ``EmployeeManager()`` returns the same object and reuses the same connection.
#     OLTP managers and the OLAP manager are separate singletons because they use
#     different databases.
#   * Thread-safe: Streamlit runs each user session in its own thread, so every
#     operation takes an RLock before touching the shared connection.
#   * autocommit=True for reads (no stale snapshots on a long-lived connection),
#     explicit transactions for multi-step writes via ``transaction()``.
#   * Credentials come from environment variables / .env / Streamlit secrets -
#     never from the source code.
# """
# import os
# import threading
# from decimal import Decimal
# from contextlib import contextmanager

# import mysql.connector
# import pandas as pd
# from mysql.connector import Error as MySQLError

# try:  # .env support for local development
#     from dotenv import load_dotenv
#     load_dotenv()
# except ImportError:  # pragma: no cover
#     pass


# class DatabaseError(Exception):
#     """Single exception type the UI layer needs to catch."""


# def get_setting(name, default=None):
#     """Read a setting from env vars first, then Streamlit secrets (cloud)."""
#     value = os.getenv(name)
#     if value:
#         return value
#     try:
#         import streamlit as st
#         if name in st.secrets:
#             return str(st.secrets[name])
#     except Exception:
#         pass
#     return default


# class DatabaseConnection:
#     """Base class: one shared connection per subclass (Singleton)."""

#     _instances = {}
#     _creation_lock = threading.Lock()
#     DB_SETTING = "OLTP_DB"          # subclasses override: which setting names the schema
#     DB_DEFAULT = "enterprise_employee_analytics"

#     def __new__(cls, *args, **kwargs):
#         with DatabaseConnection._creation_lock:
#             if cls not in DatabaseConnection._instances:
#                 instance = super().__new__(cls)
#                 instance._initialized = False
#                 DatabaseConnection._instances[cls] = instance
#         return DatabaseConnection._instances[cls]

#     def __init__(self):
#         if self._initialized:          # __init__ runs on every ClassName() call
#             return
#         self._config = {
#             "host": get_setting("MYSQL_HOST", "localhost"),
#             "port": int(get_setting("MYSQL_PORT", "3306")),
#             "user": get_setting("MYSQL_USER", "root"),
#             "password": get_setting("MYSQL_PASSWORD", ""),
#             "database": get_setting(self.DB_SETTING, self.DB_DEFAULT),
#             "connection_timeout": 10,
#         }
#         ssl_ca = get_setting("MYSQL_SSL_CA")      # hosted MySQL (Aiven, etc.)
#         if ssl_ca:
#             self._config["ssl_ca"] = ssl_ca
#         self._conn = None
#         self._lock = threading.RLock()
#         self._initialized = True

#     # ------------------------------------------------------------------ helpers
#     @property
#     def database_name(self):
#         return self._config["database"]

#     def _get_connection(self):
#         try:
#             if self._conn is None or not self._conn.is_connected():
#                 self._conn = mysql.connector.connect(autocommit=True, **self._config)
#             else:
#                 self._conn.ping(reconnect=True, attempts=2, delay=1)
#         except MySQLError as exc:
#             raise DatabaseError(f"Could not connect to MySQL ({self.database_name}): {exc}") from exc
#         return self._conn

#     # ------------------------------------------------------------------ public API
#     def test_connection(self):
#         """Return (ok, message) - used by the home page status panel."""
#         try:
#             rows = self.query("SELECT DATABASE() AS db, VERSION() AS version")
#             return True, f"{rows[0]['db']} (MySQL {rows[0]['version']})"
#         except DatabaseError as exc:
#             return False, str(exc)

#     def query(self, sql, params=None):
#         """SELECT -> list of dicts."""
#         with self._lock:
#             try:
#                 cur = self._get_connection().cursor(dictionary=True)
#                 try:
#                     cur.execute(sql, params or ())
#                     return cur.fetchall()
#                 finally:
#                     cur.close()
#             except MySQLError as exc:
#                 raise DatabaseError(f"Query failed: {exc.msg if hasattr(exc, 'msg') else exc}") from exc

#     def query_df(self, sql, params=None):
#         """SELECT -> pandas DataFrame (used by the dashboards)."""
#         df = pd.DataFrame(self.query(sql, params))
#         for col in df.columns:      # MySQL returns SUM()/AVG() as Decimal -> make real numbers
#             if df[col].dtype == object and df[col].notna().any() \
#                     and df[col].dropna().map(lambda v: isinstance(v, Decimal)).all():
#                 df[col] = df[col].astype(float)
#         return df

#     def execute(self, sql, params=None):
#         """Single INSERT/UPDATE/DELETE (auto-committed). Returns lastrowid."""
#         with self._lock:
#             try:
#                 cur = self._get_connection().cursor()
#                 try:
#                     cur.execute(sql, params or ())
#                     return cur.lastrowid
#                 finally:
#                     cur.close()
#             except MySQLError as exc:
#                 raise DatabaseError(f"Statement failed: {exc.msg if hasattr(exc, 'msg') else exc}") from exc

#     @contextmanager
#     def transaction(self):
#         """All-or-nothing block:

#             with self.transaction() as cur:
#                 cur.execute(...)
#                 cur.execute(...)
#         Commits on success, rolls everything back on any error.
#         """
#         with self._lock:
#             conn = self._get_connection()
#             cur = None
#             try:
#                 conn.start_transaction()
#                 cur = conn.cursor(dictionary=True, buffered=True)
#                 yield cur
#                 conn.commit()
#             except MySQLError as exc:
#                 conn.rollback()
#                 raise DatabaseError(f"Transaction rolled back: {exc.msg if hasattr(exc, 'msg') else exc}") from exc
#             except Exception:
#                 conn.rollback()
#                 raise
#             finally:
#                 if cur is not None:
#                     cur.close()

#     def close(self):
#         with self._lock:
#             if self._conn is not None and self._conn.is_connected():
#                 self._conn.close()
#             self._conn = None
"""db_manager.py - Singleton MySQL connection manager.

Design notes (good points to mention in your viva / documentation):
  * Singleton: each connection class is created ONCE per process; every call to
    ``EmployeeManager()`` returns the same object and reuses the same connection.
    OLTP managers and the OLAP manager are separate singletons because they use
    different databases.
  * Thread-safe: Streamlit runs each user session in its own thread, so every
    operation takes an RLock before touching the shared connection.
  * autocommit=True for reads (no stale snapshots on a long-lived connection),
    explicit transactions for multi-step writes via ``transaction()``.
  * Credentials come from environment variables / .env / Streamlit secrets -
    never from the source code.
"""
import os
import threading
from decimal import Decimal
from contextlib import contextmanager

import mysql.connector
import pandas as pd
from mysql.connector import Error as MySQLError

try:  # .env support for local development
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


class DatabaseError(Exception):
    """Single exception type the UI layer needs to catch."""


def get_setting(name, default=None):
    """Read a setting from env vars first, then Streamlit secrets (cloud)."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


class DatabaseConnection:
    """Base class: one shared connection per subclass (Singleton)."""

    _instances = {}
    _creation_lock = threading.Lock()
    DB_SETTING = "OLTP_DB"          # subclasses override: which setting names the schema
    DB_DEFAULT = "enterprise_employee_analytics"

    def __new__(cls, *args, **kwargs):
        with DatabaseConnection._creation_lock:
            if cls not in DatabaseConnection._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                DatabaseConnection._instances[cls] = instance
        return DatabaseConnection._instances[cls]

    def __init__(self):
        if self._initialized:          # __init__ runs on every ClassName() call
            return
        self._config = {
            "host": get_setting("MYSQL_HOST", "localhost"),
            "port": int(get_setting("MYSQL_PORT", "3306")),
            "user": get_setting("MYSQL_USER", "root"),
            "password": get_setting("MYSQL_PASSWORD", ""),
            "database": get_setting(self.DB_SETTING, self.DB_DEFAULT),
            "connection_timeout": 10,
        }
        ssl_ca = get_setting("MYSQL_SSL_CA")      # hosted MySQL (Aiven, etc.)
        if ssl_ca:
            if not os.path.isabs(ssl_ca) and not os.path.exists(ssl_ca):
                # relative path (e.g. "ca.pem"): also look in the repo root, wherever the app was started
                repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
                candidate = os.path.abspath(os.path.join(repo_root, ssl_ca))
                if os.path.exists(candidate):
                    ssl_ca = candidate
            self._config["ssl_ca"] = ssl_ca
        self._conn = None
        self._lock = threading.RLock()
        self._initialized = True

    # ------------------------------------------------------------------ helpers
    @property
    def database_name(self):
        return self._config["database"]

    def _get_connection(self):
        try:
            if self._conn is None or not self._conn.is_connected():
                self._conn = mysql.connector.connect(autocommit=True, **self._config)
            else:
                self._conn.ping(reconnect=True, attempts=2, delay=1)
        except MySQLError as exc:
            raise DatabaseError(f"Could not connect to MySQL ({self.database_name}): {exc}") from exc
        return self._conn

    # ------------------------------------------------------------------ public API
    def test_connection(self):
        """Return (ok, message) - used by the home page status panel."""
        try:
            rows = self.query("SELECT DATABASE() AS db, VERSION() AS version")
            return True, f"{rows[0]['db']} (MySQL {rows[0]['version']})"
        except DatabaseError as exc:
            return False, str(exc)

    def query(self, sql, params=None):
        """SELECT -> list of dicts."""
        with self._lock:
            try:
                cur = self._get_connection().cursor(dictionary=True)
                try:
                    cur.execute(sql, params or ())
                    return cur.fetchall()
                finally:
                    cur.close()
            except MySQLError as exc:
                raise DatabaseError(f"Query failed: {exc.msg if hasattr(exc, 'msg') else exc}") from exc

    def query_df(self, sql, params=None):
        """SELECT -> pandas DataFrame (used by the dashboards)."""
        df = pd.DataFrame(self.query(sql, params))
        for col in df.columns:      # MySQL returns SUM()/AVG() as Decimal -> make real numbers
            if df[col].dtype == object and df[col].notna().any() \
                    and df[col].dropna().map(lambda v: isinstance(v, Decimal)).all():
                df[col] = df[col].astype(float)
        return df

    def execute(self, sql, params=None):
        """Single INSERT/UPDATE/DELETE (auto-committed). Returns lastrowid."""
        with self._lock:
            try:
                cur = self._get_connection().cursor()
                try:
                    cur.execute(sql, params or ())
                    return cur.lastrowid
                finally:
                    cur.close()
            except MySQLError as exc:
                raise DatabaseError(f"Statement failed: {exc.msg if hasattr(exc, 'msg') else exc}") from exc

    @contextmanager
    def transaction(self):
        """All-or-nothing block:

            with self.transaction() as cur:
                cur.execute(...)
                cur.execute(...)
        Commits on success, rolls everything back on any error.
        """
        with self._lock:
            conn = self._get_connection()
            cur = None
            try:
                conn.start_transaction()
                cur = conn.cursor(dictionary=True, buffered=True)
                yield cur
                conn.commit()
            except MySQLError as exc:
                conn.rollback()
                raise DatabaseError(f"Transaction rolled back: {exc.msg if hasattr(exc, 'msg') else exc}") from exc
            except Exception:
                conn.rollback()
                raise
            finally:
                if cur is not None:
                    cur.close()

    def close(self):
        with self._lock:
            if self._conn is not None and self._conn.is_connected():
                self._conn.close()
            self._conn = None