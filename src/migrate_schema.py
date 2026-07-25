import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "volteyr.db")

def migrate():
    conn = duckdb.connect(DB_PATH)
    
    for col in [
        "enriched_description VARCHAR",
        "material VARCHAR",
        "care_instructions VARCHAR",
        "style VARCHAR",
        "seo_keywords VARCHAR",
        "enriched_at TIMESTAMP",
        "model_used VARCHAR",
    ]:
        conn.execute(f"ALTER TABLE products ADD COLUMN IF NOT EXISTS {col}")
    
    tables = [r[0] for r in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'enrichissements'").fetchall()]
    if tables:
        n = conn.execute("SELECT COUNT(*) FROM enrichissements").fetchone()[0]
        if n > 0:
            conn.execute("""
                UPDATE products SET
                    enriched_description = e.enriched_description,
                    material = e.material,
                    care_instructions = e.care_instructions,
                    style = e.style,
                    seo_keywords = e.seo_keywords,
                    enriched_at = e.created_at,
                    model_used = e.model_used
                FROM enrichissements e
                WHERE products.product_id = e.product_id
            """)
        conn.execute("DROP TABLE enrichissements")
    
    conn.commit()
    conn.close()
    print("Migration terminée")

if __name__ == "__main__":
    migrate()
