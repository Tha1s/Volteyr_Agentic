import functools
import re
import unicodedata
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "categories.yaml"

DEFAULT_CATEGORIES = [
    "Pantalons & Shorts", "Hauts", "Vestes & Manteaux", "Pulls & Maille",
    "Robes & Jupes", "Chaussures", "Sacs & Maroquinerie",
    "Bijoux", "Accessoires", "Lingerie", "Maillots De Bain",
    "Bébé & Enfant", "Pyjamas", "Autres",
]


@functools.lru_cache(maxsize=1)
def load_category_map() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {"default": "Autres"}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {"default": "Autres"}
    mappings = data.get("mappings", {})
    if not isinstance(mappings, dict):
        mappings = {}
    default = data.get("default", "Autres")
    mapping = {k: v for k, v in mappings.items() if k and v}
    mapping["default"] = default
    for cat in DEFAULT_CATEGORIES:
        mapping.setdefault(cat, cat)
    return mapping


def _save_category_map(mapping: dict[str, str]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    default = mapping.pop("default", "Autres")
    data = {"mappings": dict(sorted(mapping.items())), "default": default}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    mapping["default"] = default
    for cat in DEFAULT_CATEGORIES:
        mapping.setdefault(cat, cat)


def auto_fill_categories(product_types: set[str]) -> None:
    existing = load_category_map()

    unknown = {t for t in product_types if t not in existing}
    if not unknown:
        return

    for t in unknown:
        existing[t] = _simple_match(t)

    _save_category_map(existing)



_CAT_KEYWORDS = {
    "Pantalons & Shorts": ("pantalon", "pants", "trouser", "jeans", "denim", "jogging", "legging", "short", "bermuda", "cycliste"),
    "Hauts": ("t-shirt", "tshirt", "tee", "tees", "top", "haut", "chemise", "shirt", "blouse", "tunique", "polo", "body", "bodie", "blazer", "kimono", "combinaison"),
    "Vestes & Manteaux": ("veste", "manteau", "jacket", "coat", "doudoune", "parka", "gilet", "cardigan", "softshell", "blazer"),
    "Pulls & Maille": ("pull", "sweat", "sweater", "jumper", "knit", "maille", "teddy", "hoodie"),
    "Robes & Jupes": ("robe", "dress", "gown", "jupe", "skirt"),
    "Chaussures": ("chaussure", "shoe", "basket", "sneaker", "derbie", "derby", "sandale", "sandal", "botte", "bottine", "boot", "mule", "mocassin", "espadrille", "espadrilla", "tong", "slide", "ballerine", "escarpin", "pump", "sabot", "running", "chausson", "bateau", "talon"),
    "Bijoux": ("bijou", "bague", "bracelet", "collier", "boucle", "creole", "pendentif", "broche", "manchette"),
    "Sacs & Maroquinerie": ("sac", "bag", "tote", "maroquinerie", "portefeuille", "pochette", "trousse", "wallet", "valise", "anse"),
    "Accessoires": ("accessoire", "ceinture", "belt", "chapeau", "bonnet", "casquette", "foulard", "echarpe", "lunette", "parapluie", "gant", "mitaine", "cravate", "epingle", "casque", "masque"),
    "Lingerie": ("lingerie", "soutien", "brassiere", "culotte", "string", "tanga", "boxer", "calecon", "body", "peignoir"),
    "Maillots De Bain": ("maillot", "bain", "swim", "bikini", "beach"),
    "Bébé & Enfant": ("bebe", "nouveau ne", "enfant", "fille", "garcon", "boutchou"),
    "Pyjamas": ("pyjama", "nuit", "nightwear"),
}


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")


def _simple_match(product_type: str | None) -> str:
    if not product_type or not product_type.strip():
        return "Autres"
    t = _strip_accents(product_type.lower())
    for cat in DEFAULT_CATEGORIES:
        if t == _strip_accents(cat.lower()):
            return cat
    for category, keywords in _CAT_KEYWORDS.items():
        if any(w in t for w in keywords):
            return category
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
