import psycopg2  # or the appropriate database driver you're using
import json
from threading import Lock
from datetime import datetime
from .config_variables import ConfigConnector


class DatabaseHandler:
    def __init__(self):
        self.config = ConfigConnector()

        self.db_config = {
            "dbname": self.config.db_name,
            "user": self.config.db_user,
            "password": self.config.db_password,
            "host": self.config.db_host,
            "port": self.config.db_port,
        }
        # Database connection
        self.db_conn = psycopg2.connect(**self.db_config)
        self._initialize_database()

    def _initialize_database(self):
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                self._create_table_matched_content(cursor)
                self._create_table_selenium_output(cursor)
                self._create_classification_tables(cursor)
                self._add_matched_content_columns(cursor)
                conn.commit()

    def _create_table_matched_content(self, cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS db.matched_content (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                matched_keywords TEXT,
                html TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                processed BOOLEAN NOT NULL DEFAULT FALSE,
                sent_to_deepseek BOOLEAN NOT NULL DEFAULT FALSE,
                sent_to_opencti BOOLEAN NOT NULL DEFAULT FALSE,
                stix_data JSONB
            )"""
        )

    def _create_table_selenium_output(self, cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS db.selenium_output (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                html TEXT NOT NULL,
                screenshot BYTEA,
                timestamp TIMESTAMP NOT NULL
            )"""
        )

    def _create_classification_tables(self, cursor):
        for table in ["classification_results", "classification_results_v3"]:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS db.{table} (
                    id SERIAL PRIMARY KEY,
                    processed_data_id INT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL,
                    classification TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (processed_data_id) REFERENCES db.matched_content(id)
                )"""
            )

    def _add_matched_content_columns(self, cursor):
        cursor.execute(
            """
            ALTER TABLE db.matched_content 
            ADD COLUMN IF NOT EXISTS sent_to_deepseek BOOLEAN NOT NULL DEFAULT FALSE
        """
        )
        cursor.execute(
            """
            ALTER TABLE db.matched_content 
            ADD COLUMN IF NOT EXISTS sent_to_opencti BOOLEAN NOT NULL DEFAULT FALSE
        """
        )
        cursor.execute(
            """
            ALTER TABLE db.matched_content 
            ADD COLUMN IF NOT EXISTS stix_data JSONB
        """
        )

    def save_classification(self, processed_data_id: int, classification: dict):
        self._save_classification_result(
            "classification_results", processed_data_id, classification
        )

    def save_classificationv3(self, processed_data_id: int, classification: dict):
        self._save_classification_result(
            "classification_results_v3", processed_data_id, classification
        )

    def _save_classification_result(
        self, table: str, processed_data_id: int, classification: dict
    ):
        with self.db_conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO db.{table} 
                (processed_data_id, category, confidence, classification, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    processed_data_id,
                    classification["category"],
                    float(classification["confidence"]),
                    json.dumps(classification),
                    datetime.now(),
                ),
            )
            self.db_conn.commit()

    def fetch_unprocessed_data(self):
        """Fetch unprocessed records from database"""
        query = """
            SELECT id, url, matched_keywords, html, timestamp, sent_to_deepseek, sent_to_opencti 
            FROM db.matched_content 
            WHERE processed = FALSE
        """
        # Use the existing self.db_conn but create a fresh cursor
        with self.db_conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def mark_sent_to_deepseek(self, record_id: int, stix_data: dict):
        update_query = """
            UPDATE db.matched_content 
            SET sent_to_deepseek = TRUE, stix_data = %s::jsonb 
            WHERE id = %s
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(update_query, (json.dumps(stix_data), record_id))
            self.db_conn.commit()

    def mark_sent_to_opencti(self, record_id: int):
        update_query = """
            UPDATE db.matched_content 
            SET sent_to_opencti = TRUE 
            WHERE id = %s
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(update_query, (record_id,))
            self.db_conn.commit()

    def get_stix_data(self, record_id: int) -> dict:
        query = """
            SELECT stix_data::text 
            FROM db.matched_content 
            WHERE id = %s
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(query, (record_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return json.loads(result[0])
            return None

    def mark_as_processed(self, record_id):
        """Mark record as processed in database"""
        update_query = "UPDATE db.matched_content SET processed = TRUE WHERE id = %s"
        with self.db_conn.cursor() as cursor:
            cursor.execute(update_query, (record_id,))
            self.db_conn.commit()

    def get_classification_results(self, record_id: int, table: str):
        query = f"""
            SELECT category, confidence 
            FROM db.{table} 
            WHERE processed_data_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        with self.db_conn.cursor() as cursor:
            cursor.execute(query, (record_id,))
            result = cursor.fetchone()
            return {"category": result[0], "confidence": result[1]} if result else None


class DBSingleton:
    """
    Singleton wrapper for the SaveDB instance.
    """

    _instance: DatabaseHandler = None
    _lock: Lock = Lock()

    @classmethod
    def get_instance(cls) -> DatabaseHandler:
        """
        Get the single instance of SaveDB.

        Returns:
            SaveDB: The single instance of SaveDB.
        """
        if cls._instance is None:
            with cls._lock:  # Ensure thread safety
                if cls._instance is None:  # Double-checked locking
                    cls._instance = DatabaseHandler()
        return cls._instance
