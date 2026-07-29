import json
import logging

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT_LARGE = 120
OLLAMA_TIMEOUT_SMALL = 30

logger = logging.getLogger(__name__)
_session = requests.Session()


def generate(
    model: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    timeout: int | None = None,
) -> str | None:
    if timeout is None:
        timeout = OLLAMA_TIMEOUT_LARGE if "large" in model else OLLAMA_TIMEOUT_SMALL
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
        "format": "json",
    }
    try:
        resp = _session.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response")
    except requests.RequestException as e:
        logger.warning("LLM request failed (model=%s, timeout=%s): %s", model, timeout, e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("LLM response not valid JSON (model=%s): %s", model, e)
        return None


def check_ollama() -> bool:
    try:
        resp = _session.get("http://localhost:11434/api/tags", timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
