import json
import re
import uuid
from openai import OpenAI  # Add OpenAI dependency

stix_bundle = """{"objects":[{"type":"malware","id":"malware--a1b2c3d4-5e6f-4123-8c9d-0e1f2a3b4c5d","name":"Whatsapp-Botmaster-Cracked","description":"Cracked version of Whatsapp-Botmaster"},{"type":"malware","id":"malware--b2c3d4e5-6f7a-4234-9d8e-1f2a3b4c5d6e","name":"Chaos-Ransomware-Builder-v4","description":"Builder for Chaos Ransomware"},{"type":"malware","id":"malware--c3d4e5f6-7a8b-4345-9e8f-2a3b4c5d6e7f","name":"Ransomware-Builder-By-Shozab-Haxor","description":"Ransomware builder by Shozab Haxor"},{"type":"malware","id":"malware--d4e5f6a7-8b9c-4456-9f8a-3b4c5d6e7f8g","name":"ViralTool","description":"Tool for creating viral content"},{"type":"malware","id":"malware--e5f6a7b8-9c0d-4567-8a9b-4c5d6e7f8g9h","name":"Rats-Crew-AIO","description":"All-in-one tool by Rats Crew"},{"type":"vulnerability","id":"vulnerability--f6a7b8c9-0d1e-4678-9a8b-5d6e7f8g9h0i","name":"CVE-2024-34102","description":"Pre-authentication XML entity injection issue in Magento / Adobe Commerce"},{"type":"malware","id":"malware--a7b8c9d0-1e2f-4789-8b9c-6d7e8f9g0h1i","name":"Venom_Cracked_2.7.0.0","description":"Cracked version of Venom"},{"type":"malware","id":"malware--b8c9d0e1-2f3a-4890-9c8d-7e8f9g0h1i2j","name":"Kraken V2 Android Banking RAT","description":"Remote Access Tool for Android banking"},{"type":"malware","id":"malware--c9d0e1f2-3a4b-4901-8d9e-8f9g0h1i2j3k","name":"Ransomware tool pack","description":"Collection of ransomware tools"},{"type":"malware","id":"malware--d0e1f2a3-4b5c-4012-9e8f-9g0h1i2j3k4l","name":"Ransomware_Decrypter","description":"Tool for decrypting ransomware"},{"type":"malware","id":"malware--e1f2a3b4-5c6d-4123-8f9g-0h1i2j3k4l5m","name":"AIO-Leecher-By-Billie-Eilish","description":"All-in-one leecher tool"},{"type":"malware","id":"malware--f2a3b4c5-6d7e-4234-9g0h-1i2j3k4l5m6n","name":"Dork-Searcher-CR7","description":"Dork searching tool"},{"type":"malware","id":"malware--a3b4c5d6-7e8f-4345-0h1i-2j3k4l5m6n7o","name":"SLayer-Leecher-v0-7","description":"Leecher tool version 0.7"},{"type":"malware","id":"malware--b4c5d6e7-8f9a-4456-1i2j-3k4l5m6n7o8p","name":"Discord-Nitro-Checker-Generator-By-Wulu","description":"Discord Nitro checker and generator"},{"type":"malware","id":"malware--c5d6e7f8-9a0b-4567-2j3k-4l5m6n7o8p9q","name":"Hazard-Nuker-Tool-v1-3-3-By-Rdimo","description":"Nuker tool version 1.3.3"},{"type":"malware","id":"malware--d6e7f8a9-0b1c-4678-3k4l-5m6n7o8p9q0r","name":"Blazing-Dork-v1.5-cracked-version","description":"Cracked version of Blazing Dork v1.5"},{"type":"malware","id":"malware--e7f8a9b0-1c2d-4789-4l5m-6n7o8p9q0r1s","name":"DreamTime - Create fake nudes","description":"Tool for creating fake nudes"},{"type":"malware","id":"malware--f8a9b0c1-2d3e-4890-5m6n-7o8p9q0r1s2t","name":"SilverBullet.v1.1.4","description":"SilverBullet tool version 1.1.4"}]}"""


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
            Convert the following text into valid STIXv2 JSON format with these STRICT rules:
            1. For ALL object IDs:
               - MUST use UUIDv4 with lowercase hex characters ONLY (a-f, 0-9)
               - MUST follow 8-4-4-4-12 hyphen format
               - MUST NOT contain invalid characters (g-z, G-Z)
               - MUST have version/variant bits: 13th character=4, 17th character=8/9/a/b
            2. Relationships must reference valid existing IDs
            3. All objects MUST be in an array under "objects" key
            4. Never use placeholder characters like g, h, i, etc. in UUIDs

            
            Example of VALID UUID:
             ```json
            {
              "type": "bundle",
              "id": "bundle--...",
              "objects": [
                {
                  "type": "malware",
                  "id": "attack-pattern--a1b2c3d4-5e6f-4123-8c9d-0e1f2a3b4c5d"
                  "spec_version": "2.1",
                  "name": "Example Malware"
                  "created": "2020-02-29T18:09:12.808Z",
                  "modified": "2020-02-29T18:09:12.808Z",
                }
              ]
            }

            Example of INVALID UUID:
            ```json
            {
              "type": "attack-pattern",
              "id": "attack-pattern--g1b2c3d4-5e6f-4123-8c9d-0e1f2a3b4c5d"  # 'g' is invalid
              "spec_version": "2.1",
              "name": "Example Malware"
              "created": "2020-02-29T18:09:12.808Z",
              "modified": "2020-02-29T18:09:12.808Z",
            }```"""

            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                stream=False,
            )

            # Extract and parse the STIX output
            stix_output = response.choices[0].message.content
            self.helper.connector_logger.info(
                f"Successfully received STIX object {stix_output}"
            )
            return self._validate_stix(stix_output)

        except Exception as err:
            self.helper.connector_logger.error(f"STIX generation failed: {str(err)}")
            return {}

    def _validate_stix(self, stix_data: str) -> dict:
        """
        Validate and clean STIX output with strict UUIDv4 enforcement and structural fixes
        """
        try:
            if not stix_data:
                self.helper.connector_logger.error("Received empty STIX response")
                return {}

            # Clean JSON wrapper markers
            clean_data = re.sub(
                r"^```json|```$", "", stix_data, flags=re.DOTALL | re.IGNORECASE
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

            # Parse JSON structure
            parsed = json.loads(clean_data)

            # Add missing bundle fields if needed
            if "type" not in parsed:
                parsed["type"] = "bundle"
                self.helper.connector_logger.info("Added missing bundle type")

            if "id" not in parsed:
                parsed["id"] = f"bundle--{uuid.uuid4()}"
                self.helper.connector_logger.info("Generated missing bundle ID")

            # Validate UUIDs and structure for all objects
            valid_objects = []
            for obj in parsed.get("objects", []):
                if not isinstance(obj, dict):
                    self.helper.connector_logger.warning(
                        "Skipping non-dictionary object"
                    )
                    continue

                try:
                    # Validate object ID existence and format
                    obj_id = obj.get("id", "")
                    if not obj_id:
                        raise ValueError("Missing 'id' field")

                    # Split into prefix and UUID
                    parts = obj_id.split("--", 1)
                    if len(parts) != 2:
                        raise ValueError(f"Invalid STIX ID format: {obj_id}")
                    prefix, uuid_str = parts

                    # Strict UUID validation
                    uuid_str = uuid_str.lower()
                    if any(c not in "0123456789abcdef-" for c in uuid_str):
                        raise ValueError(f"Invalid hex characters in UUID: {uuid_str}")

                    # Parse and validate UUIDv4 structure
                    uuid_obj = uuid.UUID(uuid_str)
                    if uuid_obj.version != 4:
                        raise ValueError(f"UUID version {uuid_obj.version} != 4")

                    # Ensure proper hyphenation format
                    canonical_uuid = str(uuid_obj)
                    if uuid_str != canonical_uuid:
                        obj["id"] = f"{prefix}--{canonical_uuid}"
                        self.helper.connector_logger.info(
                            f"Reformatted UUID: {obj_id} -> {obj['id']}"
                        )

                except (ValueError, AttributeError, IndexError) as e:
                    # Generate new UUIDv4 and preserve relationships
                    original_id = obj.get("id", "missing-id")
                    new_uuid = uuid.uuid4()
                    prefix = (
                        obj.get("type", "unknown")
                        .lower()
                        .replace("_", "-")
                        .replace(" ", "-")
                    )
                    obj["id"] = f"{prefix}--{new_uuid}"
                    self.helper.connector_logger.warning(
                        f"Replaced invalid UUID {original_id} with {obj['id']} - Reason: {str(e)}"
                    )

                valid_objects.append(obj)

            # Update objects list with validated entries
            parsed["objects"] = valid_objects

            # Validate bundle structure
            if parsed.get("type") != "bundle":
                self.helper.connector_logger.error("Missing or invalid bundle type")
                return {}

            if not isinstance(parsed.get("objects"), list):
                self.helper.connector_logger.error("'objects' must be an array")
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
            self.helper.connector_logger.error(f"STIX validation failed: {str(e)}")
            return {}
