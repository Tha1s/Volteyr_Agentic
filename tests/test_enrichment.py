import sqlite3
import pytest
from unittest.mock import MagicMock, patch

import src.db.connection as conn_mod
from src.db.connection import close
from src.db.schema import init_schema
from src.enrichment.models import Enrichment
from src.enrichment.factory import EnrichmentFactory
from src.enrichment.pipeline import EnrichmentPipeline
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.persist import PersistStep
from src.db.enrichment_repository import EnrichmentRepository


@pytest.fixture
def sample_llm_response():
    return {
        "enriched_description": "Cette robe en soie est parfaite pour les soirées d'été.",
        "material": "Soie",
        "care_instructions": "Lavage à la main recommandé",
        "style": "Idéal pour une soirée chic",
        "seo_keywords": "robe, soie, soirée, élégance"
    }


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn_mod._local.connection = conn
    init_schema()
    yield conn
    close()

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

def test_pipeline_run_single():
    from unittest.mock import patch
    pipeline = EnrichmentPipeline()
    product = {"product_id": 1, "product_type": "Robe", "category": "Robes & Jupes", "vendor": "Sandro", "description": "Test", "product_tags": ""}
    with patch("src.enrichment.steps.generate.GenerateStep.process") as mock_gen:
        mock_gen.return_value = None
        result = pipeline.run_single(product)
        assert result is None


# ── T04: Enrichment.to_dict / from_db_row ──────────────────────


def test_to_dict_all_fields():
    e = Enrichment(
        product_id=42,
        enriched_description="Une belle robe en soie",
        material="Soie",
        care_instructions="Lavage à la main",
        style="Élégant",
        seo_keywords="robe, soie",
        model_used="qwen2.5:7b",
    )
    params = e.to_dict
    assert params["product_id"] == 42
    assert params["enriched_description"] == "Une belle robe en soie"
    assert params["material"] == "Soie"
    assert params["care_instructions"] == "Lavage à la main"
    assert params["style"] == "Élégant"
    assert params["seo_keywords"] == "robe, soie"
    assert params["model_used"] == "qwen2.5:7b"


def test_to_dict_empty_fields():
    e = Enrichment(product_id=1, enriched_description="")
    params = e.to_dict
    assert params["product_id"] == 1
    assert params["enriched_description"] == ""
    assert params["material"] == ""
    assert params["care_instructions"] == ""
    assert params["style"] == ""
    assert params["seo_keywords"] == ""
    assert params["model_used"] == ""


def test_from_db_row_valid():
    row = {
        "product_id": 99,
        "enriched_description": "Superbe veste en cuir",
        "material": "Cuir",
        "care_instructions": "Nettoyage à sec",
        "style": "Rock",
        "seo_keywords": "veste, cuir",
        "model_used": "qwen2.5:1.5b",
    }
    e = EnrichmentFactory.from_db_row(row)
    assert e.product_id == 99
    assert e.enriched_description == "Superbe veste en cuir"
    assert e.material == "Cuir"
    assert e.care_instructions == "Nettoyage à sec"
    assert e.style == "Rock"
    assert e.seo_keywords == "veste, cuir"
    assert e.model_used == "qwen2.5:1.5b"


def test_from_db_row_missing_product_id():
    row: dict = {}
    with pytest.raises(KeyError):
        EnrichmentFactory.from_db_row(row)


def test_from_db_row_missing_optional_keys():
    row = {"product_id": 99}
    e = EnrichmentFactory.from_db_row(row)
    assert e.product_id == 99
    assert e.enriched_description == ""
    assert e.material == ""
    assert e.care_instructions == ""
    assert e.style == ""
    assert e.seo_keywords == ""
    assert e.model_used == ""


# ── T02: PersistStep.process ────────────────────────────────────────────────


def test_persist_all_enrichments(db_conn):
    repo = EnrichmentRepository()
    step = PersistStep(repo=repo)
    enrichments = [
        Enrichment(
            product_id=1,
            enriched_description="Robe élégante",
            material="Soie",
            model_used="qwen2.5:1.5b",
        ),
        Enrichment(
            product_id=2,
            enriched_description="Pantalon chic",
            material="Lin",
            model_used="qwen2.5:1.5b",
        ),
        Enrichment(
            product_id=3,
            enriched_description="Veste tendance",
            material="Cuir",
            model_used="qwen2.5:1.5b",
        ),
    ]
    success, failures = step.process(enrichments)
    assert success == 3
    assert failures == 0
    count = db_conn.execute(
        "SELECT COUNT(*) FROM enrichissements"
    ).fetchone()[0]
    assert count == 3


def test_persist_mixed_enrichments(db_conn):
    repo = EnrichmentRepository()
    step = PersistStep(repo=repo)
    enrichments = [
        Enrichment(
            product_id=1,
            enriched_description="OK",
            model_used="qwen2.5:1.5b",
        ),
        None,
        Enrichment(
            product_id=2,
            enriched_description="OK",
            model_used="qwen2.5:1.5b",
        ),
        None,
    ]
    success, failures = step.process(enrichments)
    assert success == 2
    assert failures == 2
    count = db_conn.execute(
        "SELECT COUNT(*) FROM enrichissements"
    ).fetchone()[0]
    assert count == 2


