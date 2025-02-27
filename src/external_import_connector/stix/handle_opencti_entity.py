from typing import Dict, Optional


class OpenCTIEntityHandler:
    """Handles OpenCTI entity search and verification operations"""

    def __init__(self, helper, config):
        """
        Initialize with OpenCTI helper and config

        :param helper: OpenCTIConnectorHelper instance
        :param config: Connector configuration
        """
        self.helper = helper
        self.config = config
        self.logger = helper.connector_logger

    def search_entity_by_name_type(
        self, entity_type: str, name: str, stix_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search for existing entities by name and type in OpenCTI

        :param entity_type: STIX type (e.g., 'Malware', 'Indicator')
        :param name: Entity name to search for
        :param stix_id: Optional STIX ID for exact match
        :return: First matching entity or None
        """
        try:
            filters = []
            if stix_id:
                filters.append({"key": "id", "values": [stix_id]})
            else:
                filters.append(
                    {
                        "key": "name",
                        "values": [name],
                        "operator": "eq",
                        "mode": "insensitive",
                    }
                )
                filters.append({"key": "entity_type", "values": [entity_type]})

            result = self.helper.api.stix_domain_object.list(
                filters=filters,
                first=1,
                customAttributes="""
                    id
                    name
                    entity_type
                    created
                    modified
                """,
            )

            return result[0] if result else None

        except Exception as e:
            self.logger.error(
                f"Entity search failed for {entity_type}/{name}: {str(e)}"
            )
            return None

    def entity_exists(self, record_data: Dict) -> bool:
        """
        Check if similar entity already exists in OpenCTI
        """
        if not record_data.get("stix_id"):
            return False

        existing = self.search_entity_by_name_type(
            entity_type=record_data["malware"], name=record_data[""]
        )

        return existing is not None
