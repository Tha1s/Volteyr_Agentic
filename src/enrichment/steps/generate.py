import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from src.enrichment.factory import EnrichmentFactory
from src.enrichment.models import Enrichment
from src.llm.prompts import ENRICHMENT_SYSTEM, ENRICHMENT_USER
from src.llm.strategies import get_strategy

logger = logging.getLogger(__name__)


@dataclass
class GenerateStep:
    max_retries: int = 1
    max_workers: int = 4
    use_large_model: bool = False

    def _call_llm(self, prompt: str, product_id: int, strategy, model_used: str) -> Enrichment | None:
        for attempt in range(self.max_retries + 1):
            response = strategy.generate(prompt, ENRICHMENT_SYSTEM)
            if response:
                try:
                    data = json.loads(response)
                    if isinstance(data, dict):
                        return EnrichmentFactory.from_llm_response(
                            product_id, data, model_used
                        )
                    break
                except json.JSONDecodeError:
                    logger.warning("JSON decode failed (attempt %d)", attempt + 1)
        return None

    def process(self, products: list[dict]) -> list[Enrichment | None]:
        total = len(products)
        if total == 0:
            return []
        strategy = get_strategy(self.use_large_model)
        model_used = strategy.model

        prompts = [
            ENRICHMENT_USER.format(
                product_type=p.get("product_type", ""),
                category=p.get("category", ""),
                vendor=p.get("vendor", ""),
                description=p.get("description", ""),
            )
            for p in products
        ]

        results: list[Enrichment | None] = [None] * total
        max_workers = min(self.max_workers, total)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._call_llm, prompts[i], p["product_id"], strategy, model_used): i
                for i, p in enumerate(products)
            }
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
        logger.info("Generated %d/%d enrichments", total, total)
        return results
