from src.ui.utils import quality_label, truncate_desc


def test_quality_label_none():
    assert quality_label(None) == "Vide"


def test_quality_label_empty():
    assert quality_label("") == "Vide"


def test_quality_label_short():
    assert quality_label("Court") == "<50c"


def test_quality_label_medium():
    assert quality_label("A" * 60) == "50-200c"


def test_quality_label_long():
    assert quality_label("A" * 300) == "200-500c"


def test_quality_label_very_long():
    assert quality_label("A" * 600) == ">500c"


def test_truncate_desc_none():
    assert truncate_desc(None) == ""


def test_truncate_desc_short():
    assert truncate_desc("Hello") == "Hello"


def test_truncate_desc_long():
    assert truncate_desc("A" * 100, max_len=80) == "A" * 80 + "..."


def test_truncate_desc_int():
    assert "42" in truncate_desc(42)
