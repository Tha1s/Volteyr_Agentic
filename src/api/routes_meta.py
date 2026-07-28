from fastapi import APIRouter, Depends

from src.api.models import StatsResponse
from src.db.product_repository import ProductRepository
from src.llm.client import check_ollama

router = APIRouter(prefix="/api")


def get_product_repo() -> ProductRepository:
    return ProductRepository()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(repo: ProductRepository = Depends(get_product_repo)):
    return StatsResponse(
        total_products=repo.count_all(),
        empty_descriptions=repo.count_empty(),
        short_descriptions=repo.count_short(),
        categories=dict(repo.count_by_category()),
    )


@router.get("/categories")
async def list_categories(repo: ProductRepository = Depends(get_product_repo)):
    return dict(repo.count_by_category())


@router.get("/health")
async def health_check(repo: ProductRepository = Depends(get_product_repo)):
    try:
        db_ok = repo.count_all() >= 0
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok, "ollama": check_ollama()}
