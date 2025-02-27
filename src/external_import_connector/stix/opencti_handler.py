import time
from datetime import datetime


class OpenCTIHandler:
    """Handles all OpenCTI-specific operations including bundle creation and sending."""

    def __init__(self, helper):
        self.helper = helper

    def send_stix_bundle(self, stix_objects: list, record_id: int) -> bool:
        """
        Validates and sends STIX objects to OpenCTI as a bundle.
        Returns True on success, False otherwise.
        """
        if not self._validate_stix_objects(stix_objects, record_id):
            return False

        try:
            # Create STIX bundle
            bundle = self.helper.stix2_create_bundle(stix_objects)

            # Register work
            timestamp = int(time.time())
            now = datetime.utcfromtimestamp(timestamp)
            friendly_name = f"DarcConnector run @ {now.strftime('%Y-%m-%d %H:%M:%S')}"
            work_id = self.helper.api.work.initiate_work(
                self.helper.connect_id, friendly_name
            )

            # Send bundle
            self.helper.send_stix2_bundle(
                bundle,
                entities_types=self.helper.connect_scope,
                update=False,
                work_id=work_id,
            )

            # Finalize work
            message = (
                f"Processed record {record_id} at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.helper.api.work.to_processed(work_id, message)
            return True

        except Exception as e:
            self.helper.connector_logger.error(
                f"Failed to process bundle for record {record_id}: {str(e)}",
                exc_info=True,
            )
            return False

    def _validate_stix_objects(self, stix_objects: list, record_id: int) -> bool:
        """Validates STIX objects structure."""
        if not isinstance(stix_objects, list):
            self.helper.connector_logger.error(
                f"Invalid STIX format (record {record_id}): Expected list, got {type(stix_objects)}"
            )
            return False
        if not stix_objects:
            self.helper.connector_logger.warning(
                f"Empty STIX bundle for record {record_id}"
            )
            return False
        return True
