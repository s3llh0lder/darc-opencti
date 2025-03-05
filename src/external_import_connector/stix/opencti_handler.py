import time
import json
from datetime import datetime, timezone

from pycti import OpenCTIApiClient


class OpenCTIHandler:
    """Handles all OpenCTI-specific operations including bundle creation and sending."""

    def __init__(self, client: OpenCTIApiClient, helper):
        self.helper = helper
        self.client = client

    def send_stix_bundle(self, bundle: dict, record_id: int) -> bool:
        """
        Validates and sends STIX objects to OpenCTI as a bundle.
        Returns True on success, False otherwise.
        """
        if not self._validate_stix_bundle(bundle, record_id):
            return False

        try:

            bundle_str = json.dumps(bundle)

            #
            # # Register work
            timestamp = int(time.time())

            now = datetime.fromtimestamp(timestamp, timezone.utc)
            friendly_name = f"DarcConnector run @ {now.strftime('%Y-%m-%d %H:%M:%S')}"
            work_id = self.helper.api.work.initiate_work(
                self.helper.connect_id, friendly_name
            )
            # # Send bundle : todo verify how this work cannot be done by helper: issue with missing references
            # self.helper.send_stix2_bundle(
            #     bundle_str,
            #     entities_types=self.helper.connect_scope,
            #     update=False,
            #     work_id=work_id,
            # )
            #
            self.client.stix2.import_bundle_from_json(bundle_str, False, None, work_id)

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

    def _validate_stix_bundle(self, bundle: dict, record_id: int) -> bool:
        """Validates STIX bundle structure."""
        if not isinstance(bundle, dict):
            self.helper.connector_logger.error(
                f"Invalid STIX format (record {record_id}): Expected dict, got {type(bundle)}"
            )
            return False
        if bundle.get("type") != "bundle":
            self.helper.connector_logger.error(
                f"Invalid STIX bundle (record {record_id}): Missing or incorrect 'type'"
            )
            return False
        if not isinstance(bundle.get("objects"), list):
            self.helper.connector_logger.error(
                f"Invalid STIX bundle (record {record_id}): Missing or invalid 'objects' list"
            )
            return False
        return True
