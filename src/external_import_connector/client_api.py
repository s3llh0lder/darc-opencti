import json
import re
from openai import OpenAI  # Add OpenAI dependency

stix_bundle = """```json
{
  "type": "bundle",
  "id": "bundle--fff9e3c6-f0dd-4038-97ed-902dce183a1c",
  "objects": [
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--3d864934-72af-4343-9473-21768e8b9d27",
      "name": "Chaos Ransomware Builder",
      "description": "A tool for creating ransomware variants.",
      "created": "2025-02-16T12:00:00Z",
      "modified": "2025-02-16T12:00:00Z"
    },
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--b565077a-c009-41b4-a00e-0afc529200b8",
      "name": "Ransomware-Builder-By-Shozab-Haxor",
      "description": "A ransomware creation tool.",
      "created": "2025-02-16T12:00:00Z",
      "modified": "2025-02-16T12:00:00Z"
    },
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--df44546f-b8cd-4c69-8648-c33eca89a4d5",
      "name": "Kraken V2 Android Banking RAT",
      "description": "A remote access trojan targeting Android banking applications.",
      "created": "2025-02-16T12:00:00Z",
      "modified": "2025-02-16T12:00:00Z"
    },
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--aca95996-a5fb-48c9-a4e2-1b04fbfbfec3",
      "name": "Venom Cracked",
      "description": "A cracked version of the Venom remote access trojan.",
      "created": "2025-02-16T12:00:00Z",
      "modified": "2025-02-16T12:00:00Z"
    },
    {
      "type": "tool",
      "spec_version": "2.1",
      "id": "tool--15588abd-9b3c-4ac9-82f0-f209b69fbcef",
      "name": "Whatsapp-Botmaster-Cracked",
      "description": "A cracked tool for automating WhatsApp interactions.",
      "created": "2025-02-16T12:00:00Z",
      "modified": "2025-02-16T12:00:00Z"
    }
  ]
}
```"""

stix_bundle_old = """```json
{
    "type": "bundle",
    "id": "bundle--2a25c3c8-5d88-4ae9-862a-cc3396442317",
    "objects": [
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": "indicator--a932fcc6-e032-476c-826f-cb970a5a1ade",
            "created": "2014-02-20T09:16:08.989Z",
            "modified": "2014-02-20T09:16:08.989Z",
            "name": "File hash for Poison Ivy variant",
            "description": "This file hash indicates that a sample of Poison Ivy is present.",
            "indicator_types": [
                "malicious-activity"
            ],
            "pattern": "[file:hashes.'SHA-256' = 'ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c']",
            "pattern_type": "stix",
            "valid_from": "2014-02-20T09:00:00Z"
        },
        {
            "type": "malware",
            "spec_version": "2.1",
            "id": "malware--fdd60b30-b67c-41e3-b0b9-f01faf20d111",
            "created": "2014-02-20T09:16:08.989Z",
            "modified": "2014-02-20T09:16:08.989Z",
            "name": "Poison Ivy",
            "malware_types": [
                "remote-access-trojan"
            ],
            "is_family": false
        },
        {
            "type": "relationship",
            "spec_version": "2.1",
            "id": "relationship--29dcdf68-1b0c-4e16-94ed-bcc7a9572f69",
            "created": "2020-02-29T18:09:12.808Z",
            "modified": "2020-02-29T18:09:12.808Z",
            "relationship_type": "indicates",
            "source_ref": "indicator--a932fcc6-e032-476c-826f-cb970a5a1ade",
            "target_ref": "malware--fdd60b30-b67c-41e3-b0b9-f01faf20d111"
        }
    ]
}
```"""


class ConnectorClient:
    def __init__(self, helper, config):
        self.helper = helper
        self.config = config

        # Initialize OpenAI client with DeepSeek configuration
        self.ai_client = OpenAI(
            api_key=self.config.deepseek_api_key,
            base_url=self.config.deepseek_api_url,
        )

    def generate_stix_from_text_mock(self, text: str) -> dict:
            return self._validate_stix(stix_bundle)

    def generate_stix_from_text(self, text: str) -> dict:
        """
        Convert security-related text to STIXv2 format using AI
        :param text: Input text containing security indicators
        :return: STIXv2 formatted JSON
        """
        try:
            # Structured prompt for consistent STIX conversion
            system_prompt = """You are a cybersecurity analyst specialized in STIXv2 format. 
            Convert the following text into valid STIXv2 JSON format with these rules:
            1. Identify malware, tools, and attack patterns
            2. Create relationships between entities
            3. Use proper STIXv2 syntax and object types
            4. Include UUIDs for all objects
            5. You MUST return ONLY valid STIX 2.1 JSON wrapped in ```json markers.
            Example:
            ```json
            {
              "type": "bundle",
              "id": "bundle--...",
              "objects": [
                {
                  "type": "malware",
                  "id": "malware--...",
                  "name": "Example Malware"
                }
              ]
            }"""

            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                # response_format={"type": "json_object"},
                temperature=0.1,
                stream=False,
            )

            # Extract and parse the STIX output
            stix_output = response.choices[0].message.content
            return self._validate_stix(stix_output)

        except Exception as err:
            self.helper.connector_logger.error(f"STIX generation failed: {str(err)}")
            return {}

    def _validate_stix(self, stix_data: str) -> dict:
        """
        Validate and clean STIX output
        """
        try:
            if not stix_data:
                self.helper.connector_logger.error("Received empty STIX response")
                return {}

            # Enhanced cleaning pattern
            clean_data = re.sub(
                r"^```json|```$", "", stix_data, flags=re.DOTALL
            ).strip()

            if not clean_data:
                self.helper.connector_logger.error(
                    "Empty content after cleaning",
                    {
                        "original_data": (
                            stix_data[:100] + "..."
                            if len(stix_data) > 100
                            else stix_data
                        )
                    },
                )
                return {}

            # Attempt JSON parsing
            parsed = json.loads(clean_data)

            # Basic STIX structure validation
            if not isinstance(parsed, dict) or parsed.get("type") != "bundle":
                self.helper.connector_logger.error("Invalid STIX bundle structure")
                return {}

            return parsed

        except json.JSONDecodeError as e:
            self.helper.connector_logger.error(
                "JSON decoding failed",
                {
                    "error": str(e),
                    "clean_data_sample": (
                        clean_data[:200] + "..."
                        if len(clean_data) > 200
                        else clean_data
                    ),
                },
            )
            return {}
        except Exception as e:
            self.helper.connector_logger.error(f"Unexpected validation error: {str(e)}")
            return {}
