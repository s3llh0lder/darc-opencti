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
        self.url = get_config_variable(
            "OPENCTI_URL",
            ["opencti", "url"],
            self.load,
        )
        self.token = get_config_variable(
            "OPENCTI_TOKEN",
            ["opencti", "token"],
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

        self.deepseek_api_key = get_config_variable(
            "CONNECTOR_DEEP_SEEK_API_KEY",
            ["connector", "deepseek_api_key"],
            self.load,
        )

        self.input_token_limit = get_config_variable(
            "INPUT_TOKEN_LIMIT",
            ["connector", "input_token_limit"],
            self.load,
        )
        self.temperature = get_config_variable(
            "TEMPERATURE",
            ["connector", "temperature"],
            self.load,
        )
        self.ctibutler_base_url = get_config_variable(
            "CTIBUTLER_BASE_URL",
            ["connector", "ctibutler_base_url"],
            self.load,
        )
        self.ctibutler_api_key = get_config_variable(
            "CTIBUTLER_API_KEY",
            ["connector", "ctibutler_api_key"],
            self.load,
        )
        self.vulmatch_base_url = get_config_variable(
            "VULMATCH_BASE_URL",
            ["connector", "vulmatch_base_url"],
            self.load,
        )
        self.vulmatch_api_key = get_config_variable(
            "VULMATCH_API_KEY",
            ["connector", "vulmatch_api_key"],
            self.load,
        )
