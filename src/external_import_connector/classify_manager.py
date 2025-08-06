from .record_repository import RecordRepository
from .classification.classifier import DataClassifier


class ClassificationManager:
    """Manages data classification workflow"""

    def __init__(self, classifier: DataClassifier, db: RecordRepository):
        self.classifier = classifier
        self.db = db

    def ensure_classification(self, record_data: dict) -> None:
        """Ensures V2/V3 classifications exist"""
        if self._needs_classification(record_data["id"]):
            self.classifier.classify_data(record_data["html"], record_data["id"])

    def _needs_classification(self, record_id: int) -> bool:
        return not self.db.get_classification_results(
            record_id, "classification_results"
        ) or not self.db.get_classification_results(
            record_id, "classification_results_v3"
        )
