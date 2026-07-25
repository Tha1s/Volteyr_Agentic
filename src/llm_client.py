import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

ENRICHMENT_PROMPT = """Tu es un rédacteur de descriptions produit pour une boutique de mode.
Les produits sont vendus en France — toutes les réponses doivent être en français.

Type de produit : {product_type}
Catégorie : {category}
Marque : {vendor}
Description originale : {description}

RÈGLES IMPORTANTES :
- N'invente jamais d'information. Si le texte original ne mentionne pas la matière ou l'entretien, écris "Non précisé" à la place.
- Mentionne toujours le type de produit spécifique dans la première phrase (ex: "Ce poncho...", "Cette robe...", "Ce T-shirt...").
- Ton : chic et accessible, ni trop luxueux ni trop familier.
- Utilise uniquement les détails présents dans la description originale. N'ajoute pas de caractéristiques inventées.

Génère ces sections en français :

[DESCRIPTION]
Suis cette structure : le type de produit avec ses caractéristiques principales. Une phrase sur le style ou l'usage. La matière si elle est connue.

[MATIERE]
Une phrase sur la matière. Si inconnue : "Matière non précisée."

[ENTRETIEN]
Une phrase sur l'entretien. Si inconnu : "Entretien non précisé."

[STYLE]
Un court conseil de style.

[SEO]
5 à 10 mots-clés SEO en français, séparés par des virgules. Inclus toujours : {vendor}, {category}, {product_type}."""


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
