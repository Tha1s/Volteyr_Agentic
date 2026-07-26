import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.llm.client import generate
from src.llm.prompts import CATEGORIZATION_SYSTEM

DEFAULT_CATEGORIES = [
    "Pantalons", "Hauts", "Vestes & Manteaux", "Pulls & Maille",
    "Robes & Jupes", "Chemises", "Chaussures", "Sacs & Maroquinerie",
    "Bijoux", "Accessoires", "Lingerie", "Maillots De Bain",
    "Bébé & Enfant", "Autres",
]


def extract_types(csv_path: str = "data/products.csv") -> set[str]:
    types: set[str] = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pt = row.get("product_type", "").strip()
            if pt:
                types.add(pt)
    return types


def generate_mapping(product_types: set[str]) -> dict:
    types_list = sorted(product_types)
    prompt = (
        "Assigne chaque type de produit à une catégorie parmi la liste suivante.\n\n"
        f"Catégories disponibles: {', '.join(DEFAULT_CATEGORIES)}\n\n"
        "Types de produits:\n" + "\n".join(f"- {t}" for t in types_list) + "\n\n"
        'Réponds UNIQUEMENT au format JSON avec une clé "mappings" contenant un objet '
        'où chaque clé est un type de produit et chaque valeur est la catégorie assignée.\n'
        'Exemple: {"mappings": {"Pantalon": "Pantalons", "T-Shirt": "Hauts"}}\n'
        'Si un type ne correspond à aucune catégorie, utilise "Autres".'
    )
    response = generate(model="llama3.2:3b", prompt=prompt, system=CATEGORIZATION_SYSTEM, temperature=0.3)
    if response is None:
        print("Warning: LLM returned None, using fallback")
        return {}
    try:
        data = json.loads(response)
        mappings = data.get("mappings", {})
    except (json.JSONDecodeError, AttributeError):
        print("Warning: Failed to parse LLM response, using fallback")
        return {}
    for t in product_types:
        if t not in mappings:
            mappings[t] = "Autres"
    return mappings


def save_mapping(mapping: dict, path: str = "config/categories.yaml"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ["mappings:"]
    for key in sorted(mapping):
        lines.append(f'  "{key}": "{mapping[key]}"')
    lines.append('default: "Autres"')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Saved {len(mapping)} mappings to {path}")


if __name__ == "__main__":
    types = extract_types()
    print(f"Found {len(types)} unique product types")
    mapping = generate_mapping(types)
    save_mapping(mapping)
    print("Done")
