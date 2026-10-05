# ✈️ TripWise: AI Travel Planner NLP Chatbot

An intelligent, interactive **NLP-based Travel Planning Chatbot** designed as an academic mini-project. It processes natural language requests from users, extracts key travel constraints using classical NLP techniques, classifies user intents with machine learning, and dynamically generates personalized multi-day itineraries and budget estimates with full conversational context adaptation.

---

## 🌟 Key Features

1. **Natural-Language Trip Planning**:
   - Accepts free-form input like: *"Plan a 4-day trip to Manali for 2 people under ₹20,000. I love adventure and nature."*
2. **Context-Aware Dynamic Modifications**:
   - Supports follow-up modifications like: *"Remove beaches and add historical spots"* or *"Increase budget to 25k"* without re-asking for destination or duration.
3. **ML Intent Classification (TF-IDF + Logistic Regression)**:
   - Trained across 11 travel intents (`plan_trip`, `modify_itinerary`, `recommend_places`, `find_destination`, `budget_estimate`, `hotel_recommendation`, `food_recommendation`, `weather_query`, `greeting`, `goodbye`, `help`).
4. **Custom Entity & Slot Extraction (NER)**:
   - Extracts:
     - 📍 **Destination** (Goa, Manali, Kerala, Jaipur, Ladakh, Rishikesh, Ooty, Udaipur)
     - 📅 **Duration** ("3 days", "a weekend", "5 nights")
     - 💰 **Budget** ("₹15,000", "under 20k", "25000 inr")
     - 👥 **Travelers** ("solo", "couple", "2 people", "family of 4")
     - 🎯 **Interests** (beach, adventure, nature, heritage, nightlife, food, relaxation)
     - 🚫 **Exclusions / Removals** ("remove beaches", "no trekking")
5. **Intelligent Recommendation Engine**:
   - Schedules attractions into Morning, Afternoon, and Evening slots.
   - Calculates comprehensive expense breakdowns: **Activities + Accommodation + Food & Dining + Local Transit**.
   - Adapts to budget tiers (Backpacker / Moderate / Luxury).
6. **Live Academic NLP Inspector GUI**:
   - A dedicated right-hand sidebar showing:
     - Preprocessed tokens and removed stopwords.
     - Detected intent with real-time confidence percentage bar.
     - Top TF-IDF weighted terms for the input query.
     - Structured JSON representation of extracted entity slots.
7. **Zero Paid API Dependencies**:
   - Fully local, offline-capable, and deterministic — perfect for college lab demonstrations and viva presentations.

---

## 🏗️ System Architecture & NLP Pipeline

```text
 User Input: "Plan a 4-day trip to Manali for 2 people under ₹20,000 with adventure"
                                ↓
                 1. Text Preprocessing & Cleaning
       (Lowercasing, Contraction Expansion, Number Normalization)
                                ↓
                 2. Tokenization & Stopword Filtering
                    (Travel-sensitive stopword set)
                                ↓
              ┌─────────────────┴─────────────────┐
              ↓                                   ↓
   3. Intent Classification            4. Entity Extraction
  (TF-IDF N-grams + Logistic Reg)    (Regex Patterns & Gazetteer)
  • Intent: `plan_trip` (96%)        • Destination: Manali
                                     • Duration: 4 days
                                     • Budget: ₹20,000
                                     • Travelers: 2
                                     • Interests: ['adventure']
              └─────────────────┬─────────────────┘
                                ↓
                 5. Context & Session State Manager
                 (Slot-filling & Multi-turn updates)
                                ↓
                 6. Travel Recommendation Engine
               (Place Scoring, Slotting & Budgeting)
                                ↓
                 7. Response & Itinerary Synthesis
                                ↓
            3-Column Interactive Web GUI (Flask + HTML/CSS/JS)
```

---

## 📁 Project Structure

```text
TripWise/
│
├── app.py                     # Flask web server & REST API endpoints
├── train.py                   # NLP model training & evaluation script
├── test_app.py                # Automated unit & integration tests
├── requirements.txt           # Project dependencies
│
├── chatbot/
│   ├── __init__.py
│   ├── preprocessing.py       # Cleaning, contractions, tokenization, stop-words
│   ├── intent_classifier.py   # TF-IDF + Logistic Regression inference
│   ├── entity_extractor.py    # Rule-based entity & slot extractor
│   ├── recommendation.py      # Place scoring, itinerary generator & budgeter
│   ├── context_manager.py     # Conversation session memory & slot tracking
│   ├── response_generator.py  # Conversational text & payload generator
│   └── pipeline.py            # Master pipeline coordinator
│
├── model/
│   ├── intent_model.pkl       # Trained Logistic Regression model
│   └── vectorizer.pkl         # Fitted TF-IDF Vectorizer
│
├── data/
│   ├── intents.json           # Intent dataset with 140+ examples
│   ├── destinations.json      # Destination profiles, weather & costs
│   └── places.json            # 40+ categorized attractions
│
├── templates/
│   └── index.html             # 3-column dashboard UI
│
└── static/
    ├── css/
    │   └── style.css          # Modern dark-mode responsive styling
    └── js/
        └── script.js          # Dynamic chat, day tabs, NLP inspector & export
```

---

## 🚀 How to Run the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Retrain Intent Classifier
```bash
python train.py
```
This evaluates cross-validation accuracy and exports the model artifacts into `model/`.

### 3. Run Automated Tests
```bash
python test_app.py
```

### 4. Start the Application
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🎓 Viva & Demonstration Script

Use these exact queries during your project viva to impress evaluators:

| Query | What it Demonstrates |
| :--- | :--- |
| **"Plan a 3-day trip to Goa under ₹15,000 for 2 people with beaches and nightlife"** | Full NLP pipeline: Entity extraction (4 slots), Intent classification (`plan_trip`), and complete Day 1–3 itinerary card. |
| **"Remove beaches and add historical spots"** | Context memory: Itinerary updates dynamically by replacing beach spots with Fort Aguada / Basilica without losing destination or budget. |
| **"Increase budget to 25k"** | Slot update: Modifies budget slot, recalculates room/food tiers, and updates budget difference pill. |
| **"What is the weather in Manali?"** | Intent classification: Detects `weather_query` intent and returns climate and packing guidance. |
| **"Suggest places for a couple under ₹20,000"** | Recommendation engine: Scans destination profiles and suggests top budget-matching destinations. |

Click the **NLP Inspector** tab on the top-right of the web page to show examiners the live internal preprocessed tokens, TF-IDF weights, confidence percentages, and JSON entity payloads!
