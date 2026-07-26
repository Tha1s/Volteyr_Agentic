import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db.connection import get_connection
from src.db.schema import init_schema
from src.config.categories import normalize_product_type, load_category_map, auto_fill_categories


def parse_and_load(csv_path: str = "data/products.csv"):
    conn = get_connection()
    init_schema()
    conn.execute("DELETE FROM enrichissements")
    conn.execute("DELETE FROM products")

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    types = {r["product_type"].strip() for r in raw_rows if r.get("product_type", "").strip()}
    auto_fill_categories(types)

    mapping = load_category_map()
    rows = []
    for row in raw_rows:
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
