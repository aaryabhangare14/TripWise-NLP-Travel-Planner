from typing import Dict, Any, List, Optional
from chatbot.recommendation import RecommendationEngine
from chatbot.context_manager import ContextManager
from chatbot.dialogue_manager import DialogueManager


class ResponseGenerator:
    def __init__(self, recommendation_engine: RecommendationEngine, context_manager: ContextManager):
        self.recommender = recommendation_engine
        self.context = context_manager
        self.dialogue_manager = DialogueManager(self.recommender, self.context)

    def _get_session_state_dict(self, session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "destination": session.get("destination"),
            "duration": session.get("duration"),
            "budget": session.get("budget"),
            "travelers": session.get("travelers"),
            "travel_with": session.get("travel_with"),
            "transport": session.get("transport"),
            "accommodation": session.get("accommodation"),
            "interests": session.get("interests"),
            "excluded_categories": session.get("excluded_categories"),
            "itinerary_generated": session.get("itinerary_generated", False),
            "last_activity": session.get("last_activity"),
            "origin_city": session.get("origin_city"),
            "booking_id": session.get("booking_data", {}).get("booking_id") if session.get("booking_data") else None
        }

    def _format_activity_recommendations(self, rec_data: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        display_name = rec_data.get("display_name", "Adventure")
        icon = rec_data.get("icon", "🧭")
        destinations = rec_data.get("destinations", [])
        filters = rec_data.get("filters_applied", {})

        filter_notes = []
        if filters.get("origin_city"):
            filter_notes.append(f"📍 Near **{filters['origin_city']}**")
        if filters.get("duration"):
            filter_notes.append(f"📅 **{filters['duration']} Days**")
        if filters.get("budget"):
            filter_notes.append(f"💰 Under **₹{filters['budget']:,}**")
        if filters.get("sort_by") == "cost":
            filter_notes.append("🏷️ **Sorted by Lowest Cost**")

        filter_line = f" *({', '.join(filter_notes)})*\n\n" if filter_notes else "\n\n"

        lines = [f"{icon} **{display_name} Destinations**{filter_line}"]

        for i, d in enumerate(destinations[:5], 1):
            name = d.get("name", "")
            state = d.get("state", "")
            desc = d.get("description", "")
            best_for = " + ".join(d.get("best_for", [])[:3])
            dur = d.get("duration", "2–3 days")
            cost = d.get("avg_cost_per_person")
            cost_str = f" (~₹{cost:,}/person)" if cost else ""

            entry = (
                f"{i}. **{name}, {state}**\n"
                f"   • {desc}\n"
                f"   • **Best for:** {best_for}\n"
                f"   • **Recommended duration:** {dur}{cost_str}\n"
            )
            lines.append(entry)

        lines.append(
            "Would you like me to create a complete itinerary based on your budget and number of days?"
        )

        reply = "\n".join(lines)

        quick_dest = None
        for d in destinations:
            if self.recommender.get_destination(d["name"]):
                quick_dest = d["name"]
                break
        if not quick_dest and destinations:
            quick_dest = destinations[0]["name"]

        quick_replies = [
            f"Plan trip to {quick_dest}" if quick_dest else "Plan trip to Rishikesh",
            "Which is cheaper?",
            "2-day options",
            "Options near Mumbai"
        ]

        return {
            "reply": reply,
            "quick_replies": quick_replies
        }

    def generate_response(self,
                          text: str,
                          intent_data: Dict[str, Any],
                          extracted_entities: Dict[str, Any],
                          session_id: str = "default") -> Dict[str, Any]:
        """
        Coordinates intent classification, entity extraction, context tracking,
        dialogue turn management, and recommendation generation.
        """
        intent = intent_data["intent"]
        confidence = intent_data["confidence"]

        # Check for explicit "plan another trip" or "start over"
        if text.lower().strip() in ["plan another trip", "start new trip", "new trip", "restart", "start over"]:
            self.context.reset_session(session_id)
            session = self.context.get_session(session_id)
            next_q = self.dialogue_manager.SLOT_PROMPTS["destination"]
            return {
                "reply": next_q["prompt"],
                "itinerary": None,
                "booking_confirmation": None,
                "suggested_destinations": None,
                "quick_replies": next_q["quick_replies"],
                "session_state": {
                    "destination": None,
                    "duration": None,
                    "budget": None,
                    "travelers": 1,
                    "travel_with": None,
                    "transport": None,
                    "accommodation": None,
                    "interests": [],
                    "excluded_categories": [],
                    "itinerary_generated": False,
                    "booking_id": None
                }
            }

        # Update conversational state
        session = self.context.update_state(session_id, intent, extracted_entities)

        # Check for unavailable destination inquiry or selection
        if extracted_entities.get("unavailable_destination"):
            unavailable_dest = extracted_entities["unavailable_destination"]
            reply_text = (
                f"📍 **Location Not Available: {unavailable_dest}**\n\n"
                f"I'm sorry, but **{unavailable_dest}** is currently not available in TripWise.\n\n"
                f"🌴 **Currently Available Destinations:**\n"
                f"TripWise currently supports curated itineraries, verified hotels, and local sightseeing for these **11 popular destinations**:\n"
                f"• 🏖️ **Goa** – Sun, Sand & Nightlife\n"
                f"• 🏔️ **Manali** – Snow Peaks & Adventure\n"
                f"• 🌴 **Kerala** – Backwaters & Tea Gardens\n"
                f"• 🏰 **Jaipur** – Royal Heritage & Palaces\n"
                f"• 🏔️ **Ladakh** – High Mountain Passes & Lakes\n"
                f"• 🧘 **Rishikesh** – Yoga & River Rafting\n"
                f"• 🌲 **Ooty** – Queen of the Nilgiri Hills\n"
                f"• 🏰 **Udaipur** – City of Lakes & Romance\n"
                f"• 🕌 **Agra** – Taj Mahal & Mughal Heritage\n"
                f"• 🕉️ **Varanasi** – Ghats & Spiritual Heritage\n"
                f"• 🫖 **Darjeeling** – Himalayan Views & Tea Gardens\n\n"
                f"👉 Please choose one of the available destinations above to plan your trip!"
            )
            quick_replies = [
                "Goa", "Manali", "Kerala", "Jaipur",
                "Ladakh", "Rishikesh", "Ooty", "Udaipur"
            ]
            return {
                "reply": reply_text,
                "itinerary": None,
                "booking_confirmation": None,
                "suggested_destinations": None,
                "quick_replies": quick_replies,
                "session_state": {
                    "destination": session.get("destination"),
                    "duration": session.get("duration"),
                    "budget": session.get("budget"),
                    "travelers": session.get("travelers"),
                    "travel_with": session.get("travel_with"),
                    "transport": session.get("transport"),
                    "accommodation": session.get("accommodation"),
                    "interests": session.get("interests"),
                    "excluded_categories": session.get("excluded_categories"),
                    "itinerary_generated": session.get("itinerary_generated", False),
                    "booking_id": session.get("booking_data", {}).get("booking_id") if session.get("booking_data") else None
                }
            }

        reply_text = ""
        itinerary = None
        booking_confirmation = None
        suggested_destinations = None
        quick_replies = []

        # Activity-Based Destination Recommendation Handler
        activity_data = extracted_entities.get("activity_data")
        sort_preference = extracted_entities.get("sort_preference")
        origin_city = extracted_entities.get("origin_city")
        has_dest_in_query = bool(extracted_entities.get("destination"))
        has_session_dest = bool(session.get("destination"))

        is_explicit_activity_intent = (intent == "activity_based_recommendation")
        is_activity_query = (
            not has_dest_in_query and (
                is_explicit_activity_intent or
                (not has_session_dest and activity_data is not None) or
                (not has_session_dest and session.get("last_activity") is not None and (sort_preference or origin_city or extracted_entities.get("duration") or extracted_entities.get("budget")))
            )
        )

        if is_activity_query:
            # 1. Fallback for unsupported activities (e.g. canyoning)
            if activity_data and activity_data.get("is_unsupported"):
                raw_act = activity_data.get("raw_activity", "this activity")
                reply_text = (
                    f"I understand that you're interested in {raw_act}. "
                    f"I don't currently have enough destination information for this activity. "
                    f"Would you like me to suggest similar adventure destinations?"
                )
                quick_replies = ["River Rafting", "Trekking", "Scuba Diving", "Paragliding", "Camping"]
                return {
                    "reply": reply_text,
                    "itinerary": None,
                    "booking_confirmation": None,
                    "suggested_destinations": None,
                    "quick_replies": quick_replies,
                    "session_state": self._get_session_state_dict(session)
                }

            # 2. Extract or resolve active activity
            activity_key = None
            if activity_data and not activity_data.get("is_unsupported"):
                activity_key = activity_data["activity"]
            elif session.get("last_activity"):
                activity_key = session.get("last_activity")

            if activity_key:
                session["last_activity"] = activity_key
                if origin_city:
                    session["origin_city"] = origin_city
                budget = extracted_entities.get("budget") or session.get("budget")
                duration = extracted_entities.get("duration") or session.get("duration")
                origin = origin_city or (session.get("origin_city") if not activity_data else None)
                sort_by = sort_preference

                rec_data = self.recommender.recommend_by_activity(
                    activity_key=activity_key,
                    budget=budget,
                    duration=duration,
                    origin_city=origin,
                    sort_by=sort_by
                )
                session["last_activity_recommendations"] = rec_data.get("destinations", [])
                formatted = self._format_activity_recommendations(rec_data, session)

                return {
                    "reply": formatted["reply"],
                    "itinerary": None,
                    "booking_confirmation": None,
                    "suggested_destinations": None,
                    "quick_replies": formatted["quick_replies"],
                    "session_state": self._get_session_state_dict(session)
                }

        # 1. Context Memory Inquiry
        if intent == "memory_query" or extracted_entities.get("memory_query") is not None:
            query_type = extracted_entities.get("memory_query") or "all"
            res = self.dialogue_manager.handle_memory_query(session, query_type)
            reply_text = res["reply"]
            quick_replies = res["quick_replies"]
            if not session.get("itinerary_generated"):
                missing = self.context.check_missing_slots(session_id)
                if missing:
                    next_q = self.dialogue_manager.get_next_question(session, missing)
                    if next_q:
                        reply_text += f"\n\n👉 *Let's continue planning your trip:* {next_q['prompt']}"
                        quick_replies = next_q["quick_replies"]

        # 2. Budget Feasibility & Calculation
        elif intent == "budget_calculation" or extracted_entities.get("budget_calc") is not None:
            target_budget = extracted_entities.get("budget_calc") or extracted_entities.get("budget")
            res = self.dialogue_manager.handle_budget_calculation(session, target_budget)
            reply_text = res["reply"]
            quick_replies = res["quick_replies"]

        # 3. Dynamic Itinerary Modifications
        elif intent == "modify_itinerary":
            destination = session.get("destination")
            if not destination:
                dest_in_query = extracted_entities.get("destination")
                if dest_in_query:
                    session["destination"] = dest_in_query
                    destination = dest_in_query

            if not destination:
                reply_text = "I don't have an active itinerary to modify yet! Tell me which destination you'd like to plan for first (e.g. *“Plan 3 days in Goa”*)."
                quick_replies = ["Plan 3 days in Goa", "Plan 4 days in Manali", "Plan 5 days in Kerala"]
            else:
                duration = session.get("duration") or 3
                budget = session.get("budget")
                travelers = session.get("travelers") or 1
                interests = session.get("interests", [])
                excluded = session.get("excluded_categories", [])

                itinerary = self.recommender.generate_itinerary(
                    destination_name=destination,
                    duration=duration,
                    budget=budget,
                    travelers=travelers,
                    interests=interests,
                    excluded_categories=excluded
                )
                session["current_itinerary"] = itinerary
                session["itinerary_generated"] = True

                changes = []
                if extracted_entities.get("removals"):
                    changes.append(f"removed **{', '.join(extracted_entities['removals'])}**")
                if extracted_entities.get("additions"):
                    changes.append(f"added **{', '.join(extracted_entities['additions'])}**")
                if extracted_entities.get("budget"):
                    changes.append(f"updated budget to **₹{extracted_entities['budget']:,}**")
                if extracted_entities.get("duration"):
                    changes.append(f"adjusted duration to **{extracted_entities['duration']} days**")
                if extracted_entities.get("destination"):
                    changes.append(f"changed destination to **{extracted_entities['destination'].title()}**")

                change_desc = f" ({'; '.join(changes)})" if changes else ""
                reply_text = (
                    f"✨ **Itinerary Updated!** I've adjusted your plan{change_desc}.\n\n"
                    f"{self.dialogue_manager.format_itinerary_response(session, itinerary)}"
                )
                quick_replies = [
                    "🎟️ Confirm Booking & Invoice PDF",
                    "Suggest restaurants",
                    "Can I do this under 10k?",
                    "Show weather info"
                ]

        # 4. Booking & Invoice Confirmation
        elif intent == "confirm_booking":
            destination = session.get("destination") or "Goa"
            duration = session.get("duration") or 3
            budget = session.get("budget")
            travelers = session.get("travelers") or 1
            interests = session.get("interests", [])
            excluded = session.get("excluded_categories", [])

            itinerary = session.get("current_itinerary")
            if not itinerary:
                itinerary = self.recommender.generate_itinerary(
                    destination_name=destination,
                    duration=duration,
                    budget=budget,
                    travelers=travelers,
                    interests=interests,
                    excluded_categories=excluded
                )
                session["current_itinerary"] = itinerary

            booking_id = itinerary.get("booking_id", f"TW-2026-{destination[:3].upper()}-8821")
            start_date = itinerary.get("start_date")
            end_date = itinerary.get("end_date")
            cost_breakdown = itinerary.get("cost_breakdown", {})
            total_amount = cost_breakdown.get("total_estimated", 15000)

            booking_data = {
                "booking_id": booking_id,
                "customer_name": "Ronald",
                "destination": destination,
                "duration": duration,
                "travelers": travelers,
                "start_date": start_date,
                "end_date": end_date,
                "cost_breakdown": cost_breakdown,
                "itinerary_days": itinerary.get("itinerary_days", []),
                "total_amount": total_amount,
                "status": "CONFIRMED",
                "download_url": f"/api/download_invoice?booking_id={booking_id}&session_id={session_id}"
            }
            session["booking_data"] = booking_data
            booking_confirmation = booking_data

            reply_text = (
                f"✅ **Booking & Tickets Confirmed!**\n\n"
                f"Your travel package for **{destination}** has been locked in with Booking Reference: `{booking_id}`.\n\n"
                f"• **Lead Passenger:** Ronald ({travelers} Traveler{'s' if travelers > 1 else ''})\n"
                f"• **Journey Dates:** {start_date} to {end_date} ({duration} Days)\n"
                f"• **Tickets & Vouchers:** All attraction entries, hotel stay vouchers, and transfer passes are issued.\n"
                f"• **Invoice Total:** ₹{total_amount:,} (All Taxes & Tourism GST Included)\n\n"
                f"Click below to download your official **Tax Invoice & Travel Pass (PDF)**."
            )
            quick_replies = [
                "Download Invoice PDF",
                f"Weather in {destination}",
                f"Food guide for {destination}",
                "Plan another trip"
            ]

        # 5. Conversational Step-by-Step Slot Filling & Plan Flow
        elif intent in [
            "greeting",
            "destination_selection",
            "duration_information",
            "budget_information",
            "companions_information",
            "interests_information",
            "transport_information",
            "accommodation_information",
            "plan_trip"
        ]:
            if intent == "greeting" and not any(session.get(s) for s in ["destination", "duration", "budget", "travel_with", "transport", "accommodation"]):
                next_q = self.dialogue_manager.SLOT_PROMPTS["destination"]
                reply_text = next_q["prompt"]
                quick_replies = next_q["quick_replies"]
            else:
                missing_slots = self.context.check_missing_slots(session_id)
                if not missing_slots:
                    # All 7 slots filled!
                    destination = session.get("destination") or "Goa"
                    duration = session.get("duration") or 3
                    budget = session.get("budget")
                    travelers = session.get("travelers") or 1
                    interests = session.get("interests", [])
                    excluded = session.get("excluded_categories", [])

                    itinerary = self.recommender.generate_itinerary(
                        destination_name=destination,
                        duration=duration,
                        budget=budget,
                        travelers=travelers,
                        interests=interests,
                        excluded_categories=excluded
                    )
                    session["current_itinerary"] = itinerary
                    session["itinerary_generated"] = True

                    reply_text = self.dialogue_manager.format_itinerary_response(session, itinerary)
                    quick_replies = [
                        "🎟️ Confirm Booking & Invoice PDF",
                        "Suggest restaurants",
                        "Can I do this under 10k?",
                        "Change duration to 5 days"
                    ]
                else:
                    if not session.get("destination") and session.get("interests"):
                        user_interests = session.get("interests", [])
                        suggested = self.recommender.suggest_destinations(
                            budget=session.get("budget"),
                            interests=user_interests,
                            duration=session.get("duration"),
                            travelers=session.get("travelers", 1)
                        )
                        if suggested:
                            int_str = ", ".join(i.title() for i in user_interests)
                            dest_lines = []
                            for idx, d in enumerate(suggested[:3], 1):
                                desc = d.get('description', '')
                                if len(desc) > 90:
                                    desc = desc[:90].rsplit(' ', 1)[0] + '...'
                                dest_lines.append(f"{idx}. 🌟 **{d['name']}** ({d.get('state', '')}) – {desc}")
                            reply_text = (
                                f"Great! Based on your interest in **{int_str}**, here are top recommended destinations you might love:\n\n"
                                + "\n\n".join(dest_lines)
                                + "\n\n👉 **Where would you like to travel?** (Choose one above or name any destination!)"
                            )
                            quick_replies = [d['name'] for d in suggested[:4]]
                        else:
                            next_q = self.dialogue_manager.get_next_question(session, missing_slots)
                            reply_text = next_q["prompt"]
                            quick_replies = next_q["quick_replies"]
                    else:
                        next_q = self.dialogue_manager.get_next_question(session, missing_slots)
                        reply_text = next_q["prompt"]
                        quick_replies = next_q["quick_replies"]

        elif intent == "goodbye":
            reply_text = "Safe travels and have a wonderful adventure ahead! 🌟 Feel free to return anytime you need travel plans. Bye!"

        elif intent == "help":
            reply_text = (
                "### 🧭 What I Can Do:\n\n"
                "1. **Interactive Trip Planning**: I guide you step-by-step through destination, dates, budget, companions, and stay.\n"
                "2. **Conversational Memory**: Ask me *“What was my budget?”* or *“Where am I going?”* at any point!\n"
                "3. **Dynamic Modifications**: *“Change my trip to 5 days”* or *“Add adventure activities”*\n"
                "4. **Budget Feasibility**: *“Can I do this trip under ₹10,000?”*\n"
                "5. **Local Sightseeing & Food**: *“What are famous foods in Jaipur?”*\n"
                "6. **Weather & Season**: *“What is the weather in Manali?”*"
            )
            quick_replies = [
                "Plan 4 days in Goa",
                "Suggest destinations under 20k",
                "Top attractions in Rishikesh",
                "Weather in Ladakh"
            ]

        elif intent == "find_destination":
            text_lower = text.lower()
            if any(k in text_lower for k in ["available", "supported", "all destination", "what places", "which places", "which location", "what location", "list destination", "where can i go"]):
                reply_text = (
                    "🌴 **TripWise Currently Available Destinations:**\n\n"
                    "We support curated travel itineraries, verified stays, and top sightseeing for these **11 destinations**:\n\n"
                    "• 🏖️ **Goa** – Sun, Sand, Beaches & Nightlife\n"
                    "• 🏔️ **Manali** – Snow Peaks, Solang Valley & Adventure\n"
                    "• 🌴 **Kerala** – Backwaters, Munnar Tea Gardens & Houseboats\n"
                    "• 🏰 **Jaipur** – Amber Fort, Hawa Mahal & Royal Heritage\n"
                    "• 🏔️ **Ladakh** – Pangong Lake, High Mountain Passes & Monasteries\n"
                    "• 🧘 **Rishikesh** – Yoga Capital, River Rafting & Ganga Aarti\n"
                    "• 🌲 **Ooty** – Nilgiri Hills, Toy Train & Tea Estates\n"
                    "• 🏰 **Udaipur** – City of Lakes, Lake Pichola & Palaces\n"
                    "• 🕌 **Agra** – Taj Mahal & Mughal Architecture\n"
                    "• 🕉️ **Varanasi** – Sacred Ghats of Ganga & Kashi Vishwanath\n"
                    "• 🫖 **Darjeeling** – Mt. Kanchenjunga Vistas, Tiger Hill & Tea Gardens\n\n"
                    "👉 Where would you like to travel? Type a destination name to start planning!"
                )
                quick_replies = ["Goa", "Manali", "Kerala", "Jaipur", "Ladakh", "Rishikesh"]
            else:
                budget = session.get("budget")
                interests = session.get("interests")
                duration = session.get("duration")
                travelers = session.get("travelers", 1)

                matches = self.recommender.suggest_destinations(
                    budget=budget,
                    interests=interests,
                    duration=duration,
                    travelers=travelers
                )
                suggested_destinations = matches

                dest_names = [m["name"] for m in matches[:3]]
                reply_text = (
                    f"Based on your preferences, here are top recommended destinations: "
                    f"**{', '.join(dest_names)}**.\n\n"
                    f"Click any destination card on the left or type *“Plan a trip to {dest_names[0]}”* to get a complete itinerary!"
                )
                quick_replies = [f"Plan {m['name']} trip" for m in matches[:3]]

        elif intent == "recommend_places":
            destination = session.get("destination") or "Goa"
            dest_info = self.recommender.get_destination(destination)
            dest_places = self.recommender.places_by_dest.get(dest_info["id"].lower() if dest_info else "goa", [])[:5]

            place_bullets = "\n".join([f"• **{p['name']}** ({p['category'].title()}) – {p['description']}" for p in dest_places])
            reply_text = (
                f"📍 **Top Attractions in {destination}:**\n\n"
                f"{place_bullets}\n\n"
                f"Would you like me to build a day-by-day plan including these?"
            )
            quick_replies = [f"Plan {destination} itinerary", "Suggest budget hotels", "Local food guide"]

        elif intent == "budget_estimate":
            destination = session.get("destination") or "Goa"
            dest_info = self.recommender.get_destination(destination)
            daily_cost = dest_info["avg_daily_cost_per_person"] if dest_info else 3000
            duration = session.get("duration") or 3
            travelers = session.get("travelers") or 1

            est_3day = daily_cost * duration * travelers
            reply_text = (
                f"💰 **Budget Estimate for {destination}:**\n\n"
                f"• **Average Daily Cost:** ~₹{daily_cost:,} per person (stay, meals & transport)\n"
                f"• **Estimated {duration}-Day Trip:** ~₹{est_3day:,} for {travelers} traveler{'s' if travelers > 1 else ''}\n"
                f"• **Budget Tier:** ~₹1,500/day (Hostels, street food, public transit)\n"
                f"• **Comfort Tier:** ~₹3,500/day (3-star hotel, cafes, local cabs)\n"
                f"• **Luxury Tier:** ~₹6,500+/day (Resorts, fine dining, private tours)"
            )
            quick_replies = [f"Plan {destination} under ₹{est_3day:,}", "Show places to visit", "Best season to visit"]

        elif intent == "weather_query":
            destination = session.get("destination") or "Manali"
            dest_info = self.recommender.get_destination(destination)
            if dest_info:
                weather_info = dest_info.get("weather_summary", "Pleasant tropical/alpine conditions.")
                best_season = dest_info.get("best_season", "October to March")
                reply_text = (
                    f"🌤️ **Weather & Season for {dest_info['name']}:**\n\n"
                    f"• **Current Climate Profile:** {weather_info}\n"
                    f"• **Best Season to Visit:** {best_season}\n"
                    f"• **What to Pack:** Comfortable footwear, light layers for evening, sunscreen/sunglasses."
                )
            else:
                reply_text = f"The climate in {destination} is generally pleasant. The best time to visit is typically between October and April."
            quick_replies = [f"Plan {destination} trip", "Places to see", "Budget estimate"]

        elif intent == "hotel_recommendation":
            destination = session.get("destination") or "Goa"
            reply_text = (
                f"🏨 **Accommodation Guide for {destination}:**\n\n"
                f"• **Budget / Backpackers:** Zostel, goSTOPS, local homestays (~₹800–₹1,500/night)\n"
                f"• **Mid-range & Couples:** Boutique heritage villas and 3-star beach/mountain resorts (~₹2,500–₹4,500/night)\n"
                f"• **Luxury:** Premium 5-star properties and private pool villas (~₹8,000+/night)\n\n"
                f"*Tip: Booking 2–3 weeks in advance saves up to 25% on peak weekend stays.*"
            )
            quick_replies = [f"Plan {destination} trip", "Food recommendations", "Top sights"]

        elif intent == "food_recommendation":
            destination = session.get("destination") or "Jaipur"
            food_map = {
                "goa": "Goan Fish Curry Thali, Prawn Balchao, Bebinca dessert, Pork Vindaloo, and refreshing Kokum Feni.",
                "manali": "Siddu with ghee, Trout Fish, Dham, Tibetan Momos, Thukpa, and hot apple crumble at Old Manali cafes.",
                "kerala": "Appam with Stew, Kerala Fish Molee, Karimeen Pollichathu, Malabar Biryani, and Banana Chips.",
                "jaipur": "Dal Baati Churma, Pyaaz Kachori at Rawat, Laal Maas, Ghevar, and sweet Lassi at Lassiwala.",
                "ladakh": "Tibetan Thukpa, butter tea (Gur Gur Chai), Tingmo bread with spicy stew, and fresh Apricot jam.",
                "rishikesh": "Ayurvedic sattvic thalis, organic smoothie bowls, wood-fired pizza at Beatles cafe, and Ganga side masala chai.",
                "ooty": "Nilgiri tea, artisanal dark chocolates, fresh strawberry fudge, and South Indian filter coffee with dosa.",
                "udaipur": "Rajasthani Dal Baati, Mirchi Vada, Gatte ki Sabzi, and rooftop Lake Pichola dining.",
                "agra": "Authentic Panchhi Petha (kesar, paan, chocolate), Bedmi Puri with spicy aloo, Mughlai Kebabs, and Jalebi.",
                "varanasi": "Kashi Tamatar Chaat, Banarasi Paan, Malaiyo (winter milk froth), Kachori Jalebi breakfast, and thick rabri lassi.",
                "darjeeling": "Steamed Darjeeling chicken/veg Momos with spicy churpi chutney, Thukpa noodle soup, Shaphalay, and fresh first-flush Darjeeling tea."
            }
            dishes = food_map.get(destination.lower(), "Authentic regional street food, traditional thalis, and local cafe specialties.")
            reply_text = (
                f"🍴 **Must-Try Food in {destination}:**\n\n"
                f"{dishes}\n\n"
                f"Be sure to visit local street markets and heritage dining spots!"
            )
            quick_replies = [f"Plan {destination} itinerary", "Show sights", "Budget breakdown"]

        elif intent == "packing_tips":
            destination = session.get("destination") or "Goa"
            packing_map = {
                "goa": "• **Clothing:** Breathable cottons, beachwear, swimwear, quick-dry shorts, and light evening linen.\n• **Footwear:** Water-resistant sandals, flip-flops, and walking sneakers for fort treks.\n• **Essentials:** High-SPF reef-safe sunscreen, polarized sunglasses, mosquito repellent, and waterproof phone pouch.",
                "manali": "• **Clothing:** Layered thermal innerwear, fleece jacket, heavy windproof coat, and woollen socks.\n• **Winter Snow:** Waterproof snow boots, insulated gloves, balaclava/beanie, and lip balm.\n• **Gear:** Sturdy trekking shoes with good grip and portable power bank (batteries drain faster in cold).",
                "kerala": "• **Clothing:** Light breathable cotton, modest wear for temple visits, and umbrella/rain poncho for coastal showers.\n• **Backwaters:** Mosquito repellent, slip-on footwear, and sun hat.\n• **Ayurveda:** Loose comfortable clothes for spa and wellness sessions.",
                "jaipur": "• **Clothing:** Modest cotton clothing for day palace tours, light sweater for breezy winter evenings.\n• **Footwear:** Comfortable walking shoes (you will walk a lot across forts like Amber and Nahargarh).\n• **Sun Protection:** Scarf or wide-brim hat, sunglasses, and rehydration salts.",
                "ladakh": "• **High Altitude:** 4 layers (Thermals, Fleece, Down Jacket, Windbreaker), UV sunglasses, cold cream.\n• **Medical:** Diamox for AMS acclimatization, camphor, pulse oximeter, and moisturizers.\n• **Cash:** Extra cash as ATMs are sparse outside Leh.",
                "rishikesh": "• **Clothing:** Active quick-dry gym/yoga wear, conservative attire for Ganga Aarti ceremonies.\n• **Water Sports:** Strap-on sports sandals for rafting, dry bag for electronics.\n• **Spiritual:** Comfortable slip-on shoes for ashrams and temple ghats.",
                "agra": "• **Clothing:** Breathable modest cottons for monument entry (shoulders and knees covered).\n• **Footwear:** Comfortable walking shoes with slip-on socks (shoe covers or bare feet inside Taj mausoleum).\n• **Sun:** Sunglasses, sun hat, and water bottle.",
                "varanasi": "• **Clothing:** Modest Indian or conservative attire for temple corridors and ghats.\n• **Ghat Walking:** Sturdy, easily removable slip-on footwear for stone steps.\n• **Essentials:** Hand sanitizer, mosquito repellent for evening aarti boat rides.",
                "darjeeling": "• **Warm Layers:** Fleece jackets, thermal innerwear, woollen scarves, and beanies.\n• **Tiger Hill:** Heavy windproof jacket and gloves for sub-zero sunrise waiting.\n• **Footwear:** Walking sneakers with good tread for hilly inclines."
            }
            checklist = packing_map.get(destination.lower(), "• Comfortable walking shoes, seasonal layers, sunscreen, power bank, and universal travel adapters.")
            reply_text = (
                f"🎒 **Packing Guide for {destination}:**\n\n"
                f"{checklist}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Are you planning any high-thrill water/adventure sports, or keeping it mostly relaxed sightseeing?"
            )
            quick_replies = [
                f"Plan {destination} itinerary",
                f"Weather in {destination}",
                "Safety tips for " + destination,
                "How to reach " + destination
            ]

        elif intent == "safety_guidelines":
            destination = session.get("destination") or "Goa"
            safety_map = {
                "goa": "• **Beaches & Sea:** Never swim past red warning flags or after sunset. Lifeguards are stationed until 6:30 PM.\n• **Solo Travelers:** Very safe and tourist-friendly. Use verified app cabs (GoaMiles) or pre-negotiated airport taxis.\n• **Night Travel:** Stick to lit arterial roads in North Goa (Candolim/Baga) and avoid isolated beaches alone late at night.",
                "manali": "• **Mountain Roads:** Drive cautiously during rain/snow. Hire experienced local hill drivers for Rohtang/Atal Tunnel.\n• **Rivers:** Never venture into the fierce Beas river currents for photos.\n• **Solo & Women Safety:** Himachal Pradesh is ranked among India's safest states for solo backpackers.",
                "kerala": "• **Backwaters:** Use only government-registered boat operators with certified lifejackets.\n• **Wildlife:** Keep safe distance from wild elephants in Wayanad and Periyar reserves.\n• **Monsoon:** Watch weather bulletins for landslide alerts in hilly terrain like Munnar.",
                "jaipur": "• **Palace Guides:** Always hire government-approved guides displaying authorized tourist ID badges.\n• **Touts & Shopping:** Politely decline aggressive street gem/carpet vendors.\n• **Emergency:** Dial 112 (National Helpline) or 100 for immediate police assistance.",
                "agra": "• **Taj Tickets:** Book official ASI tickets online to skip long queues and bypass unofficial street touts.\n• **Guides:** Hire only government-authorized guides with approved blue ID badges.\n• **Taxis:** Use pre-paid auto counters at Agra Cantt station or Ola/Uber.",
                "varanasi": "• **Boat Rides:** Negotiate boat fares beforehand or book through government-registered boatmen associations.\n• **Cremation Ghats:** Respect privacy at Manikarnika Ghat (strict no-photography rule).\n• **Temples:** Deposit leather items and electronics in official locker counters before entering Kashi Vishwanath.",
                "darjeeling": "• **Hill Driving:** Hire seasoned hill cab drivers for steep routes.\n• **Weather:** Check for fog/landslide advisories during heavy monsoon.\n• **Altitude:** Gentle pacing on steep town stairs if you have respiratory sensitivity."
            }
            tips = safety_map.get(destination.lower(), "• Stay alert in crowded areas, keep emergency helpline 112 saved, and use authorized hotel cabs.")
            reply_text = (
                f"🛡️ **Travel Safety & Guidelines for {destination}:**\n\n"
                f"{tips}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Are you traveling solo, as a couple, or with family/parents? I can customize the itinerary with verified safe routes."
            )
            quick_replies = [
                "Traveling solo",
                "Traveling with family",
                f"Best hotels in {destination}",
                f"Plan {destination} trip"
            ]

        elif intent == "transport_query":
            destination = session.get("destination") or "Goa"
            transport_map = {
                "goa": "• **Airports:** Dabolim Airport (South Goa) & MOPA Airport (North Goa).\n• **Local Transit:** Renting a scooter/Activa (~₹350–₹500/day) is the most popular way to explore. Self-drive cars available from ₹1,200/day.\n• **Taxis:** GoaMiles app and pre-paid airport taxi counters.",
                "manali": "• **By Air:** Nearest airport is Bhuntar (Kullu), 50 km away.\n• **By Road:** Overnight luxury Volvo buses run daily from Delhi (ISBT Kashmere Gate, 12–14 hrs) and Chandigarh.\n• **Local Sightseeing:** Fixed-rate union cabs for Solang Valley and Rohtang pass.",
                "kerala": "• **Airports:** Cochin International Airport (COK) is best for Munnar & Alleppey.\n• **Trains:** Excellent rail connectivity to Alleppey (ALLP) and Ernakulam.\n• **Local Transit:** Private chauffeured tourist cab is highly recommended for multi-city Kerala tours.",
                "jaipur": "• **By Air/Train:** Jaipur International Airport (JAI) and Jaipur Junction with Vande Bharat Express from Delhi.\n• **Local Transit:** E-rickshaws, Ola/Uber, and Jaipur Metro make city transit very affordable.",
                "rishikesh": "• **Nearest Airport:** Dehradun Jolly Grant Airport (35 km away).\n• **By Train:** Yog Nagari Rishikesh railway station or Haridwar Junction.\n• **Local Transit:** Auto-rickshaws and walking across suspension bridges.",
                "agra": "• **By Train:** Gatimaan Express and Vande Bharat from Delhi reach Agra in just 1 hr 40 mins.\n• **By Expressways:** Yamuna Expressway connects Delhi to Agra in 3.5 hrs by car.\n• **Local Transit:** Battery-operated e-rickshaws around the Taj Mahal eco-zone.",
                "varanasi": "• **By Air:** Lal Bahadur Shastri International Airport (VNS), 25 km from city.\n• **By Train:** Varanasi Junction (BSB) and Pt. Deen Dayal Upadhyaya Junction.\n• **Local Transit:** E-rickshaws and walking through historic narrow gallis.",
                "darjeeling": "• **Nearest Airport:** Bagdogra Airport (IXB, 70 km / 3 hrs scenic uphill drive).\n• **Nearest Rail:** New Jalpaiguri (NJP).\n• **Toy Train:** UNESCO Darjeeling Himalayan Railway connects NJP/Kurseong to Darjeeling."
            }
            guide = transport_map.get(destination.lower(), "• Well-connected by domestic flights, express trains, and state highways.")
            reply_text = (
                f"🚗 **How to Reach & Get Around {destination}:**\n\n"
                f"{guide}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Would you like me to include private airport/railway transfers in your customized package and tax invoice?"
            )
            quick_replies = [
                "Include airport pickup",
                f"Plan 3 days in {destination}",
                f"Estimate budget for {destination}",
                "Confirm booking with invoice"
            ]

        elif intent == "photography_spots":
            destination = session.get("destination") or "Jaipur"
            photo_map = {
                "goa": "1. **Fort Aguada Lighthouse:** Dramatic cliff views over the Arabian Sea.\n2. **Fontainhas Latin Quarter:** Colorful 18th-century Portuguese pastel houses and bougainvillea.\n3. **Parra Road:** Famous coconut tree avenue featured in Bollywood movies.\n4. **Curlies & Thalassa:** Sunset cliff viewpoints over Vagator & Anjuna.",
                "manali": "1. **Sissu Waterfall (via Atal Tunnel):** Towering cascading falls surrounded by alpine cliffs.\n2. **Jogini Waterfalls Trail:** Wooden footbridges and pine forest streams.\n3. **Old Manali Riverside:** Riverside rocks and bohemian cafe patios.\n4. **Solang Snow Point:** Panorama of snow peaks and paragliding skies.",
                "jaipur": "1. **Hawa Mahal Facade:** Honeycomb windows early morning with street chai.\n2. **Panna Meena Ka Kund:** Ancient geometric stepwell with stunning symmetry.\n3. **Nahargarh Fort Sunset:** Panoramic golden hour city skyline.\n4. **Patrika Gate:** Vibrant painted arches displaying Rajasthani history.",
                "kerala": "1. **Alleppey Backwaters Sunrise:** Houseboat deck view over misty lotus paddies.\n2. **Kolukkumalai Tea Estate:** World's highest organic tea plantation with cloud beds.\n3. **Varkala Cliff Edge:** Sunset overlooking red cliffs and rolling surf.\n4. **Athirappilly Waterfalls:** 'The Niagara of India' amidst dense rainforest.",
                "agra": "1. **Taj Mahal from Mehtab Bagh:** Sunset reflection across the calm Yamuna waters.\n2. **Taj Central Water Channel:** Classic symmetry reflecting ivory domes and minarets.\n3. **Agra Fort Jahangir Palace Arch:** Framing the Taj Mahal in the distance.\n4. **Fatehpur Sikri Buland Darwaza:** The majestic 54-meter gateway against the sky.",
                "varanasi": "1. **Assi Ghat Sunrise Boat:** Monks, rowboats, and morning mist over sacred waters.\n2. **Dashashwamedh Maha Aarti:** Illuminated towering brass multi-tiered fire lamps.\n3. **Chet Singh Fort Ghat:** Ancient stone fort battlements on the river edge.\n4. **Historic Painted Gallis:** Colorful shrines, old wooden doorways, and sadhus.",
                "darjeeling": "1. **Tiger Hill Sunrise:** First rays turning Mt. Kanchenjunga snow gold.\n2. **Batasia Loop:** Toy train steam engine circling landscaped memorial gardens.\n3. **Happy Valley Tea Slopes:** Endless emerald tea bushes disappearing into morning mist.\n4. **Chowrasta Mall Viewpoint:** Snowy Himalayan peaks framing pine forests."
            }
            spots = photo_map.get(destination.lower(), "• Historical forts, scenic sunset viewpoints, botanical gardens, and local heritage streets.")
            reply_text = (
                f"📸 **Top Instagram & Photography Spots in {destination}:**\n\n"
                f"{spots}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Do you prefer early morning sunrise viewpoints (fewer crowds) or golden hour sunset spots?"
            )
            quick_replies = [
                "Early morning sunrise",
                "Golden hour sunset",
                f"Plan {destination} photo tour",
                f"Cafes in {destination}"
            ]

        elif intent == "shopping_query":
            destination = session.get("destination") or "Jaipur"
            shop_map = {
                "jaipur": "• **Johari Bazaar:** Authentic Kundan jewelry, silver handicrafts, and precious gems.\n• **Bapu Bazaar:** Traditional Bandhani dupattas, camel leather Mojaris, and Jaipuri quilts (Razai).\n• **Blue Pottery:** Handcrafted ceramic vases, coasters, and wall plates.",
                "goa": "• **Anjuna Flea Market:** Bohemian jewelry, beach dresses, leather crafts, and brassware.\n• **Saturday Night Market (Arpora):** Artisanal clothes, live music, and international food stalls.\n• **Local Edibles:** Goan Cashew nuts, Feni liquor, and spicy Pork/Prawn Balchao pickles.",
                "kerala": "• **Spices:** Fresh green cardamom, black pepper, and cinnamon bark from Munnar & Thekkady.\n• **Tea & Coffee:** Nilgiri CTC and Orthodox whole-leaf tea boxes.\n• **Handicrafts:** Coconut shell carvings, Aranmula metal mirrors, and Kasavu sarees.",
                "manali": "• **Mall Road:** Pure Kullu & Pashmina shawls, woollen caps, and handcrafted wooden toys.\n• **Old Manali Bazaars:** Tibetan singing bowls, prayer flags, and silver jewellery.\n• **Local Gourmet:** Himalayan wild flower honey and fresh apple jams.",
                "agra": "• **Petha Sweets:** Authentic Panchhi Petha (Kesar, Angoori, Paan, Chocolate).\n• **Marble Inlay Art:** Pietra dura marble boxes, coasters, and Taj replicas crafted by descendants of royal artisans.\n• **Leather Goods:** Handcrafted shoes, jackets, and belts at Sadar Bazaar.",
                "varanasi": "• **Banarasi Silk Sarees:** Hand-woven Katan and Zari pure silk at Godowlia & Chowk.\n• **Gulabi Meenakari:** Traditional pink enamel jewelry and silver artifacts.\n• **Spiritual Items:** Rudraksha beads, brass puja lamps, and Ganga jal containers.",
                "darjeeling": "• **Darjeeling Tea:** Certified First Flush, Muscatel Second Flush, and White Tea from certified estates.\n• **Tibetan Handicrafts:** Woollen carpets, prayer wheels, thangka paintings, and turquoise jewelry.\n• **Handmade Sweaters:** Cozy hand-knitted cardigans and woollen caps at Mall Road stalls."
            }
            guide = shop_map.get(destination.lower(), "• Local craft markets, traditional fabrics, spices, and regional souvenirs.")
            reply_text = (
                f"🛍️ **Best Shopping & Souvenirs in {destination}:**\n\n"
                f"{guide}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Would you like me to reserve 2–3 hours on the final day of your itinerary for shopping?"
            )
            quick_replies = [
                "Add shopping to Day 3",
                f"Food guide for {destination}",
                f"Plan {destination} trip",
                "Download Invoice PDF"
            ]

        elif intent == "nightlife_query":
            destination = session.get("destination") or "Goa"
            night_map = {
                "goa": "• **Top Clubs:** Tito's Lane (Baga), Club Cubana (Arpora hilltop), and Hammerzz Luxury Club.\n• **Beach Lounges & Sunsets:** Curlies & Shiva Valley (Anjuna), Thalassa (Siolim), and Cafe Mambo.\n• **Silent Parties:** Silent Noise Club at Palolem Beach (South Goa) with personal headphones.",
                "manali": "• **Old Manali Cafes:** Dylan's Toasted & Roasted, Cafe 1947 (live acoustic riverside gigs).\n• **Breweries:** The Lazy Dog and Johnson's Bar & Restaurant with fireside cocktails.",
                "udaipur": "• **Rooftop Lake Lounges:** Upre by 1559 AD and Charcoal by Carlsson overlooking illuminated Lake Pichola.\n• **Cultural Shows:** Bagore Ki Haveli Dharohar folk dance show (7:00 PM – 8:00 PM).",
                "agra": "• **Taj Mahotsav:** Cultural folk performances in February.\n• **Light & Sound Show:** Spectacular historical show at Agra Fort.\n• **Mughlai Rooftops:** Salt Cafe and Molecule Air Bar overlooking Taj silhouette.",
                "varanasi": "• **Subah & Sandhya Aarti:** Evening Ganga Aarti at Dashashwamedh Ghat.\n• **Classical Music:** Baithak evening concerts and sitar recitals near Assi Ghat.\n• **Rooftop Ghat Cafes:** Brown Bread Bakery and Dolphin Rooftop overlooking illuminated river.",
                "darjeeling": "• **Acoustic Pubs:** Joey's Pub (historic colonial tavern) and Glenary's Restaurant & Pub.\n• **Glenary's Bakery:** Evening live acoustic band, hot coffee, and pastries.\n• **Mall Square:** Evening street performers and bonfire cafes."
            }
            night = night_map.get(destination.lower(), "• Rooftop sunset cafes, cultural evening dance shows, and lively local night markets.")
            reply_text = (
                f"🎉 **Nightlife & Evening Entertainment in {destination}:**\n\n"
                f"{night}\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• Would you like me to include evening club passes and candlelight rooftop dinner reservations in your plan?"
            )
            quick_replies = [
                "Add nightlife passes",
                f"Top cafes in {destination}",
                f"Plan 3 days in {destination}",
                "Safety tips at night"
            ]

        elif intent == "family_and_kids":
            destination = session.get("destination") or "Kerala"
            reply_text = (
                f"👨‍👩‍👧‍👦 **Family & Child-Friendly Travel Guide for {destination}:**\n\n"
                f"• **Suitability:** Highly suitable for families with kids and senior citizens.\n"
                f"• **Accommodations:** Look for family resort suites with lawn access, kid-friendly swimming pools, and dedicated play areas.\n"
                f"• **Activity Pacing:** We recommend max 2 attractions per day with a 2-hour afternoon rest window to avoid fatigue.\n"
                f"• **Food:** Most family resorts and verified restaurants easily provide mild, non-spicy kid meals upon request.\n\n"
                f"💬 **Quick Question for You:**\n"
                f"• What are the age groups in your travel group? I can customize the day schedules with relaxed pacing and elevator-accessible sights."
            )
            quick_replies = [
                "Traveling with kids",
                "Traveling with elderly parents",
                f"Plan family trip to {destination}",
                "Best family hotels in " + destination
            ]

        else:
            reply_text = (
                f"I'm here to help you plan an unforgettable trip to {session.get('destination', 'your favorite destination')}!\n\n"
                f"💬 **What would you like to explore?**\n"
                f"• Tell me your dream destination, budget, or preferred travel style (e.g. adventure, beaches, heritage, relaxation).\n"
                f"• You can also ask me about **Packing tips**, **Travel safety**, **How to reach**, **Photo spots**, or **Shopping**!"
            )
            quick_replies = ["Plan a trip", "Explore destinations", "Estimate budget", "Confirm booking"]

        return {
            "reply": reply_text,
            "itinerary": itinerary,
            "booking_confirmation": booking_confirmation,
            "suggested_destinations": suggested_destinations,
            "quick_replies": quick_replies,
            "session_state": self._get_session_state_dict(session)
        }
