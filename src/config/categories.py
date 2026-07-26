import functools
import re
import unicodedata
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "categories.yaml"

DEFAULT_CATEGORIES = [
    "Pantalons", "Hauts", "Vestes & Manteaux", "Pulls & Maille",
    "Robes & Jupes", "Chemises", "Chaussures", "Sacs & Maroquinerie",
    "Bijoux", "Accessoires", "Lingerie", "Maillots De Bain",
    "Bébé & Enfant", "Autres",
]


@functools.lru_cache(maxsize=1)
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

    for t in unknown:
        existing[t] = _simple_match(t)

    _save_category_map(existing)



_CAT_KEYWORDS = {
    "Pantalons": ("pantalon", "pants", "trouser", "jeans", "denim", "jogging", "legging", "short", "bermuda", "cycliste"),
    "Hauts": ("t-shirt", "tshirt", "tee", "tees", "top", "haut", "chemise", "shirt", "blouse", "tunique", "polo", "body", "blazer", "kimono"),
    "Vestes & Manteaux": ("veste", "manteau", "jacket", "coat", "doudoune", "parka", "gilet", "cardigan", "softshell", "blazer"),
    "Pulls & Maille": ("pull", "sweat", "sweater", "jumper", "knit", "maille", "teddy", "hoodie"),
    "Robes & Jupes": ("robe", "dress", "gown", "jupe", "skirt"),
    "Chaussures": ("chaussure", "shoe", "basket", "sneaker", "derbie", "derby", "sandale", "sandal", "botte", "boot", "mule", "mocassin", "espadrille", "espadrilla", "tong", "slide", "ballerine", "escarpin", "pump", "sabot", "running", "chausson", "bateau", "talon"),
    "Sacs & Maroquinerie": ("sac", "bag", "tote", "maroquinerie", "portefeuille", "pochette", "trousse", "wallet", "valise", "anse"),
    "Bijoux": ("bijou", "bague", "bracelet", "collier", "boucle", "creole", "pendentif", "broche", "manchette", "bague"),
    "Accessoires": ("ceinture", "belt", "chapeau", "bonnet", "casquette", "foulard", "echarpe", "lunette", "parapluie", "gant", "mitaine", "cravate", "epingle", "casque", "masque"),
    "Lingerie": ("lingerie", "soutien", "brassiere", "culotte", "string", "tanga", "boxer", "calecon", "body", "peignoir", "pyjama", "nuit", "nightwear"),
    "Maillots De Bain": ("maillot", "bain", "swim", "bikini", "beach"),
    "Bébé & Enfant": ("bebe", "nouveau ne", "enfant", "fille", "garcon", "boutchou"),
}


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")


def _simple_match(product_type: str | None) -> str:
    if not product_type or not product_type.strip():
        return "Autres"
    t = _strip_accents(product_type.lower())
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
