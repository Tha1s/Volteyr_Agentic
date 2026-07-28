from __future__ import annotations

from typing import TYPE_CHECKING

from src.db.connection import get_connection

if TYPE_CHECKING:
    from src.enrichment.models import Enrichment


class EnrichmentRepository:
    @property
    def _conn(self):
        return get_connection()

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
        result = self._conn.execute(
            """
            INSERT INTO enrichissements
                (product_id, enriched_description, material, care_instructions, style, seo_keywords, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                product_id,
                enriched_description,
                material,
                care_instructions,
                style,
                seo_keywords,
                model_used,
            ),
        )
        return result.fetchone()[0]

    def find_by_product_id(self, product_id: int) -> dict | None:
        row = self._conn.execute(
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
        if row is None:
            return None
        return {
            "id": row[0],
            "product_id": row[1],
            "enriched_description": row[2],
            "material": row[3],
            "care_instructions": row[4],
            "style": row[5],
            "seo_keywords": row[6],
            "model_used": row[7],
            "created_at": row[8],
        }

    def find_enriched_ids(self) -> set[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT product_id FROM enrichissements"
        ).fetchall()
        return {row[0] for row in rows}

    def delete_by_product_id(self, product_id: int) -> None:
        self._conn.execute(
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

        rows = self._conn.execute(query, params).fetchall()
        return [
            {
                "product_id": row[0],
                "category": row[1],
                "enriched_description": row[2],
                "material": row[3],
                "care_instructions": row[4],
                "style": row[5],
                "seo_keywords": row[6],
                "model_used": row[7],
                "created_at": row[8],
            }
            for row in rows
        ]

    def search(
        self,
        q: str | None = None,
        category: str | None = None,
        vendor: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        conditions = []
        params = []

        if q:
            conditions.append("e.enriched_description ILIKE ?")
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

        count_row = self._conn.execute(
            f"""
            SELECT COUNT(*)
            FROM products p
            INNER JOIN enrichissements e ON p.product_id = e.product_id
            {where_clause}
            """,
            params,
        ).fetchone()
        total = count_row[0]

        rows = self._conn.execute(
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

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "product_id": row[1],
                    "enriched_description": row[2],
                    "material": row[3],
                    "care_instructions": row[4],
                    "style": row[5],
                    "seo_keywords": row[6],
                    "model_used": row[7],
                    "created_at": row[8],
                    "product_type": row[9],
                    "category": row[10],
                    "product_tags": row[11],
                    "vendor": row[12],
                    "description": row[13],
                }
            )

        return results, total
