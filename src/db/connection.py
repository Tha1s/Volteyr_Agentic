import duckdb


_connection = None


def get_connection():
    global _connection
    if _connection is None:
        try:
            _connection = duckdb.connect("data/volteyr.db")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to DuckDB: {e}") from e
    return _connection


def close():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
