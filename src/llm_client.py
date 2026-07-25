import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"

ENRICHMENT_PROMPT = """You are a product description writer for a luxury fashion e-commerce store.
The products are sold in France and the descriptions must be in French.

Product type: {product_type}
Brand: {vendor}
Original description: {description}

Generate the following sections in French:

[DESCRIPTION]
Write an improved 2-3 sentence product description in French. Make it appealing and informative.

[MATIERE]
Write a short material / fabric description in French (1 sentence). If you don't know the exact material, describe what it looks like.

[ENTRETIEN]
Write short care instructions in French (1 sentence). If you don't know, suggest general care.

[STYLE]
Write a short styling tip in French (1 sentence about how to wear this item).

[SEO]
List 5-10 comma-separated SEO keywords in French. Include the product type and brand."""


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


def enrich_product(description, product_type, vendor):
    if not description:
        description = "(aucune description disponible)"
    prompt = ENRICHMENT_PROMPT.format(
        product_type=product_type or "Non spécifié",
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
            if result:
                return result
        except Exception:
            if attempt == 1:
                return None
    return None
