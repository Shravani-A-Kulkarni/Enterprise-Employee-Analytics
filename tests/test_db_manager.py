from contextlib import contextmanager
from decimal import Decimal
import sys
from unittest.mock import MagicMock

import db_manager
from db_manager import DatabaseConnection, DatabaseError, get_setting
import pandas as pd
import pytest
from mysql.connector import Error as MySQLError

from db_manager import DatabaseConnection, DatabaseError, get_setting


class FakeCursor:
    def __init__(self, rows=None, lastrowid=1, error=None):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.error = error
        self.executed = None
        self.closed = False

    def execute(self, sql, params=()):
        self.executed = (sql, params)
        if self.error:
            raise self.error

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows=None, error=None):
        self.cursor_obj = FakeCursor(rows=rows, error=error)
        self.commits = 0
        self.rollbacks = 0
        self.started = 0
        self.closed = False

    def cursor(self, **kwargs):
        return self.cursor_obj

    def is_connected(self):
        return True

    def ping(self, **kwargs):
        return None

    def start_transaction(self):
        self.started += 1

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def make_manager(monkeypatch, rows=None, error=None):
    manager = DatabaseConnection()
    manager._conn = FakeConnection(rows=rows, error=error)
    monkeypatch.setattr(manager, "_get_connection", lambda: manager._conn)
    return manager


def test_get_setting_prefers_environment(monkeypatch):
    monkeypatch.setenv("SAMPLE_SETTING", "from-env")
    assert get_setting("SAMPLE_SETTING", "default") == "from-env"


def test_get_setting_uses_default_when_missing(monkeypatch):
    monkeypatch.delenv("SAMPLE_SETTING", raising=False)
    assert get_setting("SAMPLE_SETTING", "fallback") == "fallback"


def test_query_returns_rows(monkeypatch):
    manager = make_manager(monkeypatch, rows=[{"id": 1}])
    assert manager.query("SELECT 1") == [{"id": 1}]


def test_execute_returns_lastrowid(monkeypatch):
    manager = make_manager(monkeypatch)
    assert manager.execute("INSERT INTO t VALUES (%s)", (1,)) == 1


def test_query_wraps_mysql_error(monkeypatch):
    manager = make_manager(monkeypatch, error=MySQLError(msg="query failed"))
    with pytest.raises(DatabaseError, match="Query failed"):
        manager.query("SELECT 1")


def test_execute_wraps_mysql_error(monkeypatch):
    manager = make_manager(monkeypatch, error=MySQLError(msg="write failed"))
    with pytest.raises(DatabaseError, match="Statement failed"):
        manager.execute("INSERT INTO t VALUES (1)")


def test_query_df_converts_decimal_columns_to_float(monkeypatch):
    manager = make_manager(monkeypatch, rows=[{"amount": Decimal("10.50"), "label": "x"}])
    result = manager.query_df("SELECT amount, label")
    assert isinstance(result, pd.DataFrame)
    assert result.loc[0, "amount"] == 10.5
    assert result["amount"].dtype == float


def test_test_connection_success(monkeypatch):
    manager = make_manager(monkeypatch, rows=[{"db": "test_db", "version": "8.0"}])
    ok, message = manager.test_connection()
    assert ok is True
    assert "test_db" in message


def test_test_connection_failure(monkeypatch):
    manager = make_manager(monkeypatch)
    monkeypatch.setattr(manager, "query", lambda *args: (_ for _ in ()).throw(DatabaseError("offline")))
    ok, message = manager.test_connection()
    assert ok is False
    assert "offline" in message


def test_close_resets_connection(monkeypatch):
    manager = make_manager(monkeypatch)
    conn = manager._conn
    manager.close()
    assert conn.closed is True
    assert manager._conn is None


def test_transaction_commits_on_success(monkeypatch):
    manager = make_manager(monkeypatch)
    conn = manager._conn
    with manager.transaction() as cursor:
        cursor.execute("UPDATE t SET x = %s", (2,))
    assert conn.started == 1
    assert conn.commits == 1
    assert conn.rollbacks == 0


