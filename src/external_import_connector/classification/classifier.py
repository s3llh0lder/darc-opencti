from .v2.classifier import DataClassifierSingleton
from .v3_2.classifier import DataClassifierSingletonV32
from ..db import DBSingleton


class DataClassifier:

    def __init__(self):
        self.classifier = DataClassifierSingleton.get_instance()
        self.classifier_v32 = DataClassifierSingletonV32.get_instance()
        self.db_handler = DBSingleton().get_instance()

    def classify_data(self, text: str, entity_id: int) -> None:

        additional_features = {
            "Sentiment Score": 1,  # Example encoded value for "Critical"
            "Keyword Count": 1,  # Example encoded value for "English"
            "Obfuscation Level": 1,  # Example encoded value for "Monitoring"
        }

        result = self.classifier.classify_data(text, entity_id, additional_features)
        self.db_handler.save_classification(entity_id, result)

        additional_features32 = {
            "sentiment": -0.32,
            "keyword_count": 3,
            "obfuscation": 12,
        }

        result = self.classifier_v32.classify_data(
            text, entity_id, additional_features32
        )
        self.db_handler.save_classificationv3(entity_id, result)
