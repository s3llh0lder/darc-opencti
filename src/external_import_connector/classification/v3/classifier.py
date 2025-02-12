import os
import joblib
import pandas as pd
from threading import Lock
from typing import Dict
from tensorflow.keras.models import load_model
import numpy as np


class DataClassifierV3:
    def __init__(self):
        # self.model_path = MODEL_PATH_V3 # Path to the neural network model
        # self.scaler_path = SCALER_PATH # Path to the scaler for numerical features
        # self.tfidf_path = TFIDF_PATH  # Path to the TF-IDF vectorizer

        self.model_path = "./v3/model.keras"  # Path to the neural network model
        self.scaler_path = (
            "./v3/scaler.pkl"  # Path to the scaler for numerical features
        )
        self.tfidf_path = "./v3/tfidf.pkl"  # Path to the TF-IDF vectorizer
        self.required_columns = ["Content", "Sentiment Score"]
        self._initialize_()

    def _initialize_(self):
        # Load the neural network model
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")
        self.model = load_model(self.model_path)

        # Load the scaler
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler file not found at: {self.scaler_path}")
        self.scaler = joblib.load(self.scaler_path)

        # Load the TF-IDF vectorizer
        if not os.path.exists(self.tfidf_path):
            raise FileNotFoundError(
                f"TF-IDF vectorizer file not found at: {self.tfidf_path}"
            )
        self.tfidf = joblib.load(self.tfidf_path)

    def classify_data(
        self, data: str, processed_data_id: int, additional_features: Dict
    ) -> Dict:
        """Classify the input data using the pre-trained model."""
        # Ensure all required features are present
        for column in self.required_columns:
            if column not in additional_features:
                additional_features[column] = (
                    0  # Default value for missing numerical features
                )

        # Preprocess the textual data
        text_features = self.tfidf.transform([data]).toarray()

        # print(self.scaler.feature_names_in_)

        # Preprocess the numerical data
        numerical_features = pd.DataFrame(
            [
                {
                    "Sentiment Score": additional_features.get("Sentiment Score", 0),
                    "Keyword Count": additional_features.get("Keyword Count", 0),
                    "Obfuscation Level": additional_features.get(
                        "Obfuscation Level", 0
                    ),
                }
            ]
        )
        # Scale the numerical features
        numerical_features = self.scaler.transform(numerical_features)

        # numerical_features = self.scaler.transform(pd.DataFrame({'Sentiment Score': [0.85]}))

        # Combine text and numerical features
        input_data = np.hstack((text_features, numerical_features))

        # Predict using the neural network model
        try:
            prediction_proba = self.model.predict(input_data)[0]
            prediction = np.argmax(prediction_proba)
        except Exception as e:
            raise ValueError(f"Error during prediction: {e}")

        # Map prediction to label
        label = "Exploit" if prediction == 1 else "Non-Exploit"

        result = {"category": label, "confidence": float(max(prediction_proba))}

        # Save classification result to the database
        # db_instance = SaveDBSingleton.get_instance()
        # db_instance.save_classificationv3(processed_data_id, result)

        return result


class DataClassifierSingletonV3:
    """
    Singleton wrapper for the DataClassifierV2 instance.
    """

    _instance: DataClassifierV3 = None
    _lock: Lock = Lock()

    @classmethod
    def get_instance(cls) -> DataClassifierV3:
        """
        Get the single instance of DataClassifierV2.

        Returns:
            DataClassifierV2: The single instance of DataClassifierV2.
        """
        if cls._instance is None:
            with cls._lock:  # Ensure thread safety
                if cls._instance is None:  # Double-checked locking
                    cls._instance = DataClassifierV3()
        return cls._instance
