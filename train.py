import os
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report
from chatbot.preprocessing import preprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "intents.json")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "intent_model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")


def train():
    print("=" * 60)
    print("TripWise NLP Model Training: TF-IDF + Logistic Regression")
    print("=" * 60)

    os.makedirs(MODEL_DIR, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    corpus = []
    labels = []

    for item in data.get("intents", []):
        intent_label = item["intent"]
        for sample in item["examples"]:
            cleaned_sample = preprocess(sample)
            corpus.append(cleaned_sample)
            labels.append(intent_label)

    print(f"Loaded {len(corpus)} training samples across {len(set(labels))} intents.")

    # 1. Feature Extraction: TF-IDF with Unigram + Bigram support
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode"
    )
    X = vectorizer.fit_transform(corpus)
    y = labels

    print(f"Vocabulary Size: {len(vectorizer.vocabulary_)} features")

    # 2. Machine Learning Classifier: Logistic Regression with Balanced Weights
    model = LogisticRegression(
        C=2.5,
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )

    # 3. Cross Validation Evaluation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    print(f"5-Fold Cross-Validation Accuracy: {scores.mean() * 100:.2f}% (+/- {scores.std() * 100:.2f}%)")

    # 4. Fit on entire dataset
    model.fit(X, y)
    y_pred = model.predict(X)
    print("\nTraining Classification Report:")
    print(classification_report(y, y_pred))

    # 5. Persist artifacts
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    print(f"Successfully saved model to: {MODEL_PATH}")
    print(f"Successfully saved vectorizer to: {VECTORIZER_PATH}")
    print("=" * 60)
    return model, vectorizer


if __name__ == "__main__":
    train()
