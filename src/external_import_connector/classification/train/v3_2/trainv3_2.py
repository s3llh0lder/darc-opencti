import pandas as pd
import numpy as np
import re
import time

from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.over_sampling import RandomOverSampler
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical

# Load dataset
file_path = "../dataset/data.csv"
data = pd.read_csv(file_path, delimiter="@")

# Timing
start_time = time.time()


# HTML Cleaning
def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"[^\x20-\x7E]+", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


print("Cleaning HTML...")
data["cleaned_html"] = data["html"].apply(clean_html)
print(f"HTML cleaning done: {time.time() - start_time:.2f}s\n")

# Feature Engineering
print("Creating features...")
feature_start = time.time()

# Sentiment Analysis
analyzer = SentimentIntensityAnalyzer()
data["sentiment"] = data["cleaned_html"].apply(
    lambda x: analyzer.polarity_scores(x)["compound"]
)

# Keyword Count
keywords = ["0-Day", "Zero-Day", "exploit", "CVE"]
data["keyword_count"] = data["cleaned_html"].apply(
    lambda x: sum(x.lower().count(kw.lower()) for kw in keywords)
)

# Obfuscation Level
data["obfuscation"] = data["cleaned_html"].apply(
    lambda x: len(re.findall(r"[!@#$%^&*()_+]", x))
)

print(f"Features created: {time.time() - feature_start:.2f}s\n")

# Split data FIRST to prevent leakage
print("Splitting data...")
X = data[["cleaned_html", "sentiment", "keyword_count", "obfuscation"]]
y = pd.factorize(data["c1_cat"])[0]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Data split complete: {time.time() - start_time:.2f}s\n")

# Oversample ONLY training data
print("Balancing data...")
sampler = RandomOverSampler(random_state=42)
X_train, y_train = sampler.fit_resample(X_train, y_train)
print(f"Data balanced: {time.time() - start_time:.2f}s\n")

# Text Processing Pipeline
print("Processing text...")
text_start = time.time()

# TF-IDF on resampled training data
tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_text_train = tfidf.fit_transform(X_train["cleaned_html"])
X_text_test = tfidf.transform(X_test["cleaned_html"])
joblib.dump(tfidf, "tfidf.pkl")

# Scale Numerical Features
scaler = StandardScaler()
num_features = ["sentiment", "keyword_count", "obfuscation"]
X_num_train = scaler.fit_transform(X_train[num_features])
X_num_test = scaler.transform(X_test[num_features])
joblib.dump(scaler, "scaler.pkl")

# Combine Features
X_train_final = np.hstack((X_text_train.toarray(), X_num_train))
X_test_final = np.hstack((X_text_test.toarray(), X_num_test))
y_train_cat = to_categorical(y_train)
y_test_cat = to_categorical(y_test)

print(f"Text processing done: {time.time() - text_start:.2f}s\n")

# Neural Network
print("Building model...")
model = Sequential(
    [
        Input(shape=(X_train_final.shape[1],)),
        Dense(128, activation="relu", kernel_initializer="he_normal"),
        Dropout(0.5),
        Dense(64, activation="relu", kernel_initializer="he_normal"),
        Dropout(0.3),
        Dense(2, activation="softmax"),
    ]
)

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy", "Precision", "Recall"],
)

print("Training model...")
history = model.fit(
    X_train_final,
    y_train_cat,
    validation_data=(X_test_final, y_test_cat),
    epochs=30,
    batch_size=64,
    verbose=1,
)

model.save("model.keras")
print(f"Model trained: {time.time() - start_time:.2f}s\n")

# Save processed data
pd.concat(
    [pd.DataFrame(X_train_final), pd.Series(y_train, name="target")], axis=1
).to_csv("processed_dataset.csv", index=False)

print(f"Total execution time: {time.time() - start_time:.2f} seconds")
