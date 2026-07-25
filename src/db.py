import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "volteyr.db")

_connection = None

def get_connection():
    global _connection
    if _connection is None:
        _connection = duckdb.connect(DB_PATH)
        _init_schema(_connection)
    return _connection

def _init_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id BIGINT PRIMARY KEY,
            product_type VARCHAR,
            category VARCHAR,
            product_tags VARCHAR,
            images_array VARCHAR,
            vendor VARCHAR,
            inventory_quantity BIGINT,
            gross_amount_exc_tax_product DOUBLE,
            description VARCHAR
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enrichissements (
            product_id BIGINT PRIMARY KEY,
            enriched_description VARCHAR,
            material VARCHAR,
            care_instructions VARCHAR,
            style VARCHAR,
            seo_keywords VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used VARCHAR
        )
    """)

def close():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
