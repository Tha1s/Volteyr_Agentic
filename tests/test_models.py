import pytest

from src.api.models import (
    ProductResponse,
    SearchResponse,
    StatsResponse,
)


class TestProductResponse:
    def test_all_fields(self):
        p = ProductResponse(
            product_id=1,
            product_type="Robe",
            category="Robes & Jupes",
            vendor="Sandro",
            description="Belle robe",
            enriched_description="Robe élégante",
            material="Soie",
            care_instructions="Nettoyage à sec",
            style="Élégant",
            seo_keywords="robe, soie",
        )
        data = p.model_dump()
        assert data["product_id"] == 1
        assert data["product_type"] == "Robe"
        assert data["category"] == "Robes & Jupes"
        assert data["vendor"] == "Sandro"
        assert data["description"] == "Belle robe"
        assert data["enriched_description"] == "Robe élégante"
        assert data["material"] == "Soie"
        assert data["care_instructions"] == "Nettoyage à sec"
        assert data["style"] == "Élégant"
        assert data["seo_keywords"] == "robe, soie"

    def test_minimum_required_fields(self):
        p = ProductResponse(
            product_id=2,
            product_type="Pantalon",
            category="Pantalons",
            vendor="Maje",
        )
        data = p.model_dump()
        assert data["product_id"] == 2
        assert data["product_type"] == "Pantalon"
        assert data["category"] == "Pantalons"
        assert data["vendor"] == "Maje"
        assert data["description"] is None
        assert data["enriched_description"] is None
        assert data["material"] is None
        assert data["care_instructions"] is None
        assert data["style"] is None
        assert data["seo_keywords"] is None


class TestSearchResponse:
    def test_with_results(self):
        p = ProductResponse(
            product_id=1,
            product_type="Robe",
            category="Robes & Jupes",
            vendor="Sandro",
        )
        resp = SearchResponse(results=[p], total=1, limit=20, offset=0)
        data = resp.model_dump()
        assert len(data["results"]) == 1
        assert data["total"] == 1
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_empty_results(self):
        resp = SearchResponse(results=[], total=0, limit=20, offset=0)
        data = resp.model_dump()
        assert data["results"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0


class TestStatsResponse:
    def test_all_fields(self):
        s = StatsResponse(
            total_products=100,
            empty_descriptions=10,
            short_descriptions=20,
            categories={"Robes": 30, "Pantalons": 50},
        )
        data = s.model_dump()
        assert data["total_products"] == 100
        assert data["empty_descriptions"] == 10
        assert data["short_descriptions"] == 20
        assert data["categories"] == {"Robes": 30, "Pantalons": 50}

    def test_optional_fields_none(self):
        s = StatsResponse(
            total_products=100,
            empty_descriptions=0,
            short_descriptions=0,
        )
        data = s.model_dump()
        assert data["total_products"] == 100
        assert data["categories"] is None
