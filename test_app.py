import unittest
import json
from chatbot.pipeline import NLPTravelBot
from app import app


class TestTripWiseNLP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = NLPTravelBot()
        cls.client = app.test_client()

    def test_01_preprocessing_and_trace(self):
        query = "Plan a 3-day trip to Goa under ₹15,000 for 2 people"
        trace = self.bot.process_query(query, session_id="test_prep")["nlp_trace"]
        self.assertIn("goa", trace["cleaned_text"])
        self.assertTrue(trace["token_count"] > 4)
        self.assertIn("15000", trace["filtered_tokens"])

    def test_02_intent_classification(self):
        res1 = self.bot.process_query("Plan a 4-day trip to Manali for 2 people with 20000 budget", session_id="test_intent_1")
        self.assertEqual(res1["nlp_trace"]["intent"], "plan_trip")

        res2 = self.bot.process_query("Remove beaches and add historical spots", session_id="test_intent_2")
        self.assertEqual(res2["nlp_trace"]["intent"], "modify_itinerary")

        res3 = self.bot.process_query("What is the weather like in Manali right now?", session_id="test_intent_3")
        self.assertEqual(res3["nlp_trace"]["intent"], "weather_query")

        res4 = self.bot.process_query("Suggest places to travel under 20000", session_id="test_intent_4")
        self.assertEqual(res4["nlp_trace"]["intent"], "find_destination")

        # New Q&A Intents
        res_pack = self.bot.process_query("What should I pack for Manali in winter?", session_id="test_qa_pack")
        self.assertEqual(res_pack["nlp_trace"]["intent"], "packing_tips")
        self.assertIn("Quick Question", res_pack["reply"])

        res_safe = self.bot.process_query("Is it safe for solo female travelers in Goa?", session_id="test_qa_safe")
        self.assertEqual(res_safe["nlp_trace"]["intent"], "safety_guidelines")
        self.assertIn("Quick Question", res_safe["reply"])

        res_trans = self.bot.process_query("How to reach Manali from Delhi by Volvo bus?", session_id="test_qa_trans")
        self.assertEqual(res_trans["nlp_trace"]["intent"], "transport_query")
        self.assertIn("Quick Question", res_trans["reply"])

        res_photo = self.bot.process_query("Best photography and Instagram spots in Jaipur", session_id="test_qa_photo")
        self.assertEqual(res_photo["nlp_trace"]["intent"], "photography_spots")

        res_shop = self.bot.process_query("What are the best shopping markets and bazaars in Jaipur?", session_id="test_qa_shop")
        self.assertEqual(res_shop["nlp_trace"]["intent"], "shopping_query")

        res_night = self.bot.process_query("What is the nightlife like in Goa? Best beach clubs and shacks", session_id="test_qa_night")
        self.assertEqual(res_night["nlp_trace"]["intent"], "nightlife_query")

        res_fam = self.bot.process_query("Is Kerala good for a family trip with small kids and seniors?", session_id="test_qa_fam")
        self.assertEqual(res_fam["nlp_trace"]["intent"], "family_and_kids")

    def test_03_entity_extraction(self):
        query = "I want to plan a 4-day trip to Manali for 2 people. My budget is ₹20,000. I like adventure and nature."
        entities = self.bot.entity_extractor.extract_all(query)
        self.assertEqual(entities["destination"], "Manali")
        self.assertEqual(entities["duration"], 4)
        self.assertEqual(entities["budget"], 20000)
        self.assertEqual(entities["travelers"], 2)
        self.assertIn("adventure", entities["interests"])
        self.assertIn("nature", entities["interests"])

        # Test new destinations: Agra, Varanasi, Darjeeling
        ent_agra = self.bot.entity_extractor.extract_all("Plan a 2-day heritage tour to Agra to see the Taj Mahal under 10000")
        self.assertEqual(ent_agra["destination"], "Agra")
        self.assertEqual(ent_agra["duration"], 2)

        ent_var = self.bot.entity_extractor.extract_all("I want to visit Varanasi for 3 days with budget 12k")
        self.assertEqual(ent_var["destination"], "Varanasi")
        self.assertEqual(ent_var["duration"], 3)

        ent_darj = self.bot.entity_extractor.extract_all("Plan a 4-day trip to Darjeeling with tea gardens")
        self.assertEqual(ent_darj["destination"], "Darjeeling")
        self.assertEqual(ent_darj["duration"], 4)

    def test_04_itinerary_generation_and_budget(self):
        itin = self.bot.recommender.generate_itinerary(
            destination_name="Goa",
            duration=3,
            budget=15000,
            travelers=2,
            interests=["beach", "nightlife"]
        )
        self.assertEqual(itin["destination"], "Goa")
        self.assertEqual(itin["duration"], 3)
        self.assertEqual(len(itin["itinerary_days"]), 3)
        self.assertIn("total_estimated", itin["cost_breakdown"])
        self.assertTrue(itin["cost_breakdown"]["total_estimated"] > 0)

        # Test new destination itinerary: Varanasi
        itin_var = self.bot.recommender.generate_itinerary(
            destination_name="Varanasi",
            duration=3,
            budget=12000,
            travelers=2,
            interests=["spirituality", "culture"]
        )
        self.assertEqual(itin_var["destination"], "Varanasi")
        self.assertEqual(len(itin_var["itinerary_days"]), 3)

    def test_05_multi_turn_conversational_flow(self):
        sess = "test_conversation_turns"
        
        # Turn 1: Greeting
        t1 = self.bot.process_query("Hi", session_id=sess)
        self.assertEqual(t1["nlp_trace"]["intent"], "greeting")
        self.assertIn("Where would you like to travel", t1["reply"])
        
        # Turn 2: Destination
        t2 = self.bot.process_query("I want to visit Goa.", session_id=sess)
        self.assertEqual(t2["session_state"]["destination"], "Goa")
        self.assertIn("How many days are you planning to stay", t2["reply"])
        
        # Turn 3: Duration
        t3 = self.bot.process_query("4 days.", session_id=sess)
        self.assertEqual(t3["session_state"]["duration"], 4)
        self.assertIn("approximate budget", t3["reply"])
        
        # Turn 4: Budget
        t4 = self.bot.process_query("Around ₹15,000.", session_id=sess)
        self.assertEqual(t4["session_state"]["budget"], 15000)
        self.assertIn("Who are you travelling with", t4["reply"])
        
        # Turn 5: Companions
        t5 = self.bot.process_query("With my friends.", session_id=sess)
        self.assertEqual(t5["session_state"]["travel_with"], "Friends")
        self.assertIn("What type of activities do you prefer", t5["reply"])
        
        # Turn 6: Interests
        t6 = self.bot.process_query("Beaches and nightlife.", session_id=sess)
        self.assertIn("beach", t6["session_state"]["interests"])
        self.assertIn("nightlife", t6["session_state"]["interests"])
        self.assertIn("plan to travel", t6["reply"])
        
        # Turn 7: Transport
        t7 = self.bot.process_query("Train.", session_id=sess)
        self.assertEqual(t7["session_state"]["transport"], "Train")
        self.assertIn("accommodation do you prefer", t7["reply"])
        
        # Turn 8: Accommodation -> All 7 slots filled, generates Plan!
        t8 = self.bot.process_query("Budget hotel.", session_id=sess)
        self.assertEqual(t8["session_state"]["accommodation"], "Budget Hotel")
        self.assertIsNotNone(t8["itinerary"])
        self.assertIn("Awesome! Here is your custom travel plan:", t8["reply"])
        self.assertIn("| Day | Plan |", t8["reply"])
        self.assertIn("Trip Details:", t8["reply"])

        # Turn 9: Memory Recall - Budget
        t9 = self.bot.process_query("What was my budget?", session_id=sess)
        self.assertIn("15,000", t9["reply"])

        # Turn 10: Memory Recall - Destination
        t10 = self.bot.process_query("Where am I going?", session_id=sess)
        self.assertIn("Goa", t10["reply"])

        # Turn 11: Budget Feasibility Inquiry
        t11 = self.bot.process_query("Can I do this trip under ₹10,000?", session_id=sess)
        self.assertEqual(t11["nlp_trace"]["intent"], "budget_calculation")
        self.assertIn("TripWise Optimization Suggestions", t11["reply"])

        # Turn 12: Modification - Duration change
        t12 = self.bot.process_query("Change my trip to 5 days.", session_id=sess)
        self.assertEqual(t12["session_state"]["duration"], 5)
        self.assertIn("Day 5", t12["reply"])

    def test_06_flask_api_endpoints(self):
        # Test GET /
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"TripWise", resp.data)

        # Test GET /api/destinations
        resp_dest = self.client.get("/api/destinations")
        self.assertEqual(resp_dest.status_code, 200)
        data_dest = json.loads(resp_dest.data)
        self.assertTrue(len(data_dest["destinations"]) >= 5)

        # Test POST /api/chat with full 7-slot query
        payload = {
            "message": "Plan a 3-day trip to Goa under 15000 with friends for beaches by train in budget hotel",
            "session_id": "api_test"
        }
        resp_chat = self.client.post("/api/chat",
                                     data=json.dumps(payload),
                                     content_type="application/json")
        self.assertEqual(resp_chat.status_code, 200)
        chat_data = json.loads(resp_chat.data)
        self.assertIn("reply", chat_data)
        self.assertIsNotNone(chat_data["itinerary"])

        # Test POST /api/reset
        resp_reset = self.client.post("/api/reset",
                                      data=json.dumps({"session_id": "api_test"}),
                                      content_type="application/json")
        self.assertEqual(resp_reset.status_code, 200)

    def test_07_booking_confirmation_and_invoice_pdf(self):
        # 1. Test chat intent recognition for confirm_booking
        res = self.bot.process_query("Confirm booking for this trip and download invoice", session_id="test_book")
        self.assertEqual(res["nlp_trace"]["intent"], "confirm_booking")
        self.assertIsNotNone(res.get("booking_confirmation"))
        self.assertEqual(res["booking_confirmation"]["status"], "CONFIRMED")

        # 2. Test POST /api/confirm_booking endpoint
        resp = self.client.post("/api/confirm_booking",
                                data=json.dumps({"session_id": "test_book", "customer_name": "Ronald", "destination": "Goa"}),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        book_data = json.loads(resp.data)
        self.assertEqual(book_data["status"], "success")
        self.assertIn("booking_id", book_data["booking"])

        # 3. Test GET /api/download_invoice PDF endpoint
        booking_id = book_data["booking"]["booking_id"]
        resp_pdf = self.client.get(f"/api/download_invoice?booking_id={booking_id}&session_id=test_book")
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf.content_type, "application/pdf")
        self.assertTrue(len(resp_pdf.data) > 1000)
        # Verify PDF magic bytes '%PDF'
        self.assertTrue(resp_pdf.data.startswith(b"%PDF"))

    def test_08_unavailable_location_handling(self):
        # 1. Direct unavailable location statement
        res_mumbai = self.bot.process_query("I want to visit Mumbai.", session_id="test_unavail_1")
        self.assertEqual(res_mumbai["nlp_trace"]["extracted_entities"]["unavailable_destination"], "Mumbai")
        self.assertIn("Location Not Available: Mumbai", res_mumbai["reply"])
        self.assertIn("currently not available", res_mumbai["reply"])
        self.assertIn("Currently Available Destinations", res_mumbai["reply"])
        self.assertIn("Goa", res_mumbai["reply"])
        self.assertIn("Manali", res_mumbai["reply"])
        self.assertIsNone(res_mumbai["session_state"]["destination"])

        # 2. International unavailable location
        res_paris = self.bot.process_query("Plan a trip to Paris.", session_id="test_unavail_2")
        self.assertEqual(res_paris["nlp_trace"]["extracted_entities"]["unavailable_destination"], "Paris")
        self.assertIn("Location Not Available: Paris", res_paris["reply"])

        # 3. Conversational query for Pune
        res_pune = self.bot.process_query("Can we go to Pune?", session_id="test_unavail_3")
        self.assertEqual(res_pune["nlp_trace"]["extracted_entities"]["unavailable_destination"], "Pune")
        self.assertIn("Location Not Available: Pune", res_pune["reply"])

        # 4. Weather check for unavailable location (does NOT fall back to Goa/Manali)
        res_delhi = self.bot.process_query("What is the weather in Delhi?", session_id="test_unavail_4")
        self.assertEqual(res_delhi["nlp_trace"]["extracted_entities"]["unavailable_destination"], "Delhi")
        self.assertIn("Location Not Available: Delhi", res_delhi["reply"])

        # 5. Standalone unavailable destination word
        res_shimla = self.bot.process_query("Shimla", session_id="test_unavail_5")
        self.assertEqual(res_shimla["nlp_trace"]["extracted_entities"]["unavailable_destination"], "Shimla")
        self.assertIn("Location Not Available: Shimla", res_shimla["reply"])

        # 6. Available destination query works normally
        res_goa = self.bot.process_query("I want to visit Goa.", session_id="test_avail_goa")
        self.assertIsNone(res_goa["nlp_trace"]["extracted_entities"]["unavailable_destination"])
        self.assertEqual(res_goa["session_state"]["destination"], "Goa")
        self.assertIn("Goa is a wonderful choice", res_goa["reply"])

        # 7. Ask for available destinations
        res_avail_list = self.bot.process_query("What destinations are available?", session_id="test_avail_list")
        self.assertIn("TripWise Currently Available Destinations:", res_avail_list["reply"])

    def test_09_activity_based_recommendation(self):
        # 1. "I want to go river rafting" -> Expected: river_rafting
        res1 = self.bot.process_query("I want to go river rafting", session_id="test_act_1")
        self.assertEqual(res1["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "river_rafting")
        self.assertIn("River Rafting Destinations", res1["reply"])
        self.assertIn("Rishikesh", res1["reply"])
        self.assertIn("Kolad", res1["reply"])

        # 2. "Suggest a place for trekking" -> Expected: trekking
        res2 = self.bot.process_query("Suggest a place for trekking", session_id="test_act_2")
        self.assertEqual(res2["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "trekking")
        self.assertIn("Trekking & Hiking Destinations", res2["reply"])
        self.assertIn("Manali", res2["reply"])

        # 3. "Where can I go scuba diving?" -> Expected: scuba_diving
        res3 = self.bot.process_query("Where can I go scuba diving?", session_id="test_act_3")
        self.assertEqual(res3["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "scuba_diving")
        self.assertIn("Scuba Diving Destinations", res3["reply"])
        self.assertIn("Goa", res3["reply"])

        # 4. "I want to try paragliding" -> Expected: paragliding
        res4 = self.bot.process_query("I want to try paragliding", session_id="test_act_4")
        self.assertEqual(res4["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "paragliding")
        self.assertIn("Paragliding Destinations", res4["reply"])
        self.assertIn("Bir Billing", res4["reply"])

        # 5. "Best places for skiing" -> Expected: skiing
        res5 = self.bot.process_query("Best places for skiing", session_id="test_act_5")
        self.assertEqual(res5["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "skiing")
        self.assertIn("Skiing & Snowboarding Destinations", res5["reply"])
        self.assertIn("Gulmarg", res5["reply"])

        # 6. "I have 2 days for rafting" -> Expected: river_rafting, duration = 2
        res6 = self.bot.process_query("I have 2 days for rafting", session_id="test_act_6")
        self.assertEqual(res6["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "river_rafting")
        self.assertEqual(res6["nlp_trace"]["extracted_entities"]["duration"], 2)
        self.assertIn("2 Days", res6["reply"])

        # 7. "Suggest rafting near Mumbai" -> Expected: river_rafting, origin = Mumbai
        res7 = self.bot.process_query("Suggest rafting near Mumbai", session_id="test_act_7")
        self.assertEqual(res7["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "river_rafting")
        self.assertEqual(res7["nlp_trace"]["extracted_entities"]["origin_city"], "Mumbai")
        self.assertIn("Near", res7["reply"])
        self.assertIn("Mumbai", res7["reply"])
        self.assertIn("Kolad", res7["reply"])

        # 8. Follow-up: "I want to go rafting" -> "Which is cheaper?"
        self.bot.process_query("I want to go rafting", session_id="test_act_followup")
        res8 = self.bot.process_query("Which is cheaper?", session_id="test_act_followup")
        self.assertEqual(res8["session_state"]["last_activity"], "river_rafting")
        self.assertIn("Sorted by Lowest Cost", res8["reply"])
        self.assertIn("Kolad", res8["reply"])

        # 9. Fallback: "I want to try canyoning"
        res9 = self.bot.process_query("I want to try canyoning", session_id="test_act_unsupp")
        self.assertTrue(res9["nlp_trace"]["extracted_entities"]["activity_data"]["is_unsupported"])
        self.assertIn("I understand that you're interested in canyoning", res9["reply"])
        self.assertIn("River Rafting", res9["quick_replies"])

        # 10. Broad activity query: "I am interested in adventure"
        res10 = self.bot.process_query("I am interested in adventure", session_id="test_act_10")
        self.assertEqual(res10["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "adventure_sports")
        self.assertIn("Adventure Sports Destinations", res10["reply"])
        self.assertIn("Rishikesh", res10["reply"])

        # 11. Broad activity query: "I like nature and mountains"
        res11 = self.bot.process_query("I like nature and mountains", session_id="test_act_11")
        self.assertEqual(res11["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "nature_and_mountains")
        self.assertIn("Nature & Mountains Destinations", res11["reply"])
        self.assertIn("Manali", res11["reply"])

        # 12. Broad activity query: "I want relaxation"
        res12 = self.bot.process_query("I want relaxation", session_id="test_act_12")
        self.assertEqual(res12["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "relaxation_and_wellness")
        self.assertIn("Relaxation & Wellness Destinations", res12["reply"])
        self.assertIn("Kerala", res12["reply"])

    def test_10_broken_english_and_slang_understanding(self):
        # 1. Phonetic destination typo & abbreviation: "i wnt go goaa 4 dys"
        res1 = self.bot.process_query("i wnt go goaa 4 dys", session_id="test_brk_1")
        self.assertEqual(res1["nlp_trace"]["extracted_entities"]["destination"], "Goa")
        self.assertEqual(res1["nlp_trace"]["extracted_entities"]["duration"], 4)
        self.assertIn("Goa is a wonderful choice", res1["reply"])

        # 2. Slang & typo: "pln trip to manli for 3 d"
        res2 = self.bot.process_query("pln trip to manli for 3 d", session_id="test_brk_2")
        self.assertEqual(res2["nlp_trace"]["extracted_entities"]["destination"], "Manali")
        self.assertEqual(res2["nlp_trace"]["extracted_entities"]["duration"], 3)

        # 3. Hindi unit & companions: "kerla 5 dys wid frnds"
        res3 = self.bot.process_query("kerla 5 dys wid frnds", session_id="test_brk_3")
        self.assertEqual(res3["nlp_trace"]["extracted_entities"]["destination"], "Kerala")
        self.assertEqual(res3["nlp_trace"]["extracted_entities"]["duration"], 5)
        self.assertEqual(res3["nlp_trace"]["extracted_entities"]["travel_with"], "Friends")

        # 4. Budget with 'k' notation & abbreviation: "bgdt 15k"
        res4 = self.bot.process_query("bgdt 15k", session_id="test_brk_4")
        self.assertEqual(res4["nlp_trace"]["extracted_entities"]["budget"], 15000)

        # 5. Budget with 'hazar': "around 15 hazar"
        res5 = self.bot.process_query("around 15 hazar", session_id="test_brk_5")
        self.assertEqual(res5["nlp_trace"]["extracted_entities"]["budget"], 15000)

        # 6. Companion abbreviation: "wid famly"
        res6 = self.bot.process_query("wid famly", session_id="test_brk_6")
        self.assertEqual(res6["nlp_trace"]["extracted_entities"]["travel_with"], "Family")
        self.assertIsNone(res6["nlp_trace"]["extracted_entities"]["unavailable_destination"])

        # 7. Transport broken slang: "trn se travel"
        res7 = self.bot.process_query("trn se travel", session_id="test_brk_7")
        self.assertEqual(res7["nlp_trace"]["extracted_entities"]["transport"], "Train")

        # 8. Accommodation broken slang: "chp hotel"
        res8 = self.bot.process_query("chp hotel", session_id="test_brk_8")
        self.assertEqual(res8["nlp_trace"]["extracted_entities"]["accommodation"], "Budget Hotel")

        # 9. Broken activity & proximity: "river rfting near mumbai"
        res9 = self.bot.process_query("river rfting near mumbai", session_id="test_brk_9")
        self.assertEqual(res9["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "river_rafting")
        self.assertEqual(res9["nlp_trace"]["extracted_entities"]["origin_city"], "Mumbai")
        self.assertIn("River Rafting Destinations", res9["reply"])
        self.assertIn("Kolad", res9["reply"])

        # 10. Scuba diving typo: "scba dving"
        res10 = self.bot.process_query("scba dving", session_id="test_brk_10")
        self.assertEqual(res10["nlp_trace"]["extracted_entities"]["activity_data"]["activity"], "scuba_diving")
        self.assertIn("Scuba Diving Destinations", res10["reply"])

        # 11. Broken memory queries: "wat is my bdgt" & "whr am i going"
        res11a = self.bot.process_query("wat is my bdgt", session_id="test_brk_mem")
        self.assertEqual(res11a["nlp_trace"]["extracted_entities"]["memory_query"], "budget")
        res11b = self.bot.process_query("whr am i going", session_id="test_brk_mem")
        self.assertEqual(res11b["nlp_trace"]["extracted_entities"]["memory_query"], "destination")

        # 12. Full conversational planning in broken English
        sid = "test_broken_full_convo"
        self.bot.process_query("hiii", session_id=sid)
        self.bot.process_query("goaa", session_id=sid)
        self.bot.process_query("4 dys", session_id=sid)
        self.bot.process_query("15k", session_id=sid)
        self.bot.process_query("wid frnds", session_id=sid)
        self.bot.process_query("trn", session_id=sid)
        self.bot.process_query("chp hotel", session_id=sid)
        res_final = self.bot.process_query("bch and nightlife", session_id=sid)
        self.assertTrue(res_final["session_state"]["itinerary_generated"])
        self.assertEqual(res_final["session_state"]["destination"], "Goa")
        self.assertEqual(res_final["session_state"]["duration"], 4)
        self.assertEqual(res_final["session_state"]["budget"], 15000)
        self.assertEqual(res_final["session_state"]["travel_with"], "Friends")
        self.assertEqual(res_final["session_state"]["transport"], "Train")
        self.assertEqual(res_final["session_state"]["accommodation"], "Budget Hotel")
        self.assertIn("Day 1", res_final["reply"])
        self.assertIsNotNone(res_final["itinerary"])


if __name__ == "__main__":
    unittest.main()
