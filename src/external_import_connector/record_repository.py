from .db import DBSingleton
from typing import Optional, Dict, Any


class RecordRepository:
    """Handles database operations for records"""

    def __init__(self):
        self.db_handler = DBSingleton().get_instance()

    def fetch_unprocessed(self) -> list:
        return self.db_handler.fetch_unprocessed_data()

    def mark_processed(self, record_id: int) -> None:
        self.db_handler.mark_as_processed(record_id)

    def get_stix_bundle(self, record_id: int) -> Optional[dict]:
        return self.db_handler.get_stix_bundle(record_id)

    def mark_deepseek_complete(
        self, record_id: int, stix_data: dict, stix_bundle: dict
    ) -> None:
        self.db_handler.mark_sent_to_deepseek(record_id, stix_data, stix_bundle)

    def mark_opencti_complete(self, record_id: int) -> None:
        self.db_handler.mark_sent_to_opencti(record_id)

    def get_classification_results(
        self, record_id: int, table_name: str
    ) -> Optional[dict]:
        """Retrieve classification results from specified table"""
        return self.db_handler.get_classification_results(record_id, table_name)

    @staticmethod
    def unpack_record(record: tuple) -> Optional[Dict[str, Any]]:
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
            return None
