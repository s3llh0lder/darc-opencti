import psycopg2
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

    def process_data(self) -> None:
        """Main processing workflow with per-record handling"""
        records = self.db_handler.fetch_unprocessed_data()
        if not records:
            self.helper.connector_logger.info("No new records to process")
            return

        processed_count = 0
        error_count = 0

        for record in records:
            record_id, url, keywords, html, timestamp = record
            success = False

            try:
                # Process individual record
                self.helper.connector_logger.debug(f"Processing record {record_id}")

                self.classifier.classify_data(html, record_id)

                # Convert content to STIX
                # stix_objects = self.deepseek_client.generate_stix_from_text(html)

                # if stix_objects:
                #     # Create and send individual bundle
                #     # bundle = self.helper.stix2_create_bundle(stix_objects)
                #     # self.helper.send_stix2_bundle(bundle)
                #     success = True
                #     processed_count += 1
                #     self.helper.connector_logger.info(f"Successfully processed record {record_id}")
                # else:
                #     self.helper.connector_logger.warning(f"Empty STIX conversion for record {record_id}")

            except Exception as e:
                error_count += 1
                self.helper.connector_logger.error(
                    f"Error processing record {record_id}: {str(e)}",
                    {"record_id": record_id, "error": str(e)},
                )
            finally:
                if success:
                    try:
                        self.db_handler.mark_as_processed(record_id)
                    except Exception as e:
                        error_count += 1
                        self.helper.connector_logger.error(
                            f"Failed to mark record {record_id} as processed: {str(e)}"
                        )

        # Final status report
        self.helper.connector_logger.info(
            f"Processing complete - Successful: {processed_count}, Failed: {error_count}, Total: {len(records)}"
        )

    def run(self) -> None:
        """Main execution scheduler"""
        self.helper.schedule_iso(
            message_callback=self.process_data,
            duration_period=self.config.duration_period,
        )
