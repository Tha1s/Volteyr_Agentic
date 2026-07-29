from __future__ import annotations

from typing import TYPE_CHECKING

from src.db.connection import get_connection

if TYPE_CHECKING:
    from src.enrichment.models import Enrichment


class EnrichmentRepository:
    _conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = get_connection()
        return self._conn

    def save(self, enrichment: Enrichment) -> int:
        return self.save_from_dict(**enrichment.to_dict)

    def save_from_dict(
        self,
        product_id: int,
        enriched_description: str,
        material: str = "",
        care_instructions: str = "",
        style: str = "",
        seo_keywords: str = "",
        model_used: str = "",
    ) -> int:
        cursor = self.conn.execute("""
            INSERT INTO enrichissements
                (product_id, enriched_description, material, care_instructions, style, seo_keywords, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            enriched_description,
            material,
            care_instructions,
            style,
            seo_keywords,
            model_used,
        ))
        return cursor.lastrowid

    def find_by_product_id(self, product_id: int) -> dict | None:
        row = self.conn.execute(
            """
            SELECT id, product_id, enriched_description, material, care_instructions,
                   style, seo_keywords, model_used, created_at
            FROM enrichissements
            WHERE product_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()
        return dict(row) if row else None

    def find_enriched_ids(self) -> set[int]:
        return {
            row["product_id"]
            for row in self.conn.execute(
                "SELECT DISTINCT product_id FROM enrichissements"
            ).fetchall()
        }

    def delete_by_product_id(self, product_id: int) -> None:
        self.conn.execute(
            "DELETE FROM enrichissements WHERE product_id = ?", (product_id,)
        )

    def find_enriched_with_products(
        self, category: str | None = None
    ) -> list[dict]:
        query = """
            SELECT p.product_id, p.category, e.enriched_description, e.material,
                   e.care_instructions, e.style, e.seo_keywords, e.model_used, e.created_at
            FROM products p
            INNER JOIN enrichissements e ON p.product_id = e.product_id
        """
        params: list = []
        if category is not None:
            query += " WHERE p.category = ?"
            params.append(category)
        query += " ORDER BY p.product_id"

        return [
            dict(row)
            for row in self.conn.execute(query, params).fetchall()
        ]

    def _build_search_query(self, q, category, vendor):
        conditions = []
        params = []

        if q:
            conditions.append("LOWER(e.enriched_description) LIKE LOWER(?)")
            escaped = q.replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{escaped}%")
        if category:
            conditions.append("p.category = ?")
            params.append(category)
        if vendor:
            conditions.append("p.vendor = ?")
            params.append(vendor)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, params

    def search(
        self,
        q: str | None = None,
        category: str | None = None,
        vendor: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        where_clause, params = self._build_search_query(q, category, vendor)

        total = self.conn.execute(
            f"""
            SELECT COUNT(*)
            FROM products p
            INNER JOIN enrichissements e ON p.product_id = e.product_id
            {where_clause}
            """,
            params,
        ).fetchone()[0]

        rows = self.conn.execute(
            f"""
            SELECT e.id, e.product_id, e.enriched_description, e.material,
                   e.care_instructions, e.style, e.seo_keywords, e.model_used,
                   e.created_at, p.product_type, p.category, p.product_tags,
                   p.vendor, p.description
            FROM products p
            INNER JOIN enrichissements e ON p.product_id = e.product_id
            {where_clause}
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

        return [dict(row) for row in rows], total
