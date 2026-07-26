from src.db.connection import get_connection


class ProductRepository:
    def __init__(self):
        self.conn = get_connection()

    def count_all(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    def count_empty(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE description IS NULL OR description = ''"
        ).fetchone()[0]

    def count_short(self, threshold: int = 50) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE LENGTH(description) > 0 AND LENGTH(description) < ?",
            [threshold],
        ).fetchone()[0]

    def count_medium(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 50 AND LENGTH(description) < 200"
        ).fetchone()[0]

    def count_long(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 200 AND LENGTH(description) < 500"
        ).fetchone()[0]

    def count_very_long(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE LENGTH(description) >= 500"
        ).fetchone()[0]

    def count_by_category(self) -> list[tuple[str, int]]:
        return self.conn.execute(
            "SELECT category, COUNT(*) AS cnt FROM products GROUP BY category ORDER BY cnt DESC"
        ).fetchall()

    def count_by_vendor(self) -> list[tuple[str, int]]:
        return self.conn.execute(
            "SELECT vendor, COUNT(*) AS cnt FROM products GROUP BY vendor ORDER BY cnt DESC"
        ).fetchall()

    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        return self.conn.execute(
            "SELECT * FROM products ORDER BY product_id LIMIT ? OFFSET ?", [limit, offset]
        ).fetchdf().to_dict("records")

    def find_by_id(self, product_id: int) -> dict | None:
        result = self.conn.execute(
            "SELECT * FROM products WHERE product_id = ?", [product_id]
        ).fetchdf()
        if result.empty:
            return None
        return result.to_dict("records")[0]

    def find_by_ids(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        return self.conn.execute(
            f"SELECT * FROM products WHERE product_id IN ({placeholders}) ORDER BY product_id",
            ids,
        ).fetchdf().to_dict("records")

    def find_filtered(
        self,
        quality: str | None = None,
        categories: list[str] | None = None,
        vendors: list[str] | None = None,
    ) -> list[dict]:
        conditions = []
        params = []

        if quality is not None:
            if quality == "Vide":
                conditions.append("(description IS NULL OR description = '')")
            elif quality == "<50c":
                conditions.append("(description IS NOT NULL AND description != '' AND LENGTH(description) < 50)")
            elif quality == "50-200c":
                conditions.append("(description IS NOT NULL AND description != '' AND LENGTH(description) >= 50 AND LENGTH(description) < 200)")
            elif quality == "200-500c":
                conditions.append("(description IS NOT NULL AND description != '' AND LENGTH(description) >= 200 AND LENGTH(description) < 500)")
            elif quality == ">500c":
                conditions.append("(description IS NOT NULL AND description != '' AND LENGTH(description) >= 500)")

        if categories:
            placeholders = ",".join("?" * len(categories))
            conditions.append(f"category IN ({placeholders})")
            params.extend(categories)

        if vendors:
            placeholders = ",".join("?" * len(vendors))
            conditions.append(f"vendor IN ({placeholders})")
            params.extend(vendors)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return self.conn.execute(
            f"SELECT * FROM products WHERE {where_clause} ORDER BY product_id", params
        ).fetchdf().to_dict("records")

    def get_distinct_categories(self) -> list[str]:
        return [
            row[0]
            for row in self.conn.execute(
                "SELECT DISTINCT category FROM products ORDER BY category"
            ).fetchall()
            if row[0] is not None
        ]

    def get_distinct_vendors(self) -> list[str]:
        return [
            row[0]
            for row in self.conn.execute(
                "SELECT DISTINCT vendor FROM products ORDER BY vendor"
            ).fetchall()
            if row[0] is not None
        ]
