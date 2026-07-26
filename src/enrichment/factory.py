from src.enrichment.models import Enrichment


class EnrichmentFactory:

    @staticmethod
    def to_db_params(enrichment: Enrichment) -> dict:
        return {
            "product_id": enrichment.product_id,
            "enriched_description": enrichment.enriched_description,
            "material": enrichment.material,
            "care_instructions": enrichment.care_instructions,
            "style": enrichment.style,
            "seo_keywords": enrichment.seo_keywords,
            "model_used": enrichment.model_used,
        }

    @staticmethod
    def from_llm_response(product_id: int, llm_json: dict, model_used: str = "") -> Enrichment:
        enriched_description = llm_json.get("enriched_description", "")
        if not isinstance(enriched_description, str) or len(enriched_description.strip()) < 20:
            enriched_description = ""

        def _get(key: str) -> str:
            val = llm_json.get(key)
            if val and isinstance(val, str) and val.strip():
                return val.strip()
            return "Non précisé"

        return Enrichment(
            product_id=product_id,
            enriched_description=enriched_description,
            material=_get("material"),
            care_instructions=_get("care_instructions"),
            style=_get("style"),
            seo_keywords=_get("seo_keywords"),
            model_used=model_used,
        )

    @staticmethod
    def from_db_row(row: dict) -> Enrichment:
        return Enrichment(
            product_id=row["product_id"],
            enriched_description=row.get("enriched_description", ""),
            material=row.get("material", ""),
            care_instructions=row.get("care_instructions", ""),
            style=row.get("style", ""),
            seo_keywords=row.get("seo_keywords", ""),
            model_used=row.get("model_used", ""),
        )
