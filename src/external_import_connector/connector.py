import requests
import psycopg2
from pycti import OpenCTIConnectorHelper
from psycopg2 import sql

from .client_api import ConnectorClient
from .config_variables import ConfigConnector

class DarcConnector:
    def __init__(self):
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        self.deepseek_client = ConnectorClient(self.helper, self.config)

        # Database connection
        self.db_conn = psycopg2.connect(
            dbname=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
            host=self.config.db_host,
            port=self.config.db_port,
        )
        self.db_cursor = self.db_conn.cursor()

    def fetch_unprocessed_data(self):
        """Fetch unprocessed records from database"""
        query = """
            SELECT id, url, matched_keywords, html, timestamp 
            FROM db.matched_content 
            WHERE uploaded = FALSE
        """
        self.db_cursor.execute(query)
        return self.db_cursor.fetchall()

    def mark_as_uploaded(self, record_id):
        """Mark record as processed in database"""
        update_query = sql.SQL(
            "UPDATE db.matched_content SET uploaded = TRUE WHERE id = %s"
        )
        self.db_cursor.execute(update_query, (record_id,))
        self.db_conn.commit()

    def process_data(self) -> None:
        """Main processing workflow"""
        records = self.fetch_unprocessed_data()
        if not records:
            self.helper.connector_logger.info("No new records to process")
            return

        all_stix_objects = []
        processed_ids = []

        for record in records:
            record_id, url, keywords, html, timestamp = record

            # Convert content to STIX
            stix_objects = self.deepseek_client.generate_stix_from_text(html)
            self.helper.connector_logger.info(f"Created STIX object {stix_objects}")

            if stix_objects:
                all_stix_objects.extend(stix_objects)
                processed_ids.append(record_id)
                self.helper.connector_logger.debug(f"Processed record {record_id}")
            else:
                self.helper.connector_logger.warning(f"Failed to process record {record_id}")

        # Send all STIX objects in a single bundle
        # if all_stix_objects:
        #     bundle = self.helper.stix2_create_bundle(all_stix_objects)
        #     self.helper.send_stix2_bundle(bundle)
        #     self.helper.connector_logger.info(
        #         f"Successfully sent {len(all_stix_objects)} STIX objects"
        #     )

            # Mark records as uploaded only after successful processing
            for record_id in processed_ids:
                self.mark_as_uploaded(record_id)

    def run(self) -> None:
        """Main execution scheduler"""
        self.helper.schedule_iso(
            message_callback=self.process_data,
            duration_period=self.config.duration_period,
        )