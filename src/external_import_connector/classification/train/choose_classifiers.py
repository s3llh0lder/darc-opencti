from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import classification_report
import pandas as pd

# Load dataset
data = pd.read_csv("dataset/synthetic_cyber_threat_data.csv")

# Preprocess text data
tfidf = TfidfVectorizer(max_features=5000)
X_text = tfidf.fit_transform(data["Content"])

# Combine text features with other features
X_other = data[["Sentiment Score"]].values  # Example numerical feature
from scipy.sparse import hstack

X = hstack((X_text, X_other))

# Labels
y = data["Label"]

# Split data
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Remove negative features (e.g., Sentiment Score) for MultinomialNB
X_tfidf = tfidf.fit_transform(data["Content"])  # Use only text features

# Split dataset correctly
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, data["Label"], test_size=0.2, random_state=42
)

classifiers = {
    "Logistic Regression": LogisticRegression(),
    "Naive Bayes": MultinomialNB(),  # Use MultinomialNB with sparse matrix
    "Random Forest": RandomForestClassifier(),
    "SVM": SVC(probability=True),
}

for name, clf in classifiers.items():
    if name == "Naive Bayes":  # MultinomialNB
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
    else:  # Other classifiers
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

    print(f"Classifier: {name}")
    print(classification_report(y_test, y_pred))
    print("-" * 50)
