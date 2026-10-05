import os
from flask import Flask, render_template, request, jsonify
from chatbot.pipeline import NLPTravelBot

app = Flask(__name__)
bot = NLPTravelBot()


@app.route("/")
def index():
    destinations = bot.recommender.get_all_destinations()
    return render_template("index.html", destinations=destinations)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default_session")

    if not user_message:
        return jsonify({"error": "Empty message received."}), 400

    try:
        result = bot.process_query(user_message, session_id=session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "reply": f"Sorry, an unexpected error occurred while processing your request: {str(e)}",
            "error": str(e),
            "itinerary": None,
            "session_state": {},
            "nlp_trace": {
                "raw_query": user_message,
                "error": str(e)
            }
        }), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json() or {}
    session_id = data.get("session_id", "default_session")
    bot.reset_session(session_id)
    return jsonify({"status": "success", "message": "Conversation session reset successfully."})


@app.route("/api/destinations", methods=["GET"])
def get_destinations():
    destinations = bot.recommender.get_all_destinations()
    return jsonify({"destinations": destinations})


@app.route("/api/sample_queries", methods=["GET"])
def sample_queries():
    samples = [
        {
            "category": "Full Planning",
            "query": "Plan a 3-day trip to Goa under ₹15,000 for 2 people with beaches and nightlife"
        },
        {
            "category": "Adventure & Mountains",
            "query": "I want to plan a 4-day trip to Manali for 2 people with ₹20,000 budget. I like adventure and nature."
        },
        {
            "category": "Relaxing Vacation",
            "query": "Plan a 5 day trip to Kerala under 25k for me. I love nature and food."
        },
        {
            "category": "Royal Heritage",
            "query": "Plan a 3-day tour to Jaipur for 2 people with budget 12000"
        },
        {
            "category": "Modification",
            "query": "Remove beaches and add historical spots"
        },
        {
            "category": "Budget Discovery",
            "query": "Suggest places for a couple under ₹20,000"
        },
        {
            "category": "Weather Check",
            "query": "What is the weather and best time to visit Ladakh?"
        }
    ]
    return jsonify({"samples": samples})


@app.route("/api/confirm_booking", methods=["POST"])
def confirm_booking_endpoint():
    data = request.get_json() or {}
    session_id = data.get("session_id", "default_session")
    customer_name = data.get("customer_name", "Ronald").strip() or "Ronald"

    session = bot.context_manager.get_session(session_id)
    dest = session.get("destination") or data.get("destination") or "Goa"
    duration = session.get("duration") or data.get("duration") or 3
    travelers = session.get("travelers") or data.get("travelers") or 1
    budget = session.get("budget")

    itinerary = session.get("current_itinerary")
    if not itinerary:
        itinerary = bot.recommender.generate_itinerary(
            destination_name=dest,
            duration=duration,
            budget=budget,
            travelers=travelers
        )
        session["current_itinerary"] = itinerary

    booking_id = itinerary.get("booking_id", f"TW-2026-{dest[:3].upper()}-9912")
    start_date = itinerary.get("start_date")
    end_date = itinerary.get("end_date")
    cost_breakdown = itinerary.get("cost_breakdown", {})
    total_amount = cost_breakdown.get("total_estimated", 15000)

    booking_data = {
        "booking_id": booking_id,
        "customer_name": customer_name,
        "destination": dest,
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

    return jsonify({
        "status": "success",
        "message": f"Trip for {dest} confirmed successfully!",
        "booking": booking_data
    })


@app.route("/api/download_invoice", methods=["GET"])
def download_invoice():
    from flask import Response
    from chatbot.invoice_generator import generate_invoice_pdf

    session_id = request.args.get("session_id", "default_session")
    booking_id = request.args.get("booking_id")
    customer_name = request.args.get("name", "Ronald")

    session = bot.context_manager.get_session(session_id)
    booking_data = session.get("booking_data")

    # If booking_data is not in session, try to reconstruct from current itinerary or defaults
    if not booking_data:
        itin = session.get("current_itinerary")
        dest = session.get("destination") or "Goa"
        duration = session.get("duration") or 3
        travelers = session.get("travelers") or 1
        if not itin:
            itin = bot.recommender.generate_itinerary(dest, duration=duration, travelers=travelers)
            session["current_itinerary"] = itin

        booking_id = booking_id or itin.get("booking_id", f"TW-2026-{dest[:3].upper()}-7821")
        booking_data = {
            "booking_id": booking_id,
            "customer_name": customer_name,
            "destination": dest,
            "duration": duration,
            "travelers": travelers,
            "start_date": itin.get("start_date"),
            "end_date": itin.get("end_date"),
            "cost_breakdown": itin.get("cost_breakdown", {}),
            "itinerary_days": itin.get("itinerary_days", []),
            "total_amount": itin.get("cost_breakdown", {}).get("total_estimated", 15000),
            "status": "CONFIRMED"
        }

    try:
        pdf_content = generate_invoice_pdf(booking_data)
        b_id = booking_data.get("booking_id", "TW-INVOICE")
        filename = f"TripWise_Invoice_{b_id}.pdf"
        return Response(
            pdf_content,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate invoice PDF: {str(e)}"}), 500


if __name__ == "__main__":
    # Ensure model exists
    bot.intent_classifier.load_model()
    print("TripWise NLP Travel Planner running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
