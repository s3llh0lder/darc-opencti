import pandas as pd
import numpy as np
import re
import time  # Added for timing

from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from nltk.corpus import wordnet
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.over_sampling import RandomOverSampler
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical

# Start timing
start_time = time.time()

# Load dataset
data = pd.read_csv("../dataset/synthetic_cyber_threat_data_test.csv")


# Preprocess text (clean HTML and JavaScript)
def clean_html_and_js(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"[^\x20-\x7E]+", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


# Cleaning HTML and JS
stage_start = time.time()
print("Cleaning HTML and JS ....")
data["Content"] = data["Content"].apply(clean_html_and_js)
print("Cleaning HTML and JS .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Augment text with synonym replacement
stage_start = time.time()
print("Augment text with synonym replacement ....")


def augment_text(text):
    words = text.split()
    for i, word in enumerate(words):
        synonyms = wordnet.synsets(word)
        if synonyms:
            words[i] = synonyms[0].lemmas()[0].name()
    return " ".join(words)


data["Augmented Content"] = data["Content"].apply(augment_text)
print("Augment text with synonym replacement ....DONE ")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Add sentiment analysis
stage_start = time.time()
print("Add sentiment analysis ....")


def calculate_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)["compound"]


data["Sentiment Score"] = data["Content"].apply(calculate_sentiment)
print("Add sentiment analysis ....DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Add keyword count
stage_start = time.time()
print("Add keyword count ....")


def count_keywords(text, keywords):
    return sum(1 for kw in keywords if kw in text)


keywords = ["0-Day", "Zero-Day", "exploit", "CVE"]
data["Keyword Count"] = data["Content"].apply(lambda x: count_keywords(x, keywords))
print("Add keyword count .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Add obfuscation level
stage_start = time.time()
print("Add obfuscation level .... ")


def calculate_obfuscation(text):
    return len(re.findall(r"[!@#$%^&*()_+]", text))


data["Obfuscation Level"] = data["Content"].apply(calculate_obfuscation)
print("Add obfuscation level .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Balance dataset with oversampling
stage_start = time.time()
print("Balance dataset with oversampling .... ")
X = data[["Sentiment Score", "Keyword Count", "Obfuscation Level"]]
y = pd.factorize(data["Label"])[0]
ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X, y)
print("Balance dataset with oversampling .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Train-test split
stage_start = time.time()
print("Train-test split .... ")
X_train, X_test, y_train, y_test = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42
)
print("Train-test split ....DONE ")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Preprocess text for TF-IDF
stage_start = time.time()
print("Preprocess text for TF-IDF .... ")
tfidf = TfidfVectorizer(max_features=5000)
X_text = tfidf.fit_transform(data["Content"]).toarray()
joblib.dump(tfidf, "tfidf.pkl")
print("Preprocess text for TF-IDF ....DONE ")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Scale numerical features
stage_start = time.time()
print("Scale numerical features .... ")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, "scaler.pkl")
print("Scale numerical features .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Combine features
stage_start = time.time()
print("Combine features .... ")
X_combined = np.hstack((X_text, X_scaled))
y_categorical = to_categorical(y)
print("Combine features .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Build neural network
stage_start = time.time()
print("Build neural network .... ")
actual_input_size = X_combined.shape[1]
model = Sequential(
    [
        Input(shape=(actual_input_size,)),
        Dense(128, activation="relu"),
        Dropout(0.3),
        Dense(64, activation="relu"),
        Dropout(0.3),
        Dense(2, activation="softmax"),
    ]
)
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
model.fit(
    X_combined, y_categorical, validation_split=0.2, epochs=20, batch_size=32, verbose=2
)
model.save("model.keras")
print("Build neural network .... DONE")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Save augmented dataset
stage_start = time.time()
print("Save augmented dataset .... ")
data.to_csv("augmented_dataset.csv", index=False)
print("Dataset augmented and saved. Model training complete.")
print(f"Time taken: {time.time() - stage_start:.2f} seconds")

# Total time
print(f"Total script execution time: {time.time() - start_time:.2f} seconds")
