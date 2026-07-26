import os
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "categories.yaml"


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
    return mapping


_CHILD_SUFFIX = re.compile(
    r'\s*-\s*(?:Bébé|Enfant|Fille|Garçon|Mixte|Homme|Femme).*$', re.IGNORECASE
)


def normalize_product_type(
    product_type: str, mapping: dict[str, str] | None = None
) -> str:
    if not product_type or not product_type.strip():
        return "Autres"
    name = _CHILD_SUFFIX.sub("", product_type.strip()).strip()
    if mapping is None:
        mapping = load_category_map()
    default = mapping.get("default", "Autres")
    if name in mapping:
        return normalize_product_type(mapping[name], mapping)
    for key, val in mapping.items():
        if key.lower() == name.lower():
            return normalize_product_type(val, mapping)
    return default
