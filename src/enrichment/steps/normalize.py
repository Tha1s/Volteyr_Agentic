from dataclasses import dataclass

from src.config.categories import normalize_product_type


@dataclass
class NormalizeStep:

    def process(self, products: list[dict]) -> list[dict]:
        count = 0
        for product in products:
            product.setdefault("category", None)
            if not product["category"]:
                product["category"] = normalize_product_type(product["product_type"])
                count += 1
        if count:
            print(f"Normalized {count} product types")
        return products
