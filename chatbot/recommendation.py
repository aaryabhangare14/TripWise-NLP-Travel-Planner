import os
import json
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINATIONS_FILE = os.path.join(BASE_DIR, "data", "destinations.json")
PLACES_FILE = os.path.join(BASE_DIR, "data", "places.json")
ACTIVITY_FILE = os.path.join(BASE_DIR, "data", "activity_recommendations.json")


class RecommendationEngine:
    def __init__(self):
        self.destinations = {}
        self.places_by_dest = {}
        self.all_places = []
        self.activities_data = {}
        self._load_data()

    def _load_data(self):
        """Loads destinations, places, and activity recommendation datasets."""
        if os.path.exists(DESTINATIONS_FILE):
            with open(DESTINATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for d in data.get("destinations", []):
                    self.destinations[d["name"].lower()] = d
                    self.destinations[d["id"].lower()] = d

        if os.path.exists(PLACES_FILE):
            with open(PLACES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.all_places = data.get("places", [])
                for p in self.all_places:
                    dest_id = p.get("destination_id", "").lower()
                    if dest_id not in self.places_by_dest:
                        self.places_by_dest[dest_id] = []
                    self.places_by_dest[dest_id].append(p)

        if os.path.exists(ACTIVITY_FILE):
            with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
                act_data = json.load(f)
                for act in act_data.get("activities", []):
                    act_key = act.get("activity", "").lower()
                    self.activities_data[act_key] = act

    def get_destination(self, name: str) -> Optional[Dict[str, Any]]:
        """Lookup destination by name or alias."""
        if not name:
            return None
        return self.destinations.get(name.lower())

    def get_all_destinations(self) -> List[Dict[str, Any]]:
        """Returns unique list of all available destinations."""
        seen = set()
        result = []
        for d in self.destinations.values():
            if d["id"] not in seen:
                seen.add(d["id"])
                result.append(d)
        return result

    def suggest_destinations(self, budget: Optional[int] = None,
                             interests: Optional[List[str]] = None,
                             duration: Optional[int] = None,
                             travelers: int = 1) -> List[Dict[str, Any]]:
        """
        Recommends best-matching destinations based on budget and interest preferences.
        """
        candidates = self.get_all_destinations()
        scored = []

        duration = duration or 3
        travelers = max(1, travelers or 1)

        for dest in candidates:
            score = 0.0
            # 1. Budget feasibility
            est_cost = dest["avg_daily_cost_per_person"] * duration * travelers
            if budget:
                if est_cost <= budget:
                    score += 4.0
                elif est_cost <= budget * 1.25:
                    score += 2.0
                else:
                    score += 0.5
            else:
                score += 2.0

            # 2. Interest overlap
            if interests:
                overlap = set(dest.get("popular_interests", [])).intersection(set(interests))
                score += len(overlap) * 3.0

            scored.append((score, dest, est_cost))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                **item[1],
                "match_score": round(item[0], 1),
                "estimated_trip_cost": item[2]
            }
            for item in scored[:4]
        ]

    def generate_itinerary(self,
                           destination_name: str,
                           duration: int = 3,
                           budget: Optional[int] = None,
                           travelers: int = 1,
                           interests: Optional[List[str]] = None,
                           excluded_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds a comprehensive day-by-day itinerary tailored to user preferences,
        duration, and budget constraints.
        """
        dest = self.get_destination(destination_name)
        if not dest:
            dest_id = destination_name.lower().replace(" ", "_")
            dest = {
                "id": dest_id,
                "name": destination_name.title(),
                "tagline": "Scenic Getaway",
                "avg_daily_cost_per_person": 3000,
                "popular_interests": interests or ["nature", "culture"],
                "weather_summary": "Favorable travel conditions with pleasant local climate."
            }

        dest_id = dest["id"].lower()
        available_places = self.places_by_dest.get(dest_id, []).copy()

        # Filter out excluded categories
        excluded = set(c.lower() for c in (excluded_categories or []))
        if excluded:
            available_places = [p for p in available_places if p.get("category", "").lower() not in excluded]

        # Score and rank available attractions
        user_interests = set(i.lower() for i in (interests or []))

        def place_score(p):
            score = float(p.get("rating", 4.5))
            if p.get("category", "").lower() in user_interests:
                score += 3.5
            for tag in p.get("tags", []):
                if tag.lower() in user_interests:
                    score += 1.5
            return score

        available_places.sort(key=place_score, reverse=True)

        import datetime
        import random

        duration = max(1, min(duration, 10))
        travelers = max(1, travelers or 1)

        # Calculate journey calendar dates (Starting 1 month from the present date)
        import calendar
        today = datetime.date.today()
        next_month = 1 if today.month == 12 else today.month + 1
        next_year = today.year + 1 if today.month == 12 else today.year
        max_days = calendar.monthrange(next_year, next_month)[1]
        base_start = datetime.date(next_year, next_month, min(today.day, max_days))
        base_end = base_start + datetime.timedelta(days=duration - 1)
        start_date_str = base_start.strftime("%d %b %Y")
        end_date_str = base_end.strftime("%d %b %Y")

        # Generate unique Booking Reference
        rand_num = random.randint(1000, 9999)
        dest_prefix = dest['id'][:3].upper()
        booking_id = f"TW-{base_start.year}-{dest_prefix}-{rand_num}"

        # Allocate places across days
        days_schedule = []
        assigned_place_ids = set()

        # Day themes
        themes = [
            "Arrival, Orientation & Iconic Highlights",
            "Adventure Expeditions & Scenic Landscapes",
            "Cultural Heritage & Culinary Discovery",
            "Nature Trails, Waterfalls & Hidden Gems",
            "Leisure, Bohemian Cafes & Sunset Views",
            "High Altitude Exploration",
            "Local Souvenirs, Check-out & Departure"
        ]

        time_ranges = {
            "Morning": "09:00 AM – 12:30 PM",
            "Afternoon": "01:30 PM – 05:00 PM",
            "Evening": "06:30 PM – 09:30 PM"
        }

        total_activity_cost = 0

        for day_num in range(1, duration + 1):
            day_date = base_start + datetime.timedelta(days=day_num - 1)
            date_formatted = day_date.strftime("%a, %d %b %Y")
            day_theme = themes[(day_num - 1) % len(themes)]
            day_places = []

            # Day 1 Milestone: Arrival & Check-in
            if day_num == 1:
                day_places.append({
                    "id": f"arrival_{day_num}",
                    "name": f"Arrival in {dest['name']} & Hotel Check-in",
                    "time_slot": "Morning",
                    "time_range": "08:30 AM – 10:30 AM",
                    "category": "logistics",
                    "duration_hours": 2.0,
                    "cost": 0,
                    "rating": 5.0,
                    "description": f"Private cab pickup from airport/railway station, scenic drive to your resort, welcome drink, and smooth room check-in.",
                    "tags": ["arrival", "check-in", "transport"]
                })

            # Pick 2-3 attractions per day respecting time slots
            slots = ["morning", "afternoon", "evening"]
            for slot in slots:
                if day_num == 1 and slot == "morning":
                    continue  # Already filled with arrival check-in

                candidate = None
                for p in available_places:
                    if p["id"] not in assigned_place_ids:
                        if p.get("time_slot") == slot:
                            candidate = p
                            break

                if not candidate:
                    for p in available_places:
                        if p["id"] not in assigned_place_ids:
                            candidate = p
                            break

                if candidate:
                    assigned_place_ids.add(candidate["id"])
                    slot_name = slot.capitalize()
                    day_places.append({
                        "id": candidate["id"],
                        "name": candidate["name"],
                        "time_slot": slot_name,
                        "time_range": time_ranges.get(slot_name, "Flexible"),
                        "category": candidate.get("category", "sightseeing"),
                        "duration_hours": candidate.get("duration_hours", 2.0),
                        "cost": candidate.get("cost", 100),
                        "rating": candidate.get("rating", 4.7),
                        "description": candidate.get("description", ""),
                        "tags": candidate.get("tags", [])
                    })
                    total_activity_cost += candidate.get("cost", 100) * travelers

            # Final Day Milestone: Departure Transfer
            if day_num == duration:
                day_places.append({
                    "id": f"departure_{day_num}",
                    "name": f"Hotel Check-out & Farewell Departure Transfer",
                    "time_slot": "Evening",
                    "time_range": "06:00 PM – 08:30 PM",
                    "category": "logistics",
                    "duration_hours": 2.5,
                    "cost": 0,
                    "rating": 5.0,
                    "description": f"Pack bags, hotel check-out assistance, last-minute souvenir shopping, and private transfer to airport/railway station.",
                    "tags": ["departure", "transfer", "logistics"]
                })

            days_schedule.append({
                "day": day_num,
                "calendar_date": date_formatted,
                "title": f"Day {day_num} ({date_formatted}) – {day_theme}",
                "places": day_places
            })

        # Calculate comprehensive budget estimation adaptively based on budget tier
        daily_budget_per_person = (budget / (duration * travelers)) if budget else 3500

        if daily_budget_per_person < 2500:
            # Budget / Backpacker Tier
            per_night_room = 1200
            daily_food_per_person = 500
            daily_local_transport = 450
        elif daily_budget_per_person > 5500:
            # Luxury Tier
            per_night_room = 4500
            daily_food_per_person = 1500
            daily_local_transport = 1400
        else:
            # Moderate Tier
            per_night_room = 2200
            daily_food_per_person = 800
            daily_local_transport = 750

        rooms_needed = max(1, (travelers + 1) // 2)
        nights = max(1, duration - 1) if duration > 1 else 1
        total_hotel_cost = rooms_needed * nights * per_night_room
        total_food_cost = travelers * duration * daily_food_per_person
        total_transport_cost = duration * daily_local_transport

        estimated_total_cost = total_activity_cost + total_hotel_cost + total_food_cost + total_transport_cost

        # Budget status
        budget_status = "within"
        budget_difference = 0
        if budget:
            budget_difference = budget - estimated_total_cost
            if budget_difference < 0:
                budget_status = "exceeded"
            elif budget_difference >= 3000:
                budget_status = "well_under"
            else:
                budget_status = "on_track"

        return {
            "booking_id": booking_id,
            "destination": dest["name"],
            "destination_id": dest["id"],
            "duration": duration,
            "travelers": travelers,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "active_interests": list(user_interests),
            "excluded_categories": list(excluded),
            "weather_summary": dest.get("weather_summary", "Pleasant conditions expected."),
            "itinerary_days": days_schedule,
            "cost_breakdown": {
                "activities": total_activity_cost,
                "accommodation": total_hotel_cost,
                "food": total_food_cost,
                "local_transport": total_transport_cost,
                "total_estimated": estimated_total_cost,
                "user_budget": budget,
                "difference": budget_difference,
                "status": budget_status
            }
        }

    def get_activity_info(self, activity_key: str) -> Optional[Dict[str, Any]]:
        """Lookup activity data by normalized activity key."""
        if not activity_key:
            return None
        return self.activities_data.get(activity_key.lower())

    def recommend_by_activity(self,
                              activity_key: str,
                              budget: Optional[int] = None,
                              duration: Optional[int] = None,
                              origin_city: Optional[str] = None,
                              season: Optional[str] = None,
                              sort_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommends and ranks destinations tailored to an activity, with personalized
        filters for budget, trip duration, proximity to origin city, and cost preference.
        """
        act_info = self.get_activity_info(activity_key)
        if not act_info:
            return {
                "activity": activity_key,
                "found": False,
                "display_name": activity_key.replace("_", " ").title() if activity_key else "Adventure",
                "icon": "🧭",
                "destinations": [],
                "message": f"I don't currently have enough destination information for this activity."
            }

        destinations = list(act_info.get("destinations", []))

        # Personalization & Ranking:
        # Score each destination based on matches with user constraints
        def score_destination(d):
            score = 100.0

            # Proximity / Origin City match (e.g. Kolad near Mumbai/Pune)
            if origin_city:
                orig_lower = origin_city.lower()
                near = [c.lower() for c in d.get("near_cities", [])]
                if orig_lower in near:
                    score += 60.0
                elif orig_lower in d.get("state", "").lower():
                    score += 35.0

            # Duration match
            if duration:
                ideal = d.get("ideal_days", 3)
                diff = abs(ideal - duration)
                score += max(0.0, 30.0 - diff * 10.0)

            # Budget feasibility
            if budget:
                cost = d.get("avg_cost_per_person", 10000)
                if cost <= budget:
                    score += 25.0
                else:
                    score -= 15.0

            return score

        # If user explicitly asked for "cheaper" / "lowest budget":
        if sort_by in ["cost", "cheaper", "cheapest", "price", "budget"]:
            destinations = sorted(destinations, key=lambda x: x.get("avg_cost_per_person", 999999))
        elif origin_city or duration or budget:
            destinations = sorted(destinations, key=score_destination, reverse=True)

        return {
            "activity": activity_key,
            "found": True,
            "display_name": act_info.get("display_name", activity_key.title()),
            "icon": act_info.get("icon", "🎯"),
            "category": act_info.get("category", "adventure"),
            "destinations": destinations,
            "filters_applied": {
                "budget": budget,
                "duration": duration,
                "origin_city": origin_city,
                "sort_by": sort_by
            }
        }
