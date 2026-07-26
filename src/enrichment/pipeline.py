from dataclasses import dataclass, field

from src.enrichment.models import Enrichment
from src.enrichment.steps.generate import GenerateStep
from src.enrichment.steps.normalize import NormalizeStep
from src.enrichment.steps.persist import PersistStep


@dataclass
class EnrichmentPipeline:
    normalize: NormalizeStep = field(default_factory=NormalizeStep)
    generate: GenerateStep = field(default_factory=lambda: GenerateStep(use_large_model=False))
    persist: PersistStep = field(default_factory=PersistStep)

    def run(self, products: list[dict]) -> tuple[int, int]:
        normalized = self.normalize.process(products)
        results = self.generate.process(normalized)
        success, failures = self.persist.process(results)
        return (success, failures)

    def run_single(self, product: dict) -> Enrichment | None:
        normalized = self.normalize.process([product])
        gen = GenerateStep(use_large_model=True)
        results = gen.process(normalized)
        return results[0] if results else None
