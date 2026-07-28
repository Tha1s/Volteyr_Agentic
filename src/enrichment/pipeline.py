from dataclasses import dataclass, field

from src.enrichment.models import Enrichment
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.persist import PersistStep


@dataclass
class EnrichmentPipeline:
    generate: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=False))
    generate_large: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=True))
    persist: PersistStep = field(default_factory=PersistStep)

    def run(self, products: list[dict], batch_size: int = 5, on_progress=None) -> tuple[int, int]:
        total_success = 0
        total_failures = 0
        total = len(products)
        for i in range(0, total, batch_size):
            batch = products[i : i + batch_size]
            results = self.generate.process(batch)
            success, failures = self.persist.process(results)
            total_success += success
            total_failures += failures
            if on_progress:
                on_progress(
                    progress=min(i + batch_size, total) / total,
                    success=total_success,
                    failures=total_failures,
                )
        return (total_success, total_failures)

    def run_single(self, product: dict) -> Enrichment | None:
        results = self.generate_large.process([product])
        return results[0] if results else None
