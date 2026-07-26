from dataclasses import dataclass, field

from src.enrichment.models import Enrichment
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.persist import PersistStep


@dataclass
class EnrichmentPipeline:
    generate: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=False))
    persist: PersistStep = field(default_factory=PersistStep)

    def run(self, products: list[dict], batch_size: int = 5) -> tuple[int, int]:
        total_success = 0
        total_failures = 0
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            results = self.generate.process(batch)
            success, failures = self.persist.process(results)
            total_success += success
            total_failures += failures
        return (total_success, total_failures)

    def run_single(self, product: dict) -> Enrichment | None:
        gen = GenerateStep(use_large_model=True)
        results = gen.process([product])
        return results[0] if results else None
