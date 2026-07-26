from dataclasses import dataclass, field

from src.enrichment.models import Enrichment
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.persist import PersistStep


@dataclass
class EnrichmentPipeline:
    generate: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=False))
    persist: PersistStep = field(default_factory=PersistStep)

    def run(self, products: list[dict]) -> tuple[int, int]:
        results = self.generate.process(products)
        success, failures = self.persist.process(results)
        return (success, failures)

    def run_single(self, product: dict) -> Enrichment | None:
        gen = GenerateStep(use_large_model=True)
        results = gen.process([product])
        return results[0] if results else None
