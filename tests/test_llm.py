import pytest
import requests
from unittest.mock import patch, MagicMock

from src.llm.client import generate, check_ollama
from src.llm.strategies import SmallModelStrategy, LargeModelStrategy, get_strategy
from src.llm.prompts import ENRICHMENT_SYSTEM, ENRICHMENT_USER


@pytest.fixture
def mock_ollama_response():
    with patch("src.llm.client.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": '{"enriched_description": "Test", "material": "Soie"}'}
        mock_post.return_value = mock_response
        yield mock_post


def test_generate_success(mock_ollama_response):
    result = generate("qwen2.5:1.5b", "test prompt")
    assert result is not None


def test_generate_failure():
    with patch("src.llm.client.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("Connection refused")
        result = generate("qwen2.5:1.5b", "test")
        assert result is None


def test_check_ollama_success():
    with patch("src.llm.client.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        assert check_ollama() is True


def test_check_ollama_failure():
    with patch("src.llm.client.requests.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError("No connection")
        assert check_ollama() is False


def test_small_model_strategy():
    strat = SmallModelStrategy()
    assert strat.model == "qwen2.5:1.5b"
    assert strat.timeout == 30


def test_large_model_strategy():
    strat = LargeModelStrategy()
    assert strat.timeout == 120


def test_get_strategy():
    assert isinstance(get_strategy(False), SmallModelStrategy)
    assert isinstance(get_strategy(True), LargeModelStrategy)


def test_prompts_format():
    prompt = ENRICHMENT_USER.format(
        product_type="Robe",
        category="Robes & Jupes",
        vendor="Sandro",
        description="Belle robe"
    )
    assert "Robe" in prompt
    assert "Sandro" in prompt
