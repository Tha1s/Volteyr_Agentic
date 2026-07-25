import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:1.5b"

ENRICHMENT_PROMPT = """You are a product description writer for a fashion e-commerce store.
Products are sold in France — all output must be in French.

Product type: {product_type}
Category: {category}
Tags: {tags}
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
5-10 comma-separated French SEO keywords. Always include: {brand}, {category}, {product_type}."""


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


def enrich_product(description, product_type, category, vendor, tags=""):
    if not description:
        description = "(aucune description disponible)"
    prompt = ENRICHMENT_PROMPT.format(
        product_type=product_type or "Non spécifié",
        category=category or "Non spécifié",
        tags=tags or "Non spécifié",
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
