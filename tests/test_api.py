import pytest
import sqlite3
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.connection import set_connection, reset_connection
from src.db.schema import init_schema
from src.db.enrichment_repository import EnrichmentRepository
from src.enrichment.models import Enrichment


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    set_connection(conn)
    init_schema()
    yield conn
    reset_connection()


@pytest.fixture
def api_client(db_conn):
    return TestClient(app)



@pytest.fixture
def sample_data(db_conn):
    db_conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "Robe", "Robes & Jupes", "", "", "Sandro", 10, 150.0, "Belle robe en soie"),
            (2, "Pantalon", "Pantalons", "", "", "Maje", 5, 120.0, ""),
            (3, "T-Shirt", "Hauts", "", "", "AMI", 20, 60.0, "T-shirt coton bio"),
        ],
    )
    repo = EnrichmentRepository()
    repo.save(
        Enrichment(
            product_id=1,
            enriched_description="Robe elegante en soie",
            material="Soie",
            care_instructions="Nettoyage a sec",
            style="Élégant",
            seo_keywords="robe, soie",
            model_used="test",
        )
    )
    repo.save(
        Enrichment(
            product_id=2,
            enriched_description="Pantalon en lin decontracte",
            material="Lin",
            care_instructions="Lavage 30\u00b0",
            style="Décontracté",
            seo_keywords="pantalon, lin",
            model_used="test",
        )
    )
    return db_conn


class TestHealth:
    def test_health_structure(self, api_client):
        resp = api_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "db" in data
        assert "ollama" in data
        assert data["db"] is True


class TestStats:
    def test_stats_empty_db(self, api_client):
        resp = api_client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 0
        assert data["empty_descriptions"] == 0
        assert data["short_descriptions"] == 0

    def test_stats_with_data(self, api_client, sample_data):
        resp = api_client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 3
        assert data["empty_descriptions"] == 1
        assert data["short_descriptions"] == 2
        assert "Robes & Jupes" in data["categories"]
        assert data["categories"]["Robes & Jupes"] == 1


class TestCategories:
    def test_categories_empty_db(self, api_client):
        resp = api_client.get("/api/categories")
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_categories_returns_dict(self, api_client, sample_data):
        resp = api_client.get("/api/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert data["Robes & Jupes"] == 1
        assert data["Pantalons"] == 1
        assert data["Hauts"] == 1


class TestSearch:
    def test_search_no_enriched(self, api_client):
        resp = api_client.get("/api/products/search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_search_with_enriched(self, api_client, sample_data):
        resp = api_client.get("/api/products/search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        ids = {r["product_id"] for r in data["results"]}
        assert ids == {1, 2}

    def test_search_by_query(self, api_client, sample_data):
        resp = api_client.get("/api/products/search?q=soie")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["product_id"] == 1
        assert "soie" in data["results"][0]["enriched_description"].lower()

    def test_search_no_match(self, api_client, sample_data):
        resp = api_client.get("/api/products/search?q=inexistant")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_search_filtered_by_category(self, api_client, sample_data):
        resp = api_client.get("/api/products/search?category=Robes+%26+Jupes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["product_id"] == 1

    def test_search_filtered_by_vendor(self, api_client, sample_data):
        resp = api_client.get("/api/products/search?vendor=Maje")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["product_id"] == 2

    def test_search_pagination(self, api_client, sample_data):
        resp = api_client.get("/api/products/search?limit=1&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["results"]) == 1
        assert data["limit"] == 1
        assert data["offset"] == 0

        resp = api_client.get("/api/products/search?limit=1&offset=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["results"]) == 1


class TestProductDetail:
    def test_get_product_with_enrichment(self, api_client, sample_data):
        resp = api_client.get("/api/products/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == 1
        assert data["vendor"] == "Sandro"
        assert data["description"] == "Belle robe en soie"
        assert data["enriched_description"] == "Robe elegante en soie"
        assert data["material"] == "Soie"
        assert data["style"] == "Élégant"

    def test_get_product_without_enrichment(self, api_client, sample_data):
        resp = api_client.get("/api/products/3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == 3
        assert data["enriched_description"] is None
        assert data["material"] is None

    def test_get_product_not_found(self, api_client):
        resp = api_client.get("/api/products/999")
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "Produit introuvable"
