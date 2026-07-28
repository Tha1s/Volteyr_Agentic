import threading
from pathlib import Path

import duckdb

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
            _local.connection = duckdb.connect(DB_PATH)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to DuckDB: {e}") from e
    return _local.connection


def close():
    if _override_conn is not None:
        return
    if hasattr(_local, "connection") and _local.connection is not None:
        _local.connection.close()
        _local.connection = None
