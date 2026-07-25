import csv
import os

from db import get_connection, close
from normalize_types import normalize_product_type

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.csv")

def parse_and_load():
    conn = get_connection()

    conn.execute("DELETE FROM products")

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            raw_type = row["product_type"]
            rows.append((
                int(row["product_id"]),
                raw_type,
                normalize_product_type(raw_type),
                row["product_tags"],
                row["images_array"],
                row["vendor"],
                int(row["inventory_quantity"]),
                float(row["gross_amount_exc_tax_product"]),
                row["description"],
            ))

    conn.executemany(
        """INSERT INTO products (
            product_id, product_type, category, product_tags, images_array,
            vendor, inventory_quantity, gross_amount_exc_tax_product, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )

    print(f"✅ {len(rows)} produits chargés dans products")

if __name__ == "__main__":
    parse_and_load()
    close()
