import json
import time

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT_LARGE = 120
OLLAMA_TIMEOUT_SMALL = 30

_session = requests.Session()


def generate(
    model: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
) -> str | None:
    timeout = OLLAMA_TIMEOUT_LARGE if "large" in model else OLLAMA_TIMEOUT_SMALL
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
        "format": "json",
    }
    for attempt in range(2):
        try:
            resp = _session.post(OLLAMA_URL, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response")
        except requests.RequestException as e:
            print(f"LLM request failed (attempt {attempt+1}): {e}")
            if attempt == 0:
                time.sleep(1)
        except json.JSONDecodeError as e:
            print(f"LLM response not valid JSON: {e}")
            return None
    return None


def check_ollama() -> bool:
    try:
        resp = _session.get("http://localhost:11434/api/tags", timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False
