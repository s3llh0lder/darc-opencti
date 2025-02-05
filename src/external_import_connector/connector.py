import psycopg2

from pycti import OpenCTIConnectorHelper

from psycopg2 import sql

from .config_variables import ConfigConnector
from .converter_to_stix import ConverterToStix


class DarcConnector:
    """
    Specifications of the external import connector

    This class encapsulates the main actions, expected to be run by any external import connector.
    Note that the attributes defined below will be complemented per each connector type.
    This type of connector aim to fetch external data to create STIX bundle and send it in a RabbitMQ queue.
    The STIX bundle in the queue will be processed by the workers.
    This type of connector uses the basic methods of the helper.

    ---

    Attributes
        - `config (ConfigConnector())`:
            Initialize the connector with necessary configuration environment variables

        - `helper (OpenCTIConnectorHelper(config))`:
            This is the helper to use.
            ALL connectors have to instantiate the connector helper with configurations.
            Doing this will do a lot of operations behind the scene.

        - `converter_to_stix (ConnectorConverter(helper))`:
            Provide methods for converting various types of input data into STIX 2.1 objects.

    ---

    Best practices
        - `self.helper.api.work.initiate_work(...)` is used to initiate a new work
        - `self.helper.schedule_iso()` is used to encapsulate the main process in a scheduler
        - `self.helper.connector_logger.[info/debug/warning/error]` is used when logging a message
        - `self.helper.stix2_create_bundle(stix_objects)` is used when creating a bundle
        - `self.helper.send_stix2_bundle(stix_objects_bundle)` is used to send the bundle to RabbitMQ
        - `self.helper.set_state()` is used to set state

    """

    def __init__(self):
        """
        Initialize the Connector with necessary configurations
        """

        # Load configuration file and connection helper
        self.config = ConfigConnector()
        self.helper = OpenCTIConnectorHelper(self.config.load)
        # self.client = ConnectorClient(self.helper, self.config)
        self.converter_to_stix = ConverterToStix(self.helper)

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
        """Fetch data from the database where uploaded = FALSE"""
        query = "SELECT id, url, matched_keywords, html, timestamp FROM db.matched_content WHERE uploaded = FALSE"
        self.db_cursor.execute(query)
        return self.db_cursor.fetchall()

    def mark_as_uploaded(self, record_id):
        """Update the uploaded status to TRUE for a processed record"""
        update_query = sql.SQL(
            "UPDATE db.matched_content SET uploaded = TRUE WHERE id = %s"
        )
        self.db_cursor.execute(update_query, (record_id,))
        self.db_conn.commit()

    # def process_message(self) -> None:

    def process_data(self) -> None:
        """Fetch, process, and send data to OpenCTI"""
        data_rows = self.fetch_unprocessed_data()

        if not data_rows:
            self.helper.connector_logger.info("No new data to process.")
            return

        stix_objects = []
        for row in data_rows:
            record_id, url, matched_keywords, html, timestamp = row

            # Convert to STIX
            # stix_object = self.converter_to_stix.create_obs(url)  # Assuming URL is an observable
            # if stix_object:
            #     stix_objects.append(stix_object)

            # Mark as uploaded
            self.mark_as_uploaded(record_id)

        # if stix_objects:
        #     stix_bundle = self.helper.stix2_create_bundle(stix_objects)
        #     self.helper.send_stix2_bundle(stix_bundle)
        #     self.helper.connector_logger.info(f"Processed {len(stix_objects)} records.")

    def run(self) -> None:
        """
        Run the main process encapsulated in a scheduler
        It allows you to schedule the process to run at a certain intervals
        This specific scheduler from the pycti connector helper will also check the queue size of a connector
        If `CONNECTOR_QUEUE_THRESHOLD` is set, if the connector's queue size exceeds the queue threshold,
        the connector's main process will not run until the queue is ingested and reduced sufficiently,
        allowing it to restart during the next scheduler check. (default is 500MB)
        It requires the `duration_period` connector variable in ISO-8601 standard format
        Example: `CONNECTOR_DURATION_PERIOD=PT5M` => Will run the process every 5 minutes
        :return: None
        """
        self.helper.schedule_iso(
            message_callback=self.process_data,
            duration_period=self.config.duration_period,
        )
