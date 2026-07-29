import csv

from src.config.categories import normalize_product_type, load_category_map, auto_fill_categories
from src.db.connection import get_connection


def load_csv_from_dictreader(reader: csv.DictReader) -> int:
    raw_rows = list(reader)

    required_cols = {
        "product_id", "product_type", "product_tags", "images_array",
        "vendor", "inventory_quantity", "gross_amount_exc_tax_product", "description",
    }
    if not required_cols.issubset(reader.fieldnames or []):
        missing = required_cols - set(reader.fieldnames or [])
        raise ValueError(f"Colonnes manquantes: {missing}")

    types = {r["product_type"].strip() for r in raw_rows if r.get("product_type", "").strip()}
    auto_fill_categories(types)

    mapping = load_category_map()
    rows = []
    for row in raw_rows:
        raw_type = row["product_type"]
        category = normalize_product_type(raw_type, mapping)
        try:
            product_id = int(row["product_id"])
            inventory = int(row["inventory_quantity"])
            price = float(row["gross_amount_exc_tax_product"])
        except (ValueError, KeyError) as e:
            print(f"Skipping row with invalid data: {e}")
            continue
        rows.append((
            product_id,
            row["product_type"],
            category,
            row["product_tags"],
            row["images_array"],
            row["vendor"],
            inventory,
            price,
            row["description"],
        ))

    conn = get_connection()
    conn.executemany(
        """INSERT OR REPLACE INTO products (product_id, product_type, category, product_tags, images_array, vendor, inventory_quantity, gross_amount_exc_tax_product, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return len(rows)
