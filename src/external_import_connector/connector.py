import threading
import json
import time
import uuid
import os
import tempfile
import subprocess

from pycti import OpenCTIConnectorHelper
from .classification.classifier import DataClassifier
from .stix.handle_opencti_entity import OpenCTIEntityHandler
from .stix.opencti_handler import OpenCTIHandler
from .config_variables import ConfigConnector
from .db import DBSingleton


class DarcConnector:
    def __init__(self):
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        self.classifier = DataClassifier()
        self.db_handler = DBSingleton().get_instance()
        self.record_locks = {}  # Per-record locking mechanism
        self.global_lock = threading.Lock()  # For record_locks access
        # Initialize OpenCTI handler
        self.opencti_handler = OpenCTIHandler(self.helper)  # New instance
        self.entity_checker = OpenCTIEntityHandler(self.helper, self.config)

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

            # Perform classification only if missing
            self._perform_classification(record_data)

            # Process pipeline if criteria met
            success = True
            if self._meets_criteria(record_data["id"]):
                success = self._process_pipeline(record_data)

            # Only mark processed after all successful operations
            if success:
                self._safe_mark_processed(record_data["id"])

            return success
        except Exception as e:
            self.helper.connector_logger.error(
                f"Error processing record {record_data['id'] if record_data else 'unknown'}: {str(e)}",
                exc_info=True,
            )
            return False

    def _process_pipeline(self, record_data):
        """Handle processing steps only if criteria met"""
        try:
            # Check if entity exists before processing
            if self.entity_checker.entity_exists(record_data):
                self.helper.connector_logger.info(
                    f"Skipping existing entity: {record_data['name']}"
                )
                return True  # Consider existing entities as successfully processed

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

    def _txt_2_stix(self, report_id, record_data, working_dir):

        try:
            temp_file_path = None

            # Create a temporary file containing the record's HTML content
            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".txt"
            ) as temp_file:
                temp_file.write(record_data["html"])
                temp_file_path = temp_file.name

            # Build the txt2stix command using the provided parameters
            cmd = [
                "python3",
                "../txt2stix/txt2stix.py",
                "--relationship_mode",
                "ai",
                "--ai_settings_relationships",
                "deepseek:deepseek-chat",
                "--input_file",
                temp_file_path,
                "--name",
                f"Report {record_data['id']}",
                "--tlp_level",
                "clear",
                "--confidence",
                "90",
                "--use_extractions",
                "ai_*",
                "--ai_settings_extractions",
                "deepseek:deepseek-chat",
                "--report_id",
                report_id,
            ]

            self.helper.connector_logger.info(
                f"Executing txt2stix with command: {' '.join(cmd)}"
            )

            # Copy the current environment variables
            env = os.environ.copy()

            # Add or update the variable(s) you want the subprocess to see
            env["DEEPSEEK_API_KEY"] = self.config.deepseek_api_key
            env["INPUT_TOKEN_LIMIT"] = str(self.config.input_token_limit)
            env["TEMPERATURE"] = str(self.config.temperature)
            env["CTIBUTLER_BASE_URL"] = self.config.ctibutler_base_url
            env["CTIBUTLER_API_KEY"] = self.config.ctibutler_api_key
            env["VULMATCH_BASE_URL"] = self.config.vulmatch_base_url
            env["VULMATCH_API_KEY"] = self.config.vulmatch_api_key

            # Execute the txt2stix command and capture its output
            result = subprocess.run(
                cmd,
                cwd=working_dir,  # Critical for path resolution
                capture_output=False,
                text=False,
                check=True,
                env=env,
                start_new_session=True,
            )

            # Log subprocess output
            self.helper.connector_logger.debug(f"txt2stix stdout: {result.stdout}")
            if result.stderr:
                self.helper.connector_logger.warning(
                    f"txt2stix stderr: {result.stderr}"
                )

            return True
        except subprocess.CalledProcessError as e:
            self.helper.connector_logger.error(
                f"txt2stix failed for record {record_data['id']}:\n"
                f"Command: {' '.join(cmd)}\n"
                f"Error: {e.stderr}"
            )
            return False
        finally:
            # Cleanup the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    self.helper.connector_logger.error(
                        f"Error cleaning up temp file: {str(e)}"
                    )

    def _handle_deepseek(self, record_data):
        """Process txt2stix step with file synchronization and subprocess validation."""
        try:
            report_id = str(uuid.uuid4())
            output_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../output")
            )
            working_dir = os.path.dirname(output_dir)  # Parent of output directory

            # Create output directory if missing
            os.makedirs(output_dir, exist_ok=True)

            # Run txt2stix with explicit working directory
            self._txt_2_stix(report_id, record_data, working_dir)

            bundle_file = os.path.join(output_dir, f"bundle--{report_id}.json")
            data_file = os.path.join(output_dir, f"data--{report_id}.json")

            # Wait for files with exponential backoff
            max_retries = 4
            for i in range(max_retries):
                if all([os.path.exists(bundle_file), os.path.exists(data_file)]):
                    break
                time.sleep(2**i)  # 1s, 2s, 4s, etc.
            else:
                self.helper.connector_logger.error(
                    f"Files not ready after {max_retries} retries: "
                    f"{bundle_file} (exists: {os.path.exists(bundle_file)}), "
                    f"{data_file} (exists: {os.path.exists(data_file)})"
                )
                return False

            # Process files
            with open(data_file, "r") as f:
                stix_data = json.load(f)
            with open(bundle_file, "r") as f:
                stix_bundle = json.load(f)

            self.db_handler.mark_sent_to_deepseek(
                record_data["id"], stix_data, stix_bundle
            )

            # Cleanup files
            try:
                os.remove(data_file)
                os.remove(bundle_file)
            except Exception as e:
                self.helper.connector_logger.warning(f"File cleanup failed: {str(e)}")

            return True

        except Exception as e:
            self.helper.connector_logger.error(f"Deepseek processing failed: {str(e)}")
            return False

    def _handle_opencti(self, record_data):
        """Process OpenCTI step using the dedicated handler."""
        try:
            stix_data = self.db_handler.get_stix_bundle(record_data["id"])
            if not stix_data:
                self.helper.connector_logger.error(
                    f"Missing STIX data for {record_data['id']}"
                )
                return False

            stix_objects = stix_data.get("objects")
            if not isinstance(stix_objects, list):
                self.helper.connector_logger.error(
                    f"Invalid STIX structure for {record_data['id']}"
                )
                return False

            # Delegate to OpenCTI handler
            success = self.opencti_handler.send_stix_bundle(
                stix_objects, record_data["id"]
            )

            # Update DB only if successful
            if success:
                self.db_handler.mark_sent_to_opencti(record_data["id"])
            return success

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
        """Perform classification only if not already exists"""
        # Check existing classifications
        needs_v2 = not self.db_handler.get_classification_results(
            record_data["id"], "classification_results"
        )
        needs_v3 = not self.db_handler.get_classification_results(
            record_data["id"], "classification_results_v3"
        )

        if needs_v2 or needs_v3:
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

    def _log_processing_error(self, record_id, error):
        self.helper.connector_logger.error(
            f"Error processing record {record_id}: {str(error)}", exc_info=True
        )

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
