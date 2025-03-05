from pycti import OpenCTIApiClient, OpenCTIConnectorHelper
from .classification.classifier import DataClassifier
from .classify_manager import ClassificationManager
from .config_variables import ConfigConnector
from .lock_manager import LockManager
from .opencti_processor import OpenCTIProcessor
from .record_repository import RecordRepository
from .text_to_stix_processor import Text2StixProcessor


class DarcConnector:
    """Orchestrates record processing with thread safety"""

    def __init__(self):
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        self.client = OpenCTIApiClient(self.config.url, self.config.token)
        self.logger = self.helper.connector_logger

        # Initialize components
        self.db = RecordRepository()
        self.lock_manager = LockManager()
        self.classifier = ClassificationManager(DataClassifier(), self.db)
        self.deepseek_processor = Text2StixProcessor(self.config, self.db, self.logger)
        self.opencti_processor = OpenCTIProcessor(self.client, self.helper, self.db)

    def process_data(self) -> None:
        """Main processing loop"""
        with self.lock_manager.global_lock:
            records = self.db.fetch_unprocessed()
            if not records:
                self.logger.info("No new records to process")
                return

        results = {"success": 0, "errors": 0}
        for record in records:
            record_data = self.db.unpack_record(record)
            if not record_data:
                continue

            with self.lock_manager.acquire_record_lock(record_data["id"]):
                results[
                    "success" if self._process_record(record_data) else "errors"
                ] += 1

        self.logger.info(
            f"Processing complete - Successful: {results['success']}, Failed: {results['errors']}"
        )

    def _process_record(self, record_data: dict) -> bool:
        try:
            self.classifier.ensure_classification(record_data)

            if not self._meets_criteria(record_data["id"]):
                return False

            return self._execute_pipeline(record_data)
        except Exception as e:
            self.logger.error(
                f"Error processing {record_data['id']}: {str(e)}", exc_info=True
            )
            return False

    def _meets_criteria(self, record_id: int) -> bool:
        v2 = self.db.get_classification_results(record_id, "classification_results")
        v3 = self.db.get_classification_results(record_id, "classification_results_v3")
        return (
            v2
            and v3
            and v2["category"] == "Exploit"
            and v3["category"] == "Exploit"
            and v2["confidence"] > 0.9
            and v3["confidence"] > 0.9
        )

    def _execute_pipeline(self, record_data: dict) -> bool:
        """Executes DeepSeek -> OpenCTI processing pipeline"""
        try:
            if not record_data[
                "sent_to_deepseek"
            ] and not self.deepseek_processor.process(record_data):
                return False
            if not record_data[
                "sent_to_opencti"
            ] and not self.opencti_processor.process(record_data):
                return False
            self.db.mark_processed(record_data["id"])
            return True
        except Exception as e:
            self.logger.error(f"Pipeline failed for {record_data['id']}: {str(e)}")
            return False

    def run(self) -> None:
        """Main execution entry point"""
        self.helper.schedule_iso(
            message_callback=self.process_data,
            duration_period=self.config.duration_period,
        )
