import pytest
import json
from src.enrichment.models import Enrichment
from src.enrichment.factory import EnrichmentFactory
from src.enrichment.pipeline import EnrichmentPipeline
from src.enrichment.steps.normalize import NormalizeStep
from unittest.mock import patch


@pytest.fixture
def sample_llm_response():
    return {
        "enriched_description": "Cette robe en soie est parfaite pour les soirées d'été.",
        "material": "Soie",
        "care_instructions": "Lavage à la main recommandé",
        "style": "Idéal pour une soirée chic",
        "seo_keywords": "robe, soie, soirée, élégance"
    }

def test_enrichment_from_llm_response(sample_llm_response):
    e = EnrichmentFactory.from_llm_response(42, sample_llm_response, "qwen2.5:7b")
    assert e.product_id == 42
    assert e.enriched_description == sample_llm_response["enriched_description"]
    assert e.material == "Soie"
    assert e.model_used == "qwen2.5:7b"

def test_enrichment_from_llm_missing_fields():
    e = EnrichmentFactory.from_llm_response(1, {})
    assert e.enriched_description == ""

def test_enrichment_from_llm_short_description():
    e = EnrichmentFactory.from_llm_response(1, {"enriched_description": "Court"})
    assert e.enriched_description == ""

def test_enrichment_to_dict(sample_llm_response):
    e = EnrichmentFactory.from_llm_response(1, sample_llm_response)
    d = e.to_dict
    assert d["product_id"] == 1
    assert d["seo_keywords"] == "robe, soie, soirée, élégance"

def test_normalize_step():
    step = NormalizeStep()
    products = [
        {"product_id": 1, "product_type": "Robe", "category": ""},
        {"product_id": 2, "product_type": "Pantalon", "category": ""},
    ]
    results = step.process(products)
    for r in results:
        assert r["category"] != ""

def test_normalize_step_keeps_existing():
    step = NormalizeStep()
    products = [
        {"product_id": 1, "product_type": "Robe", "category": "Robes & Jupes"},
    ]
    results = step.process(products)
    assert results[0]["category"] == "Robes & Jupes"

def test_pipeline_integration():
    pipeline = EnrichmentPipeline()
    assert pipeline.normalize is not None
    assert pipeline.generate is not None
    assert pipeline.persist is not None

def test_pipeline_run_single():
    pipeline = EnrichmentPipeline()
    product = {"product_id": 1, "product_type": "Robe", "category": "", "vendor": "Sandro", "description": "Test", "product_tags": ""}
    with patch("src.enrichment.steps.generate.GenerateStep.process") as mock_gen:
        mock_gen.return_value = []
        result = pipeline.normalize.process([product])
        assert result[0]["category"] != ""
