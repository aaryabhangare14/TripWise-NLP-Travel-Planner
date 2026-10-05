import os
import joblib
from chatbot.preprocessing import preprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "intent_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "model", "vectorizer.pkl")


class IntentClassifier:
    def __init__(self, model_path=MODEL_PATH, vectorizer_path=VECTORIZER_PATH):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.model = None
        self.vectorizer = None
        self.load_model()

    def load_model(self):
        """Loads the trained model and vectorizer from disk."""
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            try:
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                return True
            except Exception as e:
                print(f"[Warning] Failed to load intent model: {e}")
                self.model = None
                self.vectorizer = None
        return False

    def predict(self, text: str) -> dict:
        """
        Classifies user query intent using TF-IDF vectorization and Logistic Regression.
        Returns predicted intent, confidence score, and top alternative predictions.
        """
        if not self.model or not self.vectorizer:
            # Attempt reloading
            if not self.load_model():
                # Fallback rule-based heuristic if model is missing
                return self._fallback_rule_intent(text)

        processed = preprocess(text)
        if not processed:
            processed = text.lower()

        features = self.vectorizer.transform([processed])
        probs = self.model.predict_proba(features)[0]
        classes = self.model.classes_

        # Sort classes by descending probability
        sorted_indices = probs.argsort()[::-1]
        best_intent = classes[sorted_indices[0]]
        best_confidence = float(probs[sorted_indices[0]])

        # Top 3 predictions with probabilities
        top_predictions = [
            {"intent": classes[i], "confidence": round(float(probs[i]), 4)}
            for i in sorted_indices[:3]
        ]

        # Get non-zero TF-IDF terms in user input for academic explanation
        feature_names = self.vectorizer.get_feature_names_out()
        cx = features.tocoo()
        top_features = [
            {"term": feature_names[col], "weight": round(float(data), 3)}
            for col, data in zip(cx.col, cx.data)
        ]
        top_features = sorted(top_features, key=lambda x: x["weight"], reverse=True)[:5]

        return {
            "intent": best_intent,
            "confidence": round(best_confidence, 4),
            "top_predictions": top_predictions,
            "top_tfidf_features": top_features,
            "preprocessed_text": processed
        }

    def _fallback_rule_intent(self, text: str) -> dict:
        """Fallback intent detector using keyword heuristics if model is not loaded."""
        lower = text.lower()
        if any(w in lower for w in ["hi", "hello", "hey", "greetings"]):
            intent = "greeting"
        elif any(w in lower for w in ["bye", "goodbye", "exit"]):
            intent = "goodbye"
        elif any(w in lower for w in ["remove", "replace", "add", "change", "increase", "decrease"]):
            intent = "modify_itinerary"
        elif any(w in lower for w in ["plan", "itinerary", "visit", "trip", "tour"]):
            intent = "plan_trip"
        elif any(w in lower for w in ["budget", "cost", "how much", "expense", "price"]):
            intent = "budget_estimate"
        elif any(w in lower for w in ["weather", "temperature", "climate", "rain"]):
            intent = "weather_query"
        elif any(w in lower for w in ["hotel", "stay", "resort", "hostel"]):
            intent = "hotel_recommendation"
        elif any(w in lower for w in ["food", "dish", "eat", "cuisine", "restaurant"]):
            intent = "food_recommendation"
        elif any(w in lower for w in ["places to visit", "attractions", "sightseeing", "what to see"]):
            intent = "recommend_places"
        elif any(w in lower for w in ["where to go", "suggest destination", "where can i"]):
            intent = "find_destination"
        else:
            intent = "plan_trip"

        return {
            "intent": intent,
            "confidence": 0.75,
            "top_predictions": [{"intent": intent, "confidence": 0.75}],
            "top_tfidf_features": [],
            "preprocessed_text": lower
        }
