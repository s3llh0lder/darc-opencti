import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load the dataset
file_path = os.path.join("../dataset/synthetic_cyber_threat_data.csv")
dataset = pd.read_csv(file_path)

# Preprocess dataset
dataset["Label"] = (dataset["Label"] == "Exploit").astype(int)
categorical_features = ["Threat Level", "Language", "Action Required"]

# Define features and target
X = dataset[["Content", "Threat Level", "Language", "Action Required"]]
y = dataset["Label"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# Define a pipeline
pipeline = Pipeline(
    [
        (
            "preprocessor",
            ColumnTransformer(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(max_features=500, stop_words="english"),
                        "Content",
                    ),
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore"),
                        categorical_features,
                    ),
                ]
            ),
        ),
        ("classifier", RandomForestClassifier(random_state=42)),
    ]
)

# Train the model
pipeline.fit(X_train, y_train)

# Evaluate the model
y_pred = pipeline.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the trained model
model_save_path = "model_v1.pkl"
joblib.dump(pipeline, model_save_path)
print(f"Model trained and saved to {model_save_path}")
