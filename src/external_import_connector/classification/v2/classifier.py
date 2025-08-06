import os
from typing import Dict
from threading import Lock
import joblib
import pandas as pd


class DataClassifierV2:
    def __init__(self):
        # self.model_path = MODEL_PATH # prod
        self.model_path = (
            "./external_import_connector/classification/v2/model.pkl"  # main.py
        )
        # self.model_path = "./v2/model.pkl" #test.py
        self.required_columns = [
            "Content",
            "Language",
            "Threat Level",
            "Action Required",
        ]
        self._initialize_()

    def _initialize_(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")
        self.model = joblib.load(self.model_path)

    def classify_data(
        self, data: str, processed_data_id: int, additional_features: Dict
    ) -> Dict:
        """Classify the input data using the pre-trained model."""
        # Ensure all required features are present
        for column in self.required_columns:
            if column not in additional_features:
                additional_features[column] = (
                    "Unknown"  # Default value for missing features
                )

        # Combine text content with additional features
        input_data = pd.DataFrame([{**additional_features, "Content": data}])

        # Predict using the model
        try:
            prediction = self.model.predict(input_data)[0]
            prediction_proba = self.model.predict_proba(input_data)[0]
        except Exception as e:
            raise ValueError(f"Error during prediction: {e}")

        # Map prediction to label
        label = "Exploit" if prediction == 1 else "Non-Exploit"

        result = {"category": label, "confidence": max(prediction_proba)}

        return result


class DataClassifierSingleton:
    """
    Singleton wrapper for the SaveDB instance.
    """

    _instance: DataClassifierV2 = None
    _lock: Lock = Lock()

    @classmethod
    def get_instance(cls) -> DataClassifierV2:
        """
        Get the single instance of SaveDB.

        Returns:
            SaveDB: The single instance of SaveDB.
        """
        if cls._instance is None:
            with cls._lock:  # Ensure thread safety
                if cls._instance is None:  # Double-checked locking
                    cls._instance = DataClassifierV2()
        return cls._instance
