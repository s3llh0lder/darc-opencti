import json
import time
import uuid
import os

from .config_variables import ConfigConnector
from .record_repository import RecordRepository
from .stix_converter import StixConverter


class Text2StixProcessor:
    """Handles Txt2Stix integration and file management"""

    def __init__(self, config: ConfigConnector, db: RecordRepository, logger):
        self.config = config
        self.db = db
        self.logger = logger
        self.stix_converter = StixConverter(config, logger)

    def process(self, record_data: dict) -> bool:
        report_id = str(uuid.uuid4())
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../output")
        )
        working_dir = os.path.dirname(output_dir)

        os.makedirs(output_dir, exist_ok=True)

        if not self.stix_converter.convert(report_id, record_data, working_dir):
            return False

        return self._validate_and_store_output(report_id, output_dir, record_data["id"])

    def _validate_and_store_output(
        self, report_id: str, output_dir: str, record_id: int
    ) -> bool:
        bundle_file = os.path.join(output_dir, f"bundle--{report_id}.json")
        data_file = os.path.join(output_dir, f"data--{report_id}.json")

        for _ in range(4):
            if all(os.path.exists(f) for f in [bundle_file, data_file]):
                break
            time.sleep(2**_)
        else:
            self.logger.error(f"Output files missing for {record_id}")
            return False

        try:
            with open(data_file) as f:
                stix_data = json.load(f)
            with open(bundle_file) as f:
                stix_bundle = json.load(f)

            # Replace all 'relationship_type' values with 'related-to' in the bundle
            for obj in stix_bundle.get("objects", []):
                if "relationship_type" in obj:
                    obj["relationship_type"] = "related-to"

            self.db.mark_deepseek_complete(record_id, stix_data, stix_bundle)
            return True
        finally:
            for f in [data_file, bundle_file]:
                try:
                    os.remove(f)
                except Exception as e:
                    self.logger.warning(f"Cleanup failed for {f}: {str(e)}")
