import pytest
import duckdb

from src.db.connection import get_connection, close
from src.db.product_repository import ProductRepository
from src.db.enrichment_repository import EnrichmentRepository
from src.enrichment.models import Enrichment
import src.db.connection as conn_mod


@pytest.fixture
def db_conn(monkeypatch):
    conn = duckdb.connect(":memory:")
    monkeypatch.setattr(conn_mod, "_connection", conn)
    conn.execute("""
        CREATE TABLE products (
            product_id BIGINT PRIMARY KEY,
            product_type VARCHAR,
            category VARCHAR,
            product_tags VARCHAR,
            images_array VARCHAR,
            vendor VARCHAR,
            inventory_quantity BIGINT,
            gross_amount_exc_tax_product DOUBLE,
            description VARCHAR
        )
    """)
    conn.execute("CREATE SEQUENCE enrichissements_seq START 1")
    conn.execute("""
        CREATE TABLE enrichissements (
            id BIGINT PRIMARY KEY DEFAULT nextval('enrichissements_seq'),
            product_id BIGINT,
            enriched_description VARCHAR,
            material VARCHAR,
            care_instructions VARCHAR,
            style VARCHAR,
            seo_keywords VARCHAR,
            model_used VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    yield conn
    conn.close()
    close()


@pytest.fixture
def sample_products(db_conn):
    db_conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "Robe", "Robes & Jupes", "", "", "Sandro", 10, 150.0, "Belle robe en soie"),
            (2, "Pantalon", "Pantalons", "", "", "Maje", 5, 120.0, ""),
            (3, "T-Shirt", "Hauts", "", "", "AMI", 20, 60.0, "T-shirt coton bio"),
        ]
    )
    return db_conn


def test_count_all(sample_products):
    repo = ProductRepository()
    assert repo.count_all() == 3


def test_count_empty(sample_products):
    repo = ProductRepository()
    assert repo.count_empty() == 1


def test_count_short(sample_products):
    repo = ProductRepository()
    assert repo.count_short(threshold=50) == 2
    assert repo.count_short(threshold=10) == 0


def test_find_by_id(sample_products):
    repo = ProductRepository()
    product = repo.find_by_id(1)
    assert product is not None
    assert product["product_id"] == 1
    assert product["vendor"] == "Sandro"
    assert product["description"] == "Belle robe en soie"
    assert repo.find_by_id(999) is None


def test_find_filtered_by_category(sample_products):
    repo = ProductRepository()
    results = repo.find_filtered(categories=["Robes & Jupes"])
    assert len(results) == 1
    assert results[0]["product_id"] == 1


def test_find_filtered_by_vendor(sample_products):
    repo = ProductRepository()
    results = repo.find_filtered(vendors=["Maje"])
    assert len(results) == 1
    assert results[0]["product_id"] == 2
    results = repo.find_filtered(vendors=["Sandro", "AMI"])
    assert len(results) == 2


def test_save_enrichment(sample_products):
    repo = EnrichmentRepository()
    enrichment = Enrichment(
        product_id=1,
        enriched_description="Robe en soie élégante",
        material="Soie",
        care_instructions="Nettoyage à sec",
        style="Élégant",
        seo_keywords="robe, soie, élégant",
        model_used="qwen2.5:1.5b",
    )
    enrichment_id = repo.save(enrichment)
    assert enrichment_id is not None
    assert enrichment_id > 0
    saved = repo.find_by_product_id(1)
    assert saved is not None
    assert saved["enriched_description"] == "Robe en soie élégante"
    assert saved["material"] == "Soie"


def test_find_enriched_ids(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=2, enriched_description="Pantalon en lin", model_used="qwen2.5:1.5b"))
    enriched = repo.find_enriched_ids()
    assert 2 in enriched
    assert 1 not in enriched
    assert 3 not in enriched


def test_search(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(
        product_id=1,
        enriched_description="Robe en soie élégante",
        material="Soie",
        model_used="qwen2.5:1.5b",
    ))
    results, total = repo.search(q="soie")
    assert total == 1
    assert len(results) == 1
    assert results[0]["product_id"] == 1
    results, total = repo.search(q="inexistant")
    assert total == 0
    assert len(results) == 0
