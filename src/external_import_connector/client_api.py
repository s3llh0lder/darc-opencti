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
      "id": "malware--3d864934-72af-4343-9473-21768e8b9d27",
      "name": "Chaos Ransomware Builder",
      "description": "A tool for creating ransomware variants."
    },
    {
      "type": "malware",
      "id": "malware--b565077a-c009-41b4-a00e-0afc529200b8",
      "name": "Ransomware-Builder-By-Shozab-Haxor",
      "description": "A ransomware creation tool."
    },
    {
      "type": "malware",
      "id": "malware--df44546f-b8cd-4c69-8648-c33eca89a4d5",
      "name": "Kraken V2 Android Banking RAT",
      "description": "A remote access trojan targeting Android banking applications."
    },
    {
      "type": "malware",
      "id": "malware--aca95996-a5fb-48c9-a4e2-1b04fbfbfec3",
      "name": "Venom Cracked",
      "description": "A cracked version of the Venom remote access trojan."
    },
    {
      "type": "tool",
      "id": "tool--15588abd-9b3c-4ac9-82f0-f209b69fbcef",
      "name": "Whatsapp-Botmaster-Cracked",
      "description": "A cracked tool for automating WhatsApp interactions."
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
