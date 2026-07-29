from dataclasses import dataclass, field

from src.enrichment.models import Enrichment
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.persist import PersistStep


@dataclass
class EnrichmentPipeline:
    generate: GenerateStep | None = None
    generate_large: GenerateStep | None = None
    persist: PersistStep | None = None

    def __post_init__(self):
        if self.generate is None:
            self.generate = GenerateStep(use_large_model=False)
        if self.generate_large is None:
            self.generate_large = GenerateStep(use_large_model=True)
        if self.persist is None:
            self.persist = PersistStep()

    def run(self, products: list[dict], batch_size: int = 5, use_large_model: bool = False, on_progress=None) -> tuple[int, int]:
        step = self.generate_large if use_large_model else self.generate
        total_success = 0
        total_failures = 0
        total = len(products)
        for i in range(0, total, batch_size):
            batch = products[i : i + batch_size]
            results = step.process(batch)
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
