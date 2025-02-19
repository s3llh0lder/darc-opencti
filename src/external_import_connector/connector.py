import threading
import psycopg2
import time
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
                success = self._process_record(record)

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

    def _process_record(self, record: tuple) -> bool:
        """Thread-safe single record processing"""
        record_id, url, keywords, html, timestamp = record
        self.helper.connector_logger.debug(f"Processing record {record_id}")

        try:
            # Classification
            self.classifier.classify_data(html, record_id)

            # STIX Conversion (using the mock method for now)
            stix_data = self.deepseek_client.generate_stix_from_text_mock(html)
            # If a bundle dict is returned, extract the list of objects
            if isinstance(stix_data, dict) and "objects" in stix_data:
                stix_objects = stix_data["objects"]
            else:
                stix_objects = stix_data

            # Validation now checks the extracted list
            if not self._validate_stix_objects(stix_objects, record_id):
                return False

            # Bundle Handling (currently commented out)
            if not self._handle_bundle(stix_objects, record_id):
                return False

            # Mark processed
            self._safe_mark_processed(record_id)
            return True

        except Exception as e:
            self.helper.connector_logger.error(
                f"Error processing record {record_id}: {str(e)}",
                {"record_id": record_id, "error": str(e)},
                exc_info=True
            )
            return False

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
            work_id = self.helper.api.work.initiate_work(self.helper.connect_id, friendly_name)

            # Send the STIX2 bundle, passing the work_id and connector scope (as entity types)
            self.helper.send_stix2_bundle(
                bundle,
                entities_types=self.helper.connect_scope,
                update=False,
                work_id=work_id,
            )

            self.helper.connector_logger.info(f"Successfully processed record {record_id}")

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