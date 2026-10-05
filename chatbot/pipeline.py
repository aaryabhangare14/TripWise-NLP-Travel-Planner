from typing import Dict, Any
from chatbot.preprocessing import preprocess_with_trace
from chatbot.intent_classifier import IntentClassifier
from chatbot.entity_extractor import EntityExtractor
from chatbot.recommendation import RecommendationEngine
from chatbot.context_manager import ContextManager
from chatbot.response_generator import ResponseGenerator


class NLPTravelBot:
    """
    Main TripWise NLP Chatbot Engine orchestrating Preprocessing,
    Intent Classification, Entity Extraction, Context Management,
    Recommendation, and Response Generation.
    """
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.recommender = RecommendationEngine()
        self.context_manager = ContextManager()
        self.response_generator = ResponseGenerator(self.recommender, self.context_manager)

    def process_query(self, user_query: str, session_id: str = "default") -> Dict[str, Any]:
        """Processes user natural-language input through the full NLP pipeline."""
        # 1. Text Preprocessing & Trace
        nlp_trace = preprocess_with_trace(user_query)
        normalized_query = nlp_trace.get("normalized_text") or nlp_trace["cleaned_text"]

        # 2. Intent Classification (TF-IDF + Logistic Regression with normalized text)
        intent_data = self.intent_classifier.predict(normalized_query or user_query)

        # 3. Entity Extraction (Rule & Gazetteer with fuzzy & typo tolerance)
        entities = self.entity_extractor.extract_all(user_query)

        # 4. Context Resolution & Response Generation
        bot_output = self.response_generator.generate_response(
            text=user_query,
            intent_data=intent_data,
            extracted_entities=entities,
            session_id=session_id
        )

        missing_slots = self.context_manager.check_missing_slots(session_id)
        slot_matrix = self.context_manager.get_slot_matrix(session_id)
        dialogue_state = {
            "current_stage": "PLAN_READY" if not missing_slots else f"COLLECTING_{missing_slots[0].upper()}",
            "missing_slots": missing_slots,
            "filled_slots_count": 7 - len(missing_slots),
            "total_slots": 7
        }

        return {
            "reply": bot_output["reply"],
            "itinerary": bot_output["itinerary"],
            "booking_confirmation": bot_output.get("booking_confirmation"),
            "suggested_destinations": bot_output["suggested_destinations"],
            "quick_replies": bot_output["quick_replies"],
            "session_state": bot_output["session_state"],
            "nlp_trace": {
                "raw_query": user_query,
                "cleaned_text": nlp_trace["cleaned_text"],
                "token_count": nlp_trace["token_count"],
                "tokens": nlp_trace["tokens"],
                "filtered_tokens": nlp_trace["filtered_tokens"],
                "stemmed_tokens": nlp_trace["stemmed_tokens"],
                "intent": intent_data["intent"],
                "confidence": intent_data["confidence"],
                "top_predictions": intent_data["top_predictions"],
                "top_tfidf_features": intent_data["top_tfidf_features"],
                "extracted_entities": entities,
                "dialogue_state": dialogue_state,
                "slot_matrix": slot_matrix
            }
        }

    def reset_session(self, session_id: str = "default"):
        """Clears conversation context."""
        self.context_manager.reset_session(session_id)
