import logging
from dataclasses import dataclass, field

from src.db.enrichment_repository import EnrichmentRepository
from src.enrichment.models import Enrichment

logger = logging.getLogger(__name__)


@dataclass
class PersistStep:
    repo: EnrichmentRepository = field(default_factory=EnrichmentRepository)

    def process(self, enrichments: list[Enrichment | None]) -> tuple[int, int]:
        success = 0
        failures = 0
        conn = self.repo.conn
        for enrichment in enrichments:
            if enrichment is None:
                failures += 1
                continue
            conn.execute("BEGIN TRANSACTION")
            try:
                self.repo.delete_by_product_id(enrichment.product_id)
                self.repo.save_from_dict(**enrichment.to_dict)
                conn.execute("COMMIT")
                success += 1
            except Exception:
                conn.execute("ROLLBACK")
                failures += 1
        logger.info("Persisted %d enrichments, %d failures", success, failures)
        return (success, failures)
