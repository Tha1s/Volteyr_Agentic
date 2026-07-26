if __name__ == "__main__":
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import csv

from src.db.loader import load_csv_from_dictreader
from src.db.schema import init_schema


def parse_and_load(csv_path: str = "data/products.csv"):
    init_schema()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = load_csv_from_dictreader(reader)
    print(f"✅ {count} products loaded")


if __name__ == "__main__":
    parse_and_load()
