import os
from pathlib import Path

import yaml
from pycti import get_config_variable


class ConfigConnector:
    def __init__(self):
        """
        Initialize the connector with necessary configurations
        """

        # Load configuration file
        self.load = self._load_config()
        self._initialize_configurations()

    @staticmethod
    def _load_config() -> dict:
        """
        Load the configuration from the YAML file
        :return: Configuration dictionary
        """
        config_file_path = Path(__file__).parents[1].joinpath("config.yml")
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )

        return config

    def _initialize_configurations(self) -> None:
        """
        Connector configuration variables
        :return: None
        """
        # OpenCTI configurations
        self.duration_period = get_config_variable(
            "CONNECTOR_DURATION_PERIOD",
            ["connector", "duration_period"],
            self.load,
        )

        # Connector extra parameters
        self.db_name = get_config_variable(
            "CONNECTOR_DARC_DB_NAME",
            ["connector", "db_name"],
            self.load,
        )
        self.db_user = get_config_variable(
            "CONNECTOR_DARC_DB_USER",
            ["connector", "db_user"],
            self.load,
        )
        self.db_password = get_config_variable(
            "CONNECTOR_DARC_DB_PASSWORD",
            ["connector", "db_password"],
            self.load,
        )
        self.db_host = get_config_variable(
            "CONNECTOR_DARC_DB_HOST",
            ["connector", "db_host"],
            self.load,
        )
        self.db_port = get_config_variable(
            "CONNECTOR_DARC_DB_PORT",
            ["connector", "db_port"],
            self.load,
        )
