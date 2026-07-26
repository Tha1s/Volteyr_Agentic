from dataclasses import dataclass


@dataclass
class Enrichment:
    product_id: int
    enriched_description: str
    material: str = ""
    care_instructions: str = ""
    style: str = ""
    seo_keywords: str = ""
    model_used: str = ""

    @property
    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "enriched_description": self.enriched_description,
            "material": self.material,
            "care_instructions": self.care_instructions,
            "style": self.style,
            "seo_keywords": self.seo_keywords,
            "model_used": self.model_used,
        }
