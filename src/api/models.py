from pydantic import BaseModel


class ProductResponse(BaseModel):
    product_id: int
    product_type: str
    category: str
    vendor: str
    description: str | None = None
    enriched_description: str | None = None
    material: str | None = None
    care_instructions: str | None = None
    style: str | None = None
    seo_keywords: str | None = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    results: list[ProductResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_products: int
    empty_descriptions: int
    short_descriptions: int
    categories: dict[str, int] | None = None
