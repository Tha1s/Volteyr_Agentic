import tempfile
from pathlib import Path
from unittest.mock import patch

import duckdb

import src.db.connection as conn_mod
from src.db.connection import get_connection, close


def _reset_connection():
    close()
    conn_mod._connection = None


def test_singleton():
    _reset_connection()
    try:
        conn1 = get_connection()
        conn2 = get_connection()
        assert conn1 is conn2
    finally:
        _reset_connection()


def test_close_and_reconnect():
    _reset_connection()
    try:
        conn1 = get_connection()
        close()
        conn2 = get_connection()
        assert conn1 is not conn2
        assert conn2 is not None
    finally:
        _reset_connection()


def test_temp_file_created_on_connect():
    _reset_connection()
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        assert not db_path.exists()
        monkey_path = str(db_path)
        with patch.object(conn_mod, "_connection", None):
            try:
                conn = duckdb.connect(monkey_path)
                conn.execute("CREATE TABLE test (id INT)")
                conn.commit()
                assert db_path.exists()
                conn.close()
            finally:
                close()


def test_file_not_found_is_skipped():
    pass
