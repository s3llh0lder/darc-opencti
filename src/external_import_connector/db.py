import psycopg2  # or the appropriate database driver you're using
import json
from threading import Lock
from datetime import datetime
from typing import Dict
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
        """
        Initialize the PostgreSQL database and create the 'matched_content' table if it doesn't exist.
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS db.matched_content (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        matched_keywords TEXT,
                        html TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        processed boolean NOT NULL DEFAULT FALSE
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS db.selenium_output (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        html TEXT NOT NULL,
                        screenshot BYTEA,
                        timestamp TIMESTAMP NOT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS db.classification_results (
                        id SERIAL PRIMARY KEY,
                        processed_data_id INT NOT NULL,
                        category TEXT NOT NULL,
                        confidence REAL,
                        classification TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (processed_data_id) REFERENCES db.matched_content(id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS db.classification_results_v3 (
                        id SERIAL PRIMARY KEY,
                        processed_data_id INT NOT NULL,
                        category TEXT NOT NULL,
                        confidence REAL,
                        classification TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (processed_data_id) REFERENCES db.matched_content(id)
                    )
                    """
                )
                # Optionally create an index for faster URL lookups
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_url ON db.matched_content (url)
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_selenium_url ON db.selenium_output (url)
                    """
                )
                conn.commit()

    def save_classification(self, processed_data_id: int, classification: Dict):
        """Save classification results to the PostgreSQL database."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO db.classification_results (processed_data_id, category, confidence, classification, timestamp)
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
                conn.commit()

    def save_classificationv3(self, processed_data_id: int, classification: Dict):
        """Save classification results to the PostgreSQL database."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO db.classification_results_v3 (processed_data_id, category, confidence, classification, timestamp)
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
                conn.commit()

    def fetch_unprocessed_data(self):
        """Fetch unprocessed records from database"""
        query = """
            SELECT id, url, matched_keywords, html, timestamp 
            FROM db.matched_content 
            WHERE processed = FALSE
        """
        # Use the existing self.db_conn but create a fresh cursor
        with self.db_conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def mark_as_processed(self, record_id):
        """Mark record as processed in database"""
        update_query = "UPDATE db.matched_content SET processed = TRUE WHERE id = %s"
        with self.db_conn.cursor() as cursor:
            cursor.execute(update_query, (record_id,))
            self.db_conn.commit()


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
