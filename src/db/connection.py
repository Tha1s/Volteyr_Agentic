import duckdb


_connection = None


def get_connection():
    global _connection
    if _connection is None:
        _connection = duckdb.connect("data/volteyr.db")
    return _connection


def close():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
