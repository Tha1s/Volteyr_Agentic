import json
from dataclasses import dataclass

from src.enrichment.factory import EnrichmentFactory
from src.enrichment.models import Enrichment
from src.llm.prompts import ENRICHMENT_SYSTEM, ENRICHMENT_USER
from src.llm.strategies import get_strategy


@dataclass
class GenerateStep:
    max_retries: int = 2
    use_large_model: bool = False

    def process(self, products: list[dict]) -> list[Enrichment | None]:
        results: list[Enrichment | None] = []
        total = len(products)
        strategy = get_strategy(self.use_large_model)
        model_used = strategy.model

        for i, product in enumerate(products):
            prompt = ENRICHMENT_USER.format(
                product_type=product.get("product_type", ""),
                category=product.get("category", ""),
                vendor=product.get("vendor", ""),
                description=product.get("description", ""),
            )
            result: Enrichment | None = None
            for attempt in range(self.max_retries + 1):
                response = strategy.generate(prompt, ENRICHMENT_SYSTEM)
                if response:
                    try:
                        data = json.loads(response)
                        if isinstance(data, dict):
                            result = EnrichmentFactory.from_llm_response(
                                product["product_id"], data, model_used
                            )
                            break
                    except json.JSONDecodeError as e:
                        print(f"JSON decode failed (attempt {attempt+1}): {e}")
            results.append(result)
            print(f"Generated {i+1}/{total}")

        return results
