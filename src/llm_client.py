import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

ENRICHMENT_PROMPT = """You are a product description writer for a fashion e-commerce store.
Products are sold in France — all output must be in French.

Product type: {product_type}
Category: {category}
Brand: {vendor}
Original description: {description}

CRITICAL INSTRUCTIONS:
- Never invent information. If the original text does not mention material, care instructions, or specific details, state "Non précisé" instead of guessing.
- Always include the specific product type in the first sentence (e.g., "Ce poncho...", "Cette robe...", "Ce T-shirt...").
- Tone: chic and elegant but accessible — not overly luxurious.
- Only use details present in the original description. Do not add fictional features.

Generate these sections in French:

[DESCRIPTION]
Follow this structure: the specific product type with key features. A sentence about style or usage. Material information if known.

[MATIERE]
One sentence about material. If unknown: "Matière non précisée."

[ENTRETIEN]
One sentence about care. If unknown: "Entretien non précisé."

[STYLE]
One short styling tip.

[SEO]
5-10 comma-separated French SEO keywords. Always include: {vendor}, {category}, {product_type}."""


def check_ollama() -> bool:
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def parse_enrichment(text):
    sections = {}
    patterns = {
        "enriched_description": r"\[DESCRIPTION\]\s*(.+?)(?=\[|\Z)",
        "material": r"\[MATIERE\]\s*(.+?)(?=\[|\Z)",
        "care_instructions": r"\[ENTRETIEN\]\s*(.+?)(?=\[|\Z)",
        "style": r"\[STYLE\]\s*(.+?)(?=\[|\Z)",
        "seo_keywords": r"\[SEO\]\s*(.+?)(?=\[|\Z)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    return sections if sections else None


def validate_result(result: dict | None) -> bool:
    if result is None:
        return False
    desc = result.get("enriched_description", "")
    if len(desc) < 20:
        return False
    keys = ["enriched_description", "material", "care_instructions", "style", "seo_keywords"]
    return all(key in result and result[key] for key in keys)


def enrich_product(description, product_type, category, vendor, tags=""):
    if not description:
        description = "(aucune description disponible)"
    prompt = ENRICHMENT_PROMPT.format(
        product_type=product_type or "Non spécifié",
        category=category or "Non spécifié",
        vendor=vendor or "Non spécifié",
        description=description,
    )

    for attempt in range(2):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.7}},
                timeout=30,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "")
            result = parse_enrichment(text)
            if validate_result(result):
                return result
        except Exception:
            if attempt == 1:
                return None
    return None


def enrich_batch(products: list[dict], max_workers=3) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for p in products:
            future = executor.submit(enrich_product, **p)
            futures[future] = p
        for future in as_completed(futures):
            result = future.result()
            results.append({"product": futures[future], "result": result})
    return results
