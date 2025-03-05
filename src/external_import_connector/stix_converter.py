import os
import tempfile
import subprocess

from .config_variables import ConfigConnector


class StixConverter:
    """Handles STIX conversion via external script"""

    def __init__(self, config: ConfigConnector, logger):
        self.config = config
        self.logger = logger

    def convert(self, report_id: str, record_data: dict, working_dir: str) -> bool:
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".txt"
            ) as temp_file:
                temp_file.write(record_data["html"])
                temp_file_path = temp_file.name

            cmd = [
                "python3",
                "../txt2stix/txt2stix.py",
                "--relationship_mode",
                "ai",
                "--ai_settings_relationships",
                "deepseek:deepseek-chat",
                "--input_file",
                temp_file_path,
                "--name",
                f"Report {record_data['id']}",
                "--tlp_level",
                "clear",
                "--confidence",
                "90",
                "--use_extractions",
                "ai_mitre_attack_enterprise,ai_ipv4_address_only,ai_url,ai_file_name,ai_email_address",
                "--ai_settings_extractions",
                "deepseek:deepseek-chat",
                "--ai_content_check_provider",
                "deepseek:deepseek-chat",
                # "--ai_create_attack_flow",
                "--report_id",
                report_id,
            ]

            self.logger.info(f"Executing txt2stix: {' '.join(cmd)}")
            env = self._prepare_environment()

            subprocess.run(
                cmd,
                cwd=working_dir,
                check=True,
                env=env,
                start_new_session=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"STIX conversion failed: {str(e)}")
            return False
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _prepare_environment(self) -> dict:
        env = os.environ.copy()
        env.update(
            {
                "DEEPSEEK_API_KEY": self.config.deepseek_api_key,
                "INPUT_TOKEN_LIMIT": str(self.config.input_token_limit),
                "TEMPERATURE": str(self.config.temperature),
                "CTIBUTLER_BASE_URL": self.config.ctibutler_base_url,
                "CTIBUTLER_API_KEY": self.config.ctibutler_api_key,
                "VULMATCH_BASE_URL": self.config.vulmatch_base_url,
                "VULMATCH_API_KEY": self.config.vulmatch_api_key,
            }
        )
        return env
