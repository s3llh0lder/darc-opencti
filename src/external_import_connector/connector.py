import threading
import time
import json
from datetime import datetime
from pycti import OpenCTIConnectorHelper
from .classification.classifier import DataClassifier
from .client_api import ConnectorClient
from .config_variables import ConfigConnector
from .db import DBSingleton


class DarcConnector:
    def __init__(self):
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        self.deepseek_client = ConnectorClient(self.helper, self.config)
        self.classifier = DataClassifier()
        self.db_handler = DBSingleton().get_instance()
        self.record_locks = {}  # Per-record locking mechanism
        self.global_lock = threading.Lock()  # For record_locks access

    def process_data(self) -> None:
        """Orchestrates thread-safe record processing"""
        with self.global_lock:
            records = self.db_handler.fetch_unprocessed_data()
            if not records:
                self.helper.connector_logger.info("No new records to process")
                return

        processed_count = 0
        error_count = 0

        for record in records:
            record_id = record[0]
            with self._get_record_lock(record_id):
                success = self._process_single_record(record)

                if success:
                    processed_count += 1
                else:
                    error_count += 1

        self.helper.connector_logger.info(
            f"Processing complete - Successful: {processed_count}, Failed: {error_count}, Total: {len(records)}"
        )

    def _get_record_lock(self, record_id: int) -> threading.Lock:
        """Get or create record-specific lock"""
        with self.global_lock:
            if record_id not in self.record_locks:
                self.record_locks[record_id] = threading.Lock()
            return self.record_locks[record_id]

    def _process_single_record(self, record: tuple) -> bool:
        try:
            record_data = self._unpack_record(record)
            if not record_data:
                return False

            self._perform_classification(record_data)

            # Always mark processed after classification
            self._safe_mark_processed(record_data["id"])

            # Only process steps if criteria met
            if self._meets_criteria(record_data["id"]):
                return self._process_pipeline(record_data)

            return True  # Marked processed but no further action
        except Exception as e:
            self.helper.connector_logger.error(
                f"Error processing single record {str(e)}"
            )
            return False

    def _process_pipeline(self, record_data):
        """Handle processing steps only if criteria met"""
        try:
            if not record_data["sent_to_deepseek"]:
                if not self._handle_deepseek(record_data):
                    return False

            if not record_data["sent_to_opencti"]:
                if not self._handle_opencti(record_data):
                    return False

            return True
        except Exception as e:
            self.helper.connector_logger.error(
                f"Error processing pipline for record id: {record_data['id']} {str(e)}"
            )
            return False

    def _handle_deepseek(self, record_data):
        """Process DeepSeek step only if not already done"""
        stix_data = self.deepseek_client.generate_stix_from_text(
            record_data["html"]
        )
        if not self._validate_stix_objects(
            stix_data.get("objects", []), record_data["id"]
        ):
            return False
        self.db_handler.mark_sent_to_deepseek(record_data["id"], stix_data)
        return True

    def _handle_opencti(self, record_data):
        """Process OpenCTI step only if not already done"""
        try:
            stix_data = self.db_handler.get_stix_data(record_data["id"])
            if not stix_data:
                self.helper.connector_logger.error(
                    f"Missing STIX data for {record_data['id']}"
                )
                return False

            # Ensure we have the objects list
            if not isinstance(stix_data.get("objects"), list):
                self.helper.connector_logger.error(
                    f"Invalid STIX structure for {record_data['id']}"
                )
                return False

            return self._handle_bundle(stix_data["objects"], record_data["id"])
        except json.JSONDecodeError as e:
            self.helper.connector_logger.error(
                f"Invalid JSON for {record_data['id']}: {str(e)}"
            )
            return False

    def _unpack_record(self, record):
        try:
            return {
                "id": record[0],
                "url": record[1],
                "keywords": record[2],
                "html": record[3],
                "timestamp": record[4],
                "sent_to_deepseek": record[5],
                "sent_to_opencti": record[6],
            }
        except IndexError:
            self.helper.connector_logger.error("Invalid record format")
            return None

    def _perform_classification(self, record_data):
        self.classifier.classify_data(record_data["html"], record_data["id"])

    def _meets_criteria(self, record_id):
        classification_v2 = self.db_handler.get_classification_results(
            record_id, "classification_results"
        )
        classification_v3 = self.db_handler.get_classification_results(
            record_id, "classification_results_v3"
        )

        return (
            classification_v2
            and classification_v3
            and classification_v2["category"] == "Exploit"
            and classification_v3["category"] == "Exploit"
            and classification_v2["confidence"] > 0.9
            and classification_v3["confidence"] > 0.9
        )

    def _process_deepseek_step(self, record_data):
        if record_data["sent_to_deepseek"]:
            return True

        stix_data = self.deepseek_client.generate_stix_from_text_mock(
            record_data["html"]
        )
        if not self._validate_stix_objects(
            stix_data.get("objects", []), record_data["id"]
        ):
            return False

        self.db_handler.mark_sent_to_deepseek(record_data["id"], stix_data)
        return True

    def _process_opencti_step(self, record_data):
        if record_data["sent_to_opencti"]:
            return True

        self.db_handler.mark_sent_to_opencti(record_data["id"])
        return True

    def _log_processing_error(self, record_id, error):
        self.helper.connector_logger.error(
            f"Error processing record {record_id}: {str(error)}", exc_info=True
        )

    def _validate_stix_objects(self, stix_objects: list, record_id: int) -> bool:
        """Validate STIX objects structure"""
        if not isinstance(stix_objects, list):
            self.helper.connector_logger.error(
                f"Invalid STIX format for record {record_id}: Expected list, got {type(stix_objects)}"
            )
            return False
        if not stix_objects:
            self.helper.connector_logger.warning(
                f"Empty STIX conversion for record {record_id}"
            )
            return False
        return True

    def _handle_bundle(self, stix_objects: list, record_id: int) -> bool:
        """Handle bundle creation and sending with work registration"""
        try:
            # Create a serialized STIX2 bundle from the list of objects
            bundle = self.helper.stix2_create_bundle(stix_objects)

            # Register a work item before sending the bundle
            timestamp = int(time.time())
            now = datetime.utcfromtimestamp(timestamp)
            friendly_name = f"DarcConnector run for record {record_id} @ {now.strftime('%Y-%m-%d %H:%M:%S')}"
            work_id = self.helper.api.work.initiate_work(
                self.helper.connect_id, friendly_name
            )

            # Send the STIX2 bundle, passing the work_id and connector scope (as entity types)
            self.helper.send_stix2_bundle(
                bundle,
                entities_types=self.helper.connect_scope,
                update=False,
                work_id=work_id,
            )

            self.helper.connector_logger.info(
                f"Successfully processed record {record_id}"
            )

            # Mark the work as processed with a success message
            message = f"Processed record {record_id} successfully at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            self.helper.api.work.to_processed(work_id, message)

            return True

        except Exception as e:
            self.helper.connector_logger.error(
                f"Bundle error for record {record_id}: {str(e)}",
                {"record_id": record_id, "error": str(e)},
            )
            return False

    def _safe_mark_processed(self, record_id: int) -> None:
        """Atomic mark-as-processed operation"""
        try:
            with self.global_lock:
                self.db_handler.mark_as_processed(record_id)
        except Exception as e:
            self.helper.connector_logger.error(
                f"Failed to mark record {record_id} as processed: {str(e)}"
            )

    def run(self) -> None:
        """Main execution scheduler"""
        self.helper.schedule_iso(
            message_callback=self.process_data,
            duration_period=self.config.duration_period,
        )
