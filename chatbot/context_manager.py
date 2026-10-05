import time
from typing import Dict, Any, List, Optional


REQUIRED_SLOTS = [
    "destination",
    "duration",
    "budget",
    "travel_with",
    "interests",
    "transport",
    "accommodation"
]


class ContextManager:
    """
    Maintains user conversation context, slot filling state,
    and handles dynamic itinerary modifications.
    """
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str = "default") -> Dict[str, Any]:
        """Retrieves or creates a session context."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "destination": None,
                "duration": None,
                "budget": None,
                "travelers": 1,
                "travel_with": None,
                "interests": [],
                "transport": None,
                "accommodation": None,
                "excluded_categories": [],
                "current_itinerary": None,
                "booking_data": None,
                "last_intent": None,
                "last_interaction": time.time(),
                "conversation_stage": "idle",
                "itinerary_generated": False,
                "last_activity": None,
                "last_activity_recommendations": [],
                "origin_city": None,
                "history": []
            }
        return self.sessions[session_id]

    def reset_session(self, session_id: str = "default") -> None:
        """Clears state for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def update_state(self, session_id: str,
                     intent: str,
                     entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates session state with newly extracted entities and manages slot updates.
        """
        session = self.get_session(session_id)
        session["last_intent"] = intent
        session["last_interaction"] = time.time()

        # Update destination if newly extracted
        if entities.get("destination"):
            new_dest = entities["destination"]
            if session.get("destination") and session.get("destination").lower() != new_dest.lower():
                session["current_itinerary"] = None
                session["booking_data"] = None
                session["itinerary_generated"] = False
                if not entities.get("duration"):
                    session["duration"] = None
                if not entities.get("budget"):
                    session["budget"] = None
                if not entities.get("travel_with"):
                    session["travel_with"] = None
                if not entities.get("transport"):
                    session["transport"] = None
                if not entities.get("accommodation"):
                    session["accommodation"] = None
                if not entities.get("interests"):
                    session["interests"] = []
                session["excluded_categories"] = []
            session["destination"] = new_dest
        elif entities.get("unavailable_destination") and intent in ["destination_selection", "plan_trip"]:
            session["destination"] = None
            session["current_itinerary"] = None
            session["booking_data"] = None
            session["itinerary_generated"] = False

        # Update duration if newly extracted
        if entities.get("duration"):
            session["duration"] = entities["duration"]

        # Update budget if newly extracted (and not a hypothetical budget feasibility inquiry)
        if entities.get("budget") and intent != "budget_calculation" and not entities.get("budget_calc"):
            session["budget"] = entities["budget"]

        # Update travelers if newly extracted
        if entities.get("travelers"):
            session["travelers"] = entities["travelers"]

        # Update travel companions / type
        if entities.get("travel_with"):
            session["travel_with"] = entities["travel_with"]
            if session["travel_with"] == "Couple" and session["travelers"] == 1:
                session["travelers"] = 2
            elif session["travel_with"] == "Solo":
                session["travelers"] = 1

        # Update transport mode
        if entities.get("transport"):
            session["transport"] = entities["transport"]

        # Update accommodation preference
        if entities.get("accommodation"):
            session["accommodation"] = entities["accommodation"]

        # Update removals (e.g., 'remove beaches')
        removals = entities.get("removals", [])
        for rem in removals:
            if rem not in session["excluded_categories"]:
                session["excluded_categories"].append(rem)
            if rem in session["interests"]:
                session["interests"].remove(rem)

        # Update additions / interests
        additions = entities.get("additions", [])
        for add in additions:
            if add not in session["interests"]:
                session["interests"].append(add)
            if add in session["excluded_categories"]:
                session["excluded_categories"].remove(add)

        # General interests
        for item in entities.get("interests", []):
            if item not in session["interests"] and item not in session["excluded_categories"]:
                session["interests"].append(item)

        # Update activity tracking
        if entities.get("activity_data"):
            act_info = entities["activity_data"]
            if not act_info.get("is_unsupported"):
                session["last_activity"] = act_info.get("activity")

        # Update origin / location preference
        if entities.get("origin_city"):
            session["origin_city"] = entities["origin_city"]

        return session

    def check_missing_slots(self, session_id: str) -> List[str]:
        """Checks for essential missing slots in conversational order."""
        session = self.get_session(session_id)
        missing = []
        for slot in REQUIRED_SLOTS:
            val = session.get(slot)
            if val is None or (isinstance(val, list) and len(val) == 0):
                missing.append(slot)
        return missing

    def get_slot_matrix(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns slot table with statuses for NLP inspection."""
        session = self.get_session(session_id)
        matrix = []
        for slot in REQUIRED_SLOTS:
            val = session.get(slot)
            filled = val is not None and not (isinstance(val, list) and len(val) == 0)
            matrix.append({
                "slot": slot,
                "value": val,
                "status": "FILLED" if filled else "PENDING"
            })
        return matrix
