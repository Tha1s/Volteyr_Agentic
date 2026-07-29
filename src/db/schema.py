from src.db.connection import get_connection


def init_schema():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_type TEXT,
            category TEXT,
            product_tags TEXT,
            images_array TEXT,
            vendor TEXT,
            inventory_quantity INTEGER,
            gross_amount_exc_tax_product REAL,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enrichissements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            enriched_description TEXT,
            material TEXT,
            care_instructions TEXT,
            style TEXT,
            seo_keywords TEXT,
            model_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    conn.commit()