def test_transaction_rolls_back_mysql_error(monkeypatch):
    manager = make_manager(monkeypatch)
    conn = manager._conn
    manager._conn.cursor_obj.error = MySQLError(msg="broken")
    with pytest.raises(DatabaseError, match="Transaction rolled back"):
        with manager.transaction() as cursor:
            cursor.execute("UPDATE t SET x = 1")
    assert conn.rollbacks == 1
    assert conn.commits == 0


def test_transaction_rolls_back_other_error(monkeypatch):
    manager = make_manager(monkeypatch)
    conn = manager._conn
    with pytest.raises(RuntimeError):
        with manager.transaction():
            raise RuntimeError("boom")
    assert conn.rollbacks == 1
    assert conn.commits == 0

def test_get_connection_creates_connection_when_missing(monkeypatch):
    manager = DatabaseConnection()
    manager._conn = None
    connect = MagicMock()
    fake_conn = MagicMock()
    fake_conn.is_connected.return_value = True
    connect.return_value = fake_conn

    monkeypatch.setattr(db_manager.mysql.connector, "connect", connect)

    result = manager._get_connection()

    assert result is fake_conn
    connect.assert_called_once_with(autocommit=True, **manager._config)


def test_get_connection_pings_existing_connection(monkeypatch):
    manager = DatabaseConnection()
    fake_conn = MagicMock()
    fake_conn.is_connected.return_value = True
    manager._conn = fake_conn

    connect = MagicMock()
    monkeypatch.setattr(db_manager.mysql.connector, "connect", connect)

    assert manager._get_connection() is fake_conn
    fake_conn.ping.assert_called_once_with(
        reconnect=True, attempts=2, delay=1
    )
    connect.assert_not_called()


def test_get_connection_wraps_mysql_error(monkeypatch):
    manager = DatabaseConnection()
    manager._conn = None

    monkeypatch.setattr(
        db_manager.mysql.connector,
        "connect",
        MagicMock(side_effect=db_manager.MySQLError("connection failed")),
    )

    with pytest.raises(DatabaseError, match="Could not connect to MySQL"):
        manager._get_connection()


def test_get_setting_uses_streamlit_secret(monkeypatch):
    monkeypatch.delenv("TEST_DB_SETTING", raising=False)

    fake_streamlit = MagicMock()
    fake_streamlit.secrets = {"TEST_DB_SETTING": "secret_value"}

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    assert get_setting("TEST_DB_SETTING") == "secret_value"


def test_get_setting_returns_default_when_secrets_fail(monkeypatch):
    monkeypatch.delenv("TEST_DB_SETTING", raising=False)

    
    

    class FakeStreamlit:
        @property
        def secrets(self):
            raise RuntimeError("No secrets")

    monkeypatch.setitem(sys.modules, "streamlit", FakeStreamlit())

    assert get_setting("TEST_DB_SETTING", "fallback") == "fallback"


def test_close_without_connection(monkeypatch):
    manager = DatabaseConnection()
    manager._conn = None

    manager.close()

    assert manager._conn is None


def test_transaction_closes_cursor_after_success(monkeypatch):
    manager = DatabaseConnection()
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(manager, "_get_connection", lambda: fake_conn)

    with manager.transaction() as cursor:
        assert cursor is fake_cursor

    fake_conn.commit.assert_called_once()
    fake_conn.rollback.assert_not_called()
    fake_cursor.close.assert_called_once()


def test_transaction_closes_cursor_after_mysql_error(monkeypatch):
    manager = DatabaseConnection()
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(manager, "_get_connection", lambda: fake_conn)

    with pytest.raises(DatabaseError, match="Transaction rolled back"):
        with manager.transaction() as cursor:
            raise db_manager.MySQLError("transaction failed")

    fake_conn.rollback.assert_called_once()
    fake_conn.commit.assert_not_called()
    fake_cursor.close.assert_called_once()