def test_persist_empty_list(db_conn):
    repo = EnrichmentRepository()
    step = PersistStep(repo=repo)
    success, failures = step.process([])
    assert success == 0
    assert failures == 0
    count = db_conn.execute(
        "SELECT COUNT(*) FROM enrichissements"
    ).fetchone()[0]
    assert count == 0


def test_persist_delete_before_save(db_conn):
    repo = EnrichmentRepository()
    step = PersistStep(repo=repo)

    e1 = Enrichment(
        product_id=1,
        enriched_description="Version 1",
        model_used="qwen2.5:1.5b",
    )
    step.process([e1])

    e2 = Enrichment(
        product_id=1,
        enriched_description="Version 2 mise à jour",
        material="Coton",
        care_instructions="Laver à 30°",
        style="Décontracté",
        seo_keywords="coton, casual",
        model_used="qwen2.5:7b",
    )
    step.process([e2])

    count = db_conn.execute(
        "SELECT COUNT(*) FROM enrichissements WHERE product_id = 1"
    ).fetchone()[0]
    assert count == 1
    saved = repo.find_by_product_id(1)
    assert saved["enriched_description"] == "Version 2 mise à jour"
    assert saved["material"] == "Coton"
    assert saved["care_instructions"] == "Laver à 30°"
    assert saved["model_used"] == "qwen2.5:7b"


# ── T03: GenerateStep.process ──────────────────────────────────────────────


def _valid_json_response():
    return '{"enriched_description": "Superbe robe en soie parfaite pour les soirées.", "material": "Soie", "care_instructions": "Lavage à la main", "style": "Élégant et chic", "seo_keywords": "robe, soie, soirée, mode"}'

def _invalid_json_response():
    return "pas du json valide {broken}"

def _sample_product():
    return {
        "product_id": 42,
        "product_type": "Robe",
        "category": "Robes & Jupes",
        "vendor": "Sandro",
        "description": "Belle robe",
    }


def test_generate_valid_json():
    step = GenerateStep()
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = _valid_json_response()
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([_sample_product()])
    assert len(results) == 1
    assert results[0] is not None
    assert results[0].product_id == 42
    assert "robe" in results[0].enriched_description.lower()
    assert results[0].material == "Soie"


def test_generate_invalid_json():
    step = GenerateStep()
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = _invalid_json_response()
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([_sample_product()])
    assert len(results) == 1
    assert results[0] is None


def test_generate_llm_returns_none():
    step = GenerateStep()
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = None
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([_sample_product()])
    assert len(results) == 1
    assert results[0] is None


def test_generate_retry_on_first_failure():
    step = GenerateStep(max_retries=1)
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.side_effect = [
            _invalid_json_response(),
            _valid_json_response(),
        ]
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([_sample_product()])
    assert len(results) == 1
    assert results[0] is not None
    assert mock_strategy.generate.call_count == 2


def test_generate_product_missing_keys():
    step = GenerateStep()
    product = {"product_id": 1}  # missing product_type, category, vendor, description
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = _valid_json_response()
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([product])
    assert len(results) == 1
    assert results[0] is not None
    assert results[0].product_id == 1


def test_generate_multiple_products():
    step = GenerateStep()
    products = [
        {"product_id": 1, "product_type": "Robe", "category": "", "vendor": "A", "description": "d1"},
        {"product_id": 2, "product_type": "Pantalon", "category": "", "vendor": "B", "description": "d2"},
        {"product_id": 3, "product_type": "Veste", "category": "", "vendor": "C", "description": "d3"},
    ]
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = _valid_json_response()
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process(products)
    assert len(results) == 3
    assert all(r is not None for r in results)


def test_generate_not_dict_json():
    step = GenerateStep()
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get:
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = "[1, 2, 3]"
        mock_strategy.model = "qwen2.5:1.5b"
        mock_get.return_value = mock_strategy
        results = step.process([_sample_product()])
    assert len(results) == 1
    assert results[0] is None


# T08: generate step with missing keys / edge-case product dicts


def test_generate_missing_category_key():
    step = GenerateStep()
    product = {"product_id": 1, "product_type": "Robe", "vendor": "Sandro", "description": "Test"}
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get_strat:
        mock_strat = MagicMock()
        mock_strat.model = "test"
        mock_strat.generate.return_value = '{"enriched_description": "Test description suffisamment longue", "material": "Soie"}'
        mock_get_strat.return_value = mock_strat
        results = step.process([product])
        assert results[0] is not None
        assert results[0].product_id == 1


def test_generate_with_none_values():
    step = GenerateStep()
    product = {"product_id": 2, "product_type": None, "category": None, "vendor": None, "description": None}
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get_strat:
        mock_strat = MagicMock()
        mock_strat.model = "test"
        mock_strat.generate.return_value = '{"enriched_description": "Test description suffisamment longue", "material": "Soie"}'
        mock_get_strat.return_value = mock_strat
        results = step.process([product])
        assert results[0] is not None
        assert results[0].product_id == 2


def test_generate_empty_product_dict():
    step = GenerateStep()
    product = {"product_id": 3}
    with patch("src.enrichment.steps.generate.get_strategy") as mock_get_strat:
        mock_strat = MagicMock()
        mock_strat.model = "test"
        mock_strat.generate.return_value = '{"enriched_description": "Test description suffisamment longue", "material": "Soie"}'
        mock_get_strat.return_value = mock_strat
        results = step.process([product])
        assert results[0] is not None
        assert results[0].product_id == 3
