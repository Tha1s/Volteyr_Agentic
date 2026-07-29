import threading
from pathlib import Path

import sqlite3

DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "volteyr.db")
_local = threading.local()
_override_conn = None


def set_connection(conn):
    global _override_conn
    _override_conn = conn


def reset_connection():
    global _override_conn
    _override_conn = None


def get_connection():
    if _override_conn is not None:
        return _override_conn
    if not hasattr(_local, "connection") or _local.connection is None:
        try:
            _local.connection = sqlite3.connect(DB_PATH, timeout=10)
            _local.connection.execute("PRAGMA journal_mode=WAL")
            _local.connection.execute("PRAGMA foreign_keys=ON")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}") from e
    return _local.connection


def close():
    if _override_conn is not None:
        return
    if hasattr(_local, "connection") and _local.connection is not None:
        _local.connection.close()
        _local.connection = None
