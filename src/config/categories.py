import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "categories.yaml"

DEFAULT_CATEGORIES = [
    "Pantalons", "Hauts", "Vestes & Manteaux", "Pulls & Maille",
    "Robes & Jupes", "Chemises", "Chaussures", "Sacs & Maroquinerie",
    "Bijoux", "Accessoires", "Lingerie", "Maillots De Bain",
    "Bébé & Enfant", "Autres",
]


def load_category_map() -> dict[str, str]:
    path = CONFIG_PATH
    if not path.exists():
        return {"default": "Autres"}
    text = path.read_text(encoding="utf-8")
    mapping = {}
    current_default = "Autres"
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("default:"):
            current_default = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif ":" in line and not line.startswith("#"):
            parts = line.split(":", 1)
            key = parts[0].strip().strip('"')
            val = parts[1].strip().strip('"')
            if key and val and key not in ("mappings", "default"):
                mapping[key] = val
    mapping["default"] = current_default
    for cat in DEFAULT_CATEGORIES:
        mapping.setdefault(cat, cat)
    return mapping


def _save_category_map(mapping: dict[str, str]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    default = mapping.pop("default", "Autres")
    lines = ["mappings:"]
    for key in sorted(mapping):
        lines.append(f'  "{key}": "{mapping[key]}"')
    lines.append(f'default: "{default}"')
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mapping["default"] = default
    for cat in DEFAULT_CATEGORIES:
        mapping.setdefault(cat, cat)


def auto_fill_categories(product_types: set[str]) -> None:
    existing = load_category_map()

    unknown = {t for t in product_types if t not in existing}
    if not unknown:
        return

    # Step 1: keyword-based matching for obvious types
    hard_to_match = set()
    for t in unknown:
        cat = _simple_match(t)
        if cat == "Autres":
            hard_to_match.add(t)
        else:
            existing[t] = cat

    if not hard_to_match:
        _save_category_map(existing)
        return

    # Step 2: LLM batch for remaining ambiguous types
    from src.llm.client import generate

    BATCH = 40
    types_list = sorted(hard_to_match)

    for start in range(0, len(types_list), BATCH):
        batch = types_list[start : start + BATCH]
        prompt = (
            "Assigne chaque type de produit à la catégorie la plus appropriée.\n\n"
            f"Catégories disponibles: {', '.join(DEFAULT_CATEGORIES)}\n\n"
            "Types de produits:\n" + "\n".join(f"- {t}" for t in batch) + "\n\n"
            'Réponds UNIQUEMENT au format JSON: {"mappings": {"Type": "Catégorie", ...}}\n'
            'Si un type ne correspond à aucune catégorie, utilise "Autres".'
        )

        response = generate(
            model="qwen2.5:1.5b",
            prompt=prompt,
            system="Tu es un expert en catégorisation de produits de mode. Réponds uniquement en JSON.",
            temperature=0.1,
        )

        if response is None:
            for t in batch:
                existing[t] = "Autres"
            continue

        try:
            data = json.loads(response)
            new_mappings = data.get("mappings", {})
        except (json.JSONDecodeError, AttributeError):
            new_mappings = {}

        for t in batch:
            cat = new_mappings.get(t, "Autres")
            if cat not in DEFAULT_CATEGORIES:
                cat = "Autres"
            existing[t] = cat

    _save_category_map(existing)


def _simple_match(product_type: str) -> str:
    t = product_type.lower()
    if any(w in t for w in ("pantalon", "pants", "trouser", "jeans", "denim", "jogging", "legging", "short", "bermuda", "cycliste")):
        return "Pantalons"
    if any(w in t for w in ("t-shirt", "tshirt", "tee", "tees", "top", "haut", "chemise", "shirt", "blouse", "tunique", "polo", "body", "blazer", "kimono")):
        return "Hauts"
    if any(w in t for w in ("veste", "manteau", "jacket", "coat", "doudoune", "parka", "gilet", "cardigan", "softshell", "blazer")):
        return "Vestes & Manteaux"
    if any(w in t for w in ("pull", "sweat", "sweater", "jumper", "knit", "maille", "teddy", "hoodie")):
        return "Pulls & Maille"
    if any(w in t for w in ("robe", "dress", "gown", "jupe", "skirt")):
        return "Robes & Jupes"
    if any(w in t for w in ("chaussure", "shoe", "basket", "sneaker", "derbie", "derby", "sandale", "sandal", "botte", "boot", "mule", "mocassin", "espadrille", "espadrilla", "tong", "slide", "ballerine", "escarpin", "pump", "sabot", "running", "chausson", "bateau", "talon")):
        return "Chaussures"
    if any(w in t for w in ("sac", "bag", "tote", "maroquinerie", "portefeuille", "pochette", "trousse", "wallet", "valise", "anse")):
        return "Sacs & Maroquinerie"
    if any(w in t for w in ("bijou", "bague", "bracelet", "collier", "boucle", "creole", "pendentif", "broche", "manchette", "bague")):
        return "Bijoux"
    if any(w in t for w in ("ceinture", "belt", "chapeau", "bonnet", "casquette", "foulard", "echarpe", "lunette", "parapluie", "gant", "mitaine", "cravate", "epingle", "casque", "masque", "foulard", "echarpe")):
        return "Accessoires"
    if any(w in t for w in ("lingerie", "soutien", "brassiere", "culotte", "string", "tanga", "boxer", "calecon", "body", "peignoir", "pyjama", "nuit", "nightwear")):
        return "Lingerie"
    if any(w in t for w in ("maillot", "bain", "swim", "bikini", "beach")):
        return "Maillots De Bain"
    if any(w in t for w in ("bebe", "nouveau ne", "enfant", "fille", "garcon", "boutchou")):
        return "Bébé & Enfant"
    return "Autres"


_CHILD_SUFFIX = re.compile(
    r'\s*-\s*(?:Bébé|Enfant|Fille|Garçon|Mixte|Homme|Femme).*$', re.IGNORECASE
)


def normalize_product_type(
    product_type: str, mapping: dict[str, str] | None = None
) -> str:
    if not product_type or not product_type.strip():
        return "Autres"
    raw = product_type.strip()
    name = _CHILD_SUFFIX.sub("", raw).strip()
    if mapping is None:
        mapping = load_category_map()
    default = mapping.get("default", "Autres")

    # Resolve chain, with terminal guard
    for _ in range(10):
        if name in mapping:
            if mapping[name] == name:
                return name
            name = mapping[name]
        elif raw != name and raw in mapping:
            name = mapping[raw]
        else:
            for key, val in mapping.items():
                if key.lower() == name.lower():
                    if val == name:
                        return name
                    name = val
                    break
            else:
                return name
    return default
