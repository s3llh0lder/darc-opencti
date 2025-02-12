import os
import joblib
import pandas as pd
import numpy as np
from threading import Lock
from typing import Dict
from tensorflow.keras.models import load_model


class DataClassifierV32:
    def __init__(self):
        # prod
        # self.model_path = MODEL_PATH_V3
        # self.scaler_path = SCALER_PATH
        # self.tfidf_path = TFIDF_PATH

        # main.py
        self.model_path = "./external_import_connector/classification/v3_2/model.keras"  # Path to the neural network model
        self.scaler_path = "./external_import_connector/classification/v3_2/scaler.pkl"  # Path to the scaler for numerical features
        self.tfidf_path = "./external_import_connector/classification/v3_2/tfidf.pkl"  # Path to the TF-IDF vectorizer

        # test.py
        # self.model_path = "./v3_2/model.keras"  # Path to the neural network model
        # self.scaler_path = "./v3_2/scaler.pkl"  # Path to the scaler for numerical features
        # self.tfidf_path = "./v3_2/tfidf.pkl"  # Path to the TF-IDF vectorizer

        self.required_features = ["sentiment", "keyword_count", "obfuscation"]
        self._initialize_()
        # self.lock = Lock()  # Thread safety for predictions

    def _initialize_(self):
        """Load all required ML artifacts"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Keras model not found at {self.model_path}")
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler not found at {self.scaler_path}")
        if not os.path.exists(self.tfidf_path):
            raise FileNotFoundError(f"TF-IDF vectorizer not found at {self.tfidf_path}")

        # with self.lock:
        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        self.tfidf = joblib.load(self.tfidf_path)

    def classify_data(
        self, raw_content: str, processed_data_id: int, features: Dict
    ) -> Dict:
        """Classify web content using the trained security model.

        Args:
            raw_content: Cleaned HTML content
            processed_data_id: Database ID for tracking
            features: Dictionary containing {
                'sentiment': float,
                'keyword_count': int,
                'obfuscation': int
            }

        Returns:
            Dictionary with classification results
        """
        # Validate input features
        for feat in self.required_features:
            if feat not in features:
                raise ValueError(f"Missing required feature: {feat}")

        # Process text features
        # with self.lock:
        text_vector = self.tfidf.transform([raw_content]).toarray()

        # Process numerical features
        numerical_features = pd.DataFrame(
            [
                [
                    features["sentiment"],
                    features["keyword_count"],
                    features["obfuscation"],
                ]
            ],
            columns=self.required_features,
        )

        scaled_numerical = self.scaler.transform(numerical_features)

        # Combine features
        combined_input = np.hstack((text_vector, scaled_numerical))

        # Make prediction
        # with self.lock:
        #     try:
        probabilities = self.model.predict(combined_input, verbose=0)[0]
        prediction = int(np.argmax(probabilities))
        confidence = float(np.max(probabilities))
        # except Exception as e:
        #     raise RuntimeError(f"Classification failed: {str(e)}")

        # Format results
        result = {
            "category": "Exploit" if prediction == 1 else "Non-Exploit",
            "confidence": confidence,
            "probabilities": {
                "Non-Exploit": float(probabilities[0]),
                "Exploit": float(probabilities[1]),
            },
        }

        # Save to database
        # db = SaveDBSingleton.get_instance()
        # db.save_classificationv3(processed_data_id, result)

        return result


class DataClassifierSingletonV32:
    """
    Singleton wrapper for the DataClassifierV2 instance.
    """

    _instance: DataClassifierV32 = None
    _lock: Lock = Lock()

    @classmethod
    def get_instance(cls) -> DataClassifierV32:
        """
        Get the single instance of DataClassifierV2.

        Returns:
            DataClassifierV2: The single instance of DataClassifierV2.
        """
        if cls._instance is None:
            with cls._lock:  # Ensure thread safety
                if cls._instance is None:  # Double-checked locking
                    cls._instance = DataClassifierV32()
        return cls._instance
