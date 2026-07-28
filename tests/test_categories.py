import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.config.categories import (
    load_category_map, normalize_product_type, _simple_match,
    auto_fill_categories, CONFIG_PATH, DEFAULT_CATEGORIES,
)


def test_simple_match_pantalon():
    assert _simple_match("Pantalon") == "Pantalons & Shorts"


def test_simple_match_chaussures():
    assert _simple_match("SHOES") == "Chaussures"


def test_simple_match_unknown():
    assert _simple_match("MarqueInconnue") == "Autres"


def test_normalize_with_mapping():
    mapping = {"Pantalon": "Pantalons & Shorts", "Pantalons & Shorts": "Pantalons & Shorts"}
    result = normalize_product_type("Pantalon", mapping)
    assert result == "Pantalons & Shorts"


def test_normalize_chain():
    mapping = {"A": "B", "B": "C", "C": "C"}
    result = normalize_product_type("A", mapping)
    assert result == "C"


def test_normalize_strips_child_suffix():
    mapping = {"Chaussures - Chaussures - Fille": "Chaussures", "Chaussures": "Chaussures"}
    result = normalize_product_type("Chaussures - Chaussures - Fille", mapping)
    assert result == "Chaussures"


def test_normalize_empty():
    assert normalize_product_type("") == "Autres"


def test_load_category_map_empty_file(tmp_path):
    yaml_file = tmp_path / "categories.yaml"
    yaml_file.write_text('default: "Test"\n')
    with patch("src.config.categories.CONFIG_PATH", yaml_file):
        mapping = load_category_map()
        assert mapping["default"] == "Test"
        for cat in DEFAULT_CATEGORIES:
            assert mapping.get(cat) == cat


def test_auto_fill():
    types = {"Pantalon", "SHOES", "MarqueInconnue"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write('mappings:\ndefault: "Autres"\n')
        tmp_path = Path(f.name)
    try:
        with patch("src.config.categories.CONFIG_PATH", tmp_path):
            auto_fill_categories(types)
            mapping = load_category_map()
            assert mapping["Pantalon"] == "Pantalons & Shorts"
            assert mapping["SHOES"] == "Chaussures"
            assert mapping["MarqueInconnue"] == "Autres"
    finally:
        tmp_path.unlink(missing_ok=True)


class TestSimpleMatchEdgeCases:
    def test_empty_string(self):
        assert _simple_match("") == "Autres"

    def test_none(self):
        assert _simple_match(None) == "Autres"

    def test_accented_bebe(self):
        assert _simple_match("Bébé") == "Bébé & Enfant"

    def test_mixed_case_pantalon(self):
        assert _simple_match("PANTALON") == "Pantalons & Shorts"

    def test_partial_match_pantalon_en_lin(self):
        assert _simple_match("Pantalon en lin") == "Pantalons & Shorts"

    def test_ambiguous_sac_a_main(self):
        assert _simple_match("Sac à main") == "Sacs & Maroquinerie"
