import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
from sklearn.preprocessing import OneHotEncoder

# Load the dataset
file_path = "dataset/synthetic_cyber_threat_data.csv"
dataset = pd.read_csv(file_path)

# Preprocess dataset
# Encode target labels
dataset["Label"] = (dataset["Label"] == "Exploit").astype(int)

# Encode categorical features
categorical_features = ["Threat Level", "Language", "Action Required"]
encoded_features = {}
for feature in categorical_features:
    dataset[f"{feature} Encoded"] = dataset[feature].astype("category").cat.codes
    encoded_features[feature] = dataset[f"{feature} Encoded"]

# Define features and target
X = dataset[
    ["Content", "Threat Level Encoded", "Language Encoded", "Action Required Encoded"]
]
y = dataset["Label"]

# Split data into train and test sets
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

# Save the trained model
model_save_path = "test_classifier.pkl"
joblib.dump(pipeline, model_save_path)

print(f"Model trained and saved to {model_save_path}")

# Test the model
# Load the trained model
model = joblib.load(model_save_path)

# Predict on the test set
y_pred = model.predict(X_test)

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Test Accuracy: {accuracy:.2f}")

# Detailed metrics
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Confusion matrix
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
