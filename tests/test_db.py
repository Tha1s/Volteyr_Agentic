import pytest
import sqlite3

from src.db.connection import get_connection, close
from src.db.product_repository import ProductRepository
from src.db.enrichment_repository import EnrichmentRepository
from src.enrichment.models import Enrichment
from src.db.schema import init_schema
import src.db.connection as conn_mod


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn_mod._local.connection = conn
    init_schema()
    yield conn
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


# T05: find_enriched_with_products edge cases


def test_find_enriched_with_products_no_filter(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Robe soie test", model_used="test"))
    repo.save(Enrichment(product_id=2, enriched_description="Pantalon lin test", model_used="test"))
    results = repo.find_enriched_with_products()
    assert len(results) == 2
    ids = {r["product_id"] for r in results}
    assert ids == {1, 2}


def test_find_enriched_with_products_category_filter(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Robe soie test", model_used="test"))
    repo.save(Enrichment(product_id=2, enriched_description="Pantalon lin test", model_used="test"))
    results = repo.find_enriched_with_products(category="Pantalons")
    assert len(results) == 1
    assert results[0]["product_id"] == 2


def test_find_enriched_with_products_category_no_match(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Robe soie test", model_used="test"))
    results = repo.find_enriched_with_products(category="Chaussures")
    assert results == []


def test_find_enriched_with_products_after_save(sample_products):
    repo = EnrichmentRepository()
    assert repo.find_enriched_with_products() == []
    repo.save(Enrichment(product_id=1, enriched_description="Test", model_used="test"))
    results = repo.find_enriched_with_products()
    assert len(results) == 1
    assert results[0]["product_id"] == 1


# T06: find_by_ids edge cases


def test_find_by_ids_empty_list(sample_products):
    repo = ProductRepository()
    results = repo.find_by_ids([])
    assert results == []


def test_find_by_ids_valid_ids(sample_products):
    repo = ProductRepository()
    results = repo.find_by_ids([3, 1])
    assert len(results) == 2
    assert results[0]["product_id"] == 1
    assert results[1]["product_id"] == 3


def test_find_by_ids_mixed_valid_invalid(sample_products):
    repo = ProductRepository()
    results = repo.find_by_ids([1, 999, 2, 777])
    assert len(results) == 2
    assert {r["product_id"] for r in results} == {1, 2}


# T07: search edge cases


def test_search_empty_q(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Test", model_used="test"))
    results, total = repo.search(q="")
    assert total == 1


def test_search_category_filter(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Test 1", model_used="test"))
    repo.save(Enrichment(product_id=2, enriched_description="Test 2", model_used="test"))
    results, total = repo.search(category="Robes & Jupes")
    assert total == 1
    assert results[0]["product_id"] == 1


def test_search_vendor_filter(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Test 1", model_used="test"))
    repo.save(Enrichment(product_id=2, enriched_description="Test 2", model_used="test"))
    results, total = repo.search(vendor="Sandro")
    assert total == 1
    assert results[0]["product_id"] == 1


def test_search_all_filters_combined(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Soie naturelle", model_used="test"))
    results, total = repo.search(q="soie", category="Robes & Jupes", vendor="Sandro")
    assert total == 1


def test_search_returns_tuple(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Test", model_used="test"))
    results, total = repo.search(q="test")
    assert isinstance(results, list)
    assert isinstance(total, int)
    assert total == 1


def test_search_pagination(sample_products):
    repo = EnrichmentRepository()
    repo.save(Enrichment(product_id=1, enriched_description="Test 1", model_used="test"))
    repo.save(Enrichment(product_id=2, enriched_description="Test 2", model_used="test"))
    repo.save(Enrichment(product_id=3, enriched_description="Test 3", model_used="test"))
    results, total = repo.search(limit=2, offset=0)
    assert total == 3
    assert len(results) == 2


class TestInitSchemaIdempotency:

    @pytest.fixture(autouse=True)
    def setup(self):
        conn = sqlite3.connect(":memory:")
        conn_mod._local.connection = conn
        from src.db.schema import init_schema
        self.init_schema = init_schema
        self.conn = conn
        yield
        close()

    def test_init_schema_twice_no_error(self):
        self.init_schema()
        self.init_schema()

    def test_init_schema_twice_no_duplicates(self):
        self.init_schema()
        count_before = self.conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='products'"
        ).fetchone()[0]
        self.init_schema()
        count_after = self.conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='products'"
        ).fetchone()[0]
        assert count_before == 1
        assert count_after == 1

    def test_schema_creates_both_tables(self):
        self.init_schema()
        tables = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {row[0] for row in tables}
        assert "products" in table_names
        assert "enrichissements" in table_names
