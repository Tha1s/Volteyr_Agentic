from src.db.connection import get_connection


class ProductRepository:
    @property
    def conn(self):
        return get_connection()

    def count_all(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    def _count_with(self, condition: str, params: list | None = None) -> int:
        return self.conn.execute(
            f"SELECT COUNT(*) FROM products WHERE {condition}", params or []
        ).fetchone()[0]

    def count_empty(self) -> int:
        return self._count_with("description IS NULL OR description = ''")

    def count_short(self, threshold: int = 50) -> int:
        return self._count_with(
            "LENGTH(description) > 0 AND LENGTH(description) < ?", [threshold]
        )

    def count_medium(self) -> int:
        return self._count_with("LENGTH(description) >= 50 AND LENGTH(description) < 200")

    def count_long(self) -> int:
        return self._count_with("LENGTH(description) >= 200 AND LENGTH(description) < 500")

    def count_very_long(self) -> int:
        return self._count_with("LENGTH(description) >= 500")

    def count_by_category(self) -> list[tuple[str, int]]:
        return self.conn.execute(
            "SELECT category, COUNT(*) AS cnt FROM products GROUP BY category ORDER BY cnt DESC"
        ).fetchall()

    def count_by_vendor(self) -> list[tuple[str, int]]:
        return self.conn.execute(
            "SELECT vendor, COUNT(*) AS cnt FROM products GROUP BY vendor ORDER BY cnt DESC"
        ).fetchall()

    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM products ORDER BY product_id LIMIT ? OFFSET ?", [limit, offset]
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def find_by_id(self, product_id: int) -> dict | None:
        cursor = self.conn.execute(
            "SELECT * FROM products WHERE product_id = ?", [product_id]
        )
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(columns, row))

    def find_by_ids(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        cursor = self.conn.execute(
            f"SELECT * FROM products WHERE product_id IN ({placeholders}) ORDER BY product_id",
            ids,
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

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
        cursor = self.conn.execute(
            f"SELECT * FROM products WHERE {where_clause} ORDER BY product_id", params
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

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

    def get_vendors_by_categories(self, categories: list[str]) -> list[str]:
        if not categories:
            return []
        placeholders = ",".join("?" * len(categories))
        return [
            row[0]
            for row in self.conn.execute(
                f"SELECT DISTINCT vendor FROM products WHERE category IN ({placeholders}) ORDER BY vendor",
                categories,
            ).fetchall()
            if row[0] is not None
        ]
