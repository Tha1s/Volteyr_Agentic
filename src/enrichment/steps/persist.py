from dataclasses import dataclass, field

from src.db.enrichment_repository import EnrichmentRepository
from src.enrichment.models import Enrichment


@dataclass
class PersistStep:
    repo: EnrichmentRepository = field(default_factory=EnrichmentRepository)

    def process(self, enrichments: list[Enrichment | None]) -> tuple[int, int]:
        success = 0
        failures = 0
        for enrichment in enrichments:
            if enrichment is None:
                failures += 1
                continue
            self.repo.delete_by_product_id(enrichment.product_id)
            self.repo.save(enrichment)
            success += 1
        print(f"Persisted {success} enrichments, {failures} failures")
        return (success, failures)
