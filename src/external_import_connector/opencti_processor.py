from pycti import OpenCTIConnectorHelper

from .record_repository import RecordRepository
from .stix.handle_opencti_entity import OpenCTIEntityHandler
from .stix.opencti_handler import OpenCTIHandler
from .config_variables import ConfigConnector


class OpenCTIProcessor:
    """Handles OpenCTI communication"""

    def __init__(self, helper: OpenCTIConnectorHelper, db: RecordRepository):
        self.handler = OpenCTIHandler(helper)
        self.entity_checker = OpenCTIEntityHandler(helper, ConfigConnector())
        self.db = db

    def process(self, record_data: dict) -> bool:
        if self.entity_checker.entity_exists(record_data):
            return True  # Skip existing entities

        stix_data = self.db.get_stix_bundle(record_data["id"])
        if not stix_data or not isinstance(stix_data, dict) or not isinstance(stix_data.get("objects"), list):
            return False

        if self.handler.send_stix_bundle(stix_data, record_data["id"]):
            self.db.mark_opencti_complete(record_data["id"])
            return True
        return False
