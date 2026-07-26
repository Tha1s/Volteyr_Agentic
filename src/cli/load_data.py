import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db.connection import get_connection
from src.db.schema import init_schema
from src.config.categories import normalize_product_type, load_category_map


def parse_and_load(csv_path: str = "data/products.csv"):
    conn = get_connection()
    init_schema()
    conn.execute("DELETE FROM products")

    mapping = load_category_map()
    rows = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_type = row["product_type"]
            category = normalize_product_type(raw_type, mapping)
            product_id = int(row["product_id"])
            rows.append((
                product_id,
                row["product_type"],
                category,
                row["product_tags"],
                row["images_array"],
                row["vendor"],
                int(row["inventory_quantity"]),
                float(row["gross_amount_exc_tax_product"]),
                row["description"],
            ))

    conn.executemany(
        """INSERT INTO products (product_id, product_type, category, product_tags, images_array, vendor, inventory_quantity, gross_amount_exc_tax_product, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    print(f"✅ {len(rows)} products loaded")


if __name__ == "__main__":
    parse_and_load()
