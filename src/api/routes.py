from fastapi import APIRouter, Depends, HTTPException, Path, Query

from src.api.dependencies import get_enrichment_repo, get_product_repo
from src.api.models import ProductResponse, SearchResponse
from src.db.enrichment_repository import EnrichmentRepository
from src.db.product_repository import ProductRepository

router = APIRouter(prefix="/api")


@router.get("/products/search", response_model=SearchResponse)
async def search_products(
    q: str | None = Query(None),
    category: str | None = Query(None),
    vendor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: EnrichmentRepository = Depends(get_enrichment_repo),
):
    results, total = repo.search(q=q, category=category, vendor=vendor, limit=limit, offset=offset)
    return SearchResponse(
        results=[ProductResponse(**r) for r in results],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(gt=0),
    product_repo: ProductRepository = Depends(get_product_repo),
    enrichment_repo: EnrichmentRepository = Depends(get_enrichment_repo),
):
    product = product_repo.find_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    enriched = enrichment_repo.find_by_product_id(product_id)
    return ProductResponse(
        product_id=product["product_id"],
        product_type=product.get("product_type") or "",
        category=product.get("category") or "",
        vendor=product.get("vendor") or "",
        description=product.get("description"),
        enriched_description=enriched["enriched_description"] if enriched else None,
        material=enriched["material"] if enriched else None,
        care_instructions=enriched["care_instructions"] if enriched else None,
        style=enriched["style"] if enriched else None,
        seo_keywords=enriched["seo_keywords"] if enriched else None,
    )
