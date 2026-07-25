import csv
import os

from db import get_connection, close

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.csv")

def parse_and_load():
    conn = get_connection()

    conn.execute("DELETE FROM products")

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append((
                int(row["product_id"]),
                row["product_type"],
                row["product_tags"],
                row["images_array"],
                row["vendor"],
                int(row["inventory_quantity"]),
                float(row["gross_amount_exc_tax_product"]),
                row["description"],
            ))

    conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

    print(f"✅ {len(rows)} produits chargés dans products")

    count_enrich = conn.execute("SELECT COUNT(*) FROM enrichissements").fetchone()[0]
    print(f"📦 enrichissements : {count_enrich} lignes")

if __name__ == "__main__":
    parse_and_load()
    close()
