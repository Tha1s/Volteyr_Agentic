from src.db.enrichment_repository import EnrichmentRepository
from src.db.product_repository import ProductRepository


def get_product_repo() -> ProductRepository:
    return ProductRepository()


def get_enrichment_repo() -> EnrichmentRepository:
    return EnrichmentRepository()
