import re
import difflib
from typing import Dict, Any, List, Optional
from chatbot.preprocessing import normalize_broken_english, SLANG_AND_TYPO_MAP

DESTINATION_MAP = {
    "goa": "Goa",
    "north goa": "Goa",
    "south goa": "Goa",
    "manali": "Manali",
    "old manali": "Manali",
    "solang": "Manali",
    "kerala": "Kerala",
    "munnar": "Kerala",
    "alleppey": "Kerala",
    "alappuzha": "Kerala",
    "kochi": "Kerala",
    "cochin": "Kerala",
    "varkala": "Kerala",
    "wayanad": "Kerala",
    "jaipur": "Jaipur",
    "pink city": "Jaipur",
    "ladakh": "Ladakh",
    "leh": "Ladakh",
    "pangong": "Ladakh",
    "nubra": "Ladakh",
    "zanskar": "Ladakh",
    "rishikesh": "Rishikesh",
    "ooty": "Ooty",
    "nilgiri": "Ooty",
    "udhagamandalam": "Ooty",
    "udaipur": "Udaipur",
    "lake city": "Udaipur",
    "agra": "Agra",
    "taj mahal": "Agra",
    "taj": "Agra",
    "fatehpur": "Agra",
    "varanasi": "Varanasi",
    "banaras": "Varanasi",
    "kashi": "Varanasi",
    "benaras": "Varanasi",
    "darjeeling": "Darjeeling",
    "darjiling": "Darjeeling",
    "kanchenjunga": "Darjeeling",
    "tiger hill": "Darjeeling",

    # Common broken English, typos & phonetic spellings
    "goaa": "Goa",
    "goo": "Goa",
    "manli": "Manali",
    "mnaali": "Manali",
    "mnli": "Manali",
    "kerla": "Kerala",
    "keral": "Kerala",
    "kerela": "Kerala",
    "karala": "Kerala",
    "rishkesh": "Rishikesh",
    "rshikesh": "Rishikesh",
    "rishkes": "Rishikesh",
    "jaipr": "Jaipur",
    "jaypur": "Jaipur",
    "jaipure": "Jaipur",
    "ladak": "Ladakh",
    "ladkh": "Ladakh",
    "ooti": "Ooty",
    "oti": "Ooty",
    "otty": "Ooty",
    "udaipr": "Udaipur",
    "udaipoor": "Udaipur",
    "udaypur": "Udaipur",
    "darjeling": "Darjeeling",
    "darjling": "Darjeeling",
    "varnasi": "Varanasi",
    "varnsi": "Varanasi",
    "aggra": "Agra",
    "agraa": "Agra"
}

SUPPORTED_DESTINATIONS = {
    "Goa", "Manali", "Kerala", "Jaipur", "Ladakh",
    "Rishikesh", "Ooty", "Udaipur", "Agra", "Varanasi", "Darjeeling"
}

KNOWN_UNAVAILABLE_DESTINATIONS = {
    # Major Indian Cities & Metro
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "New Delhi",
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "pune": "Pune",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "surat": "Surat",
    "vadodara": "Vadodara",
    "rajkot": "Rajkot",
    "nagpur": "Nagpur",
    "nashik": "Nashik",
    "aurangabad": "Aurangabad",
    "chhatrapati sambhajinagar": "Aurangabad",
    "kolhapur": "Kolhapur",
    "solapur": "Solapur",
    "thane": "Thane",
    "navi mumbai": "Navi Mumbai",

    # Maharashtra Getaways
    "mahabaleshwar": "Mahabaleshwar",
    "lonavala": "Lonavala",
    "khandala": "Khandala",
    "alibaug": "Alibaug",
    "panchgani": "Panchgani",
    "matheran": "Matheran",
    "shirdi": "Shirdi",
    "lavasa": "Lavasa",
    "igatpuri": "Igatpuri",
    "tarkarli": "Tarkarli",

    # North India & Himalayas
    "shimla": "Shimla",
    "kufri": "Kufri",
    "dharamshala": "Dharamshala",
    "dharamsala": "Dharamshala",
    "mcleodganj": "McLeodGanj",
    "mcleod ganj": "McLeodGanj",
    "dalhousie": "Dalhousie",
    "khajjiar": "Khajjiar",
    "spiti": "Spiti Valley",
    "spiti valley": "Spiti Valley",
    "kasauli": "Kasauli",
    "kasol": "Kasol",
    "tirthan": "Tirthan Valley",
    "jibhi": "Jibhi",
    "kullu": "Kullu",
    "srinagar": "Srinagar",
    "kashmir": "Kashmir",
    "gulmarg": "Gulmarg",
    "pahalgam": "Pahalgam",
    "sonamarg": "Sonamarg",
    "jammu": "Jammu",
    "katra": "Katra",
    "vaishno devi": "Vaishno Devi",
    "amritsar": "Amritsar",
    "chandigarh": "Chandigarh",

    # Uttarakhand
    "dehradun": "Dehradun",
    "mussoorie": "Mussoorie",
    "nainital": "Nainital",
    "corbett": "Jim Corbett",
    "jim corbett": "Jim Corbett",
    "ranikhet": "Ranikhet",
    "almora": "Almora",
    "kausani": "Kausani",
    "lansdowne": "Lansdowne",
    "auli": "Auli",
    "haridwar": "Haridwar",
    "kedarnath": "Kedarnath",
    "badrinath": "Badrinath",
    "gangotri": "Gangotri",
    "yamunotri": "Yamunotri",
    "valley of flowers": "Valley of Flowers",

    # Rajasthan (other than Jaipur & Udaipur)
    "jodhpur": "Jodhpur",
    "jaisalmer": "Jaisalmer",
    "bikaner": "Bikaner",
    "pushkar": "Pushkar",
    "mount abu": "Mount Abu",
    "ajmer": "Ajmer",
    "ranthambore": "Ranthambore",
    "chittorgarh": "Chittorgarh",

    # South India (other than Kerala & Ooty)
    "mysore": "Mysore",
    "mysuru": "Mysore",
    "coorg": "Coorg",
    "madikeri": "Coorg",
    "hampi": "Hampi",
    "gokarna": "Gokarna",
    "chikmagalur": "Chikmagalur",
    "mangalore": "Mangalore",
    "udupi": "Udupi",
    "dandeli": "Dandeli",
    "pondicherry": "Pondicherry",
    "puducherry": "Pondicherry",
    "madurai": "Madurai",
    "rameswaram": "Rameswaram",
    "rameshwaram": "Rameswaram",
    "kanyakumari": "Kanyakumari",
    "mahabalipuram": "Mahabalipuram",
    "kodaikanal": "Kodaikanal",
    "coonoor": "Coonoor",
    "tirupati": "Tirupati",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",

    # Central & East India
    "ayodhya": "Ayodhya",
    "mathura": "Mathura",
    "vrindavan": "Vrindavan",
    "lucknow": "Lucknow",
    "kanpur": "Kanpur",
    "prayagraj": "Prayagraj",
    "allahabad": "Prayagraj",
    "bhopal": "Bhopal",
    "indore": "Indore",
    "ujjain": "Ujjain",
    "gwalior": "Gwalior",
    "khajuraho": "Khajuraho",
    "pachmarhi": "Pachmarhi",
    "bhubaneswar": "Bhubaneswar",
    "puri": "Puri",
    "konark": "Konark",
    "patna": "Patna",
    "bodh gaya": "Bodh Gaya",
    "bodhgaya": "Bodh Gaya",
    "ranchi": "Ranchi",

    # North East & Islands
    "sikkim": "Sikkim",
    "gangtok": "Gangtok",
    "pelling": "Pelling",
    "lachung": "Lachung",
    "shillong": "Shillong",
    "meghalaya": "Meghalaya",
    "cherrapunji": "Cherrapunji",
    "dawki": "Dawki",
    "assam": "Assam",
    "guwahati": "Guwahati",
    "kaziranga": "Kaziranga",
    "tawang": "Tawang",
    "arunachal": "Arunachal Pradesh",
    "andaman": "Andaman & Nicobar",
    "port blair": "Port Blair",
    "havelock": "Havelock Island",
    "lakshadweep": "Lakshadweep",

    # International Tourist Destinations
    "paris": "Paris",
    "france": "France",
    "london": "London",
    "uk": "United Kingdom",
    "england": "England",
    "united kingdom": "United Kingdom",
    "dubai": "Dubai",
    "uae": "UAE",
    "abu dhabi": "Abu Dhabi",
    "singapore": "Singapore",
    "bangkok": "Bangkok",
    "phuket": "Phuket",
    "pattaya": "Pattaya",
    "krabi": "Krabi",
    "thailand": "Thailand",
    "bali": "Bali",
    "indonesia": "Indonesia",
    "tokyo": "Tokyo",
    "kyoto": "Kyoto",
    "japan": "Japan",
    "new york": "New York",
    "nyc": "New York",
    "los angeles": "Los Angeles",
    "las vegas": "Las Vegas",
    "san francisco": "San Francisco",
    "miami": "Miami",
    "chicago": "Chicago",
    "usa": "USA",
    "america": "USA",
    "united states": "USA",
    "hawaii": "Hawaii",
    "honolulu": "Honolulu",
    "switzerland": "Switzerland",
    "zurich": "Zurich",
    "geneva": "Geneva",
    "interlaken": "Interlaken",
    "lucerne": "Lucerne",
    "maldives": "Maldives",
    "rome": "Rome",
    "venice": "Venice",
    "florence": "Florence",
    "milan": "Milan",
    "italy": "Italy",
    "barcelona": "Barcelona",
    "madrid": "Madrid",
    "spain": "Spain",
    "amsterdam": "Amsterdam",
    "netherlands": "Netherlands",
    "germany": "Germany",
    "berlin": "Berlin",
    "munich": "Munich",
    "greece": "Greece",
    "athens": "Athens",
    "santorini": "Santorini",
    "mykonos": "Mykonos",
    "turkey": "Turkey",
    "istanbul": "Istanbul",
    "cappadocia": "Cappadocia",
    "egypt": "Egypt",
    "cairo": "Cairo",
    "south africa": "South Africa",
    "cape town": "Cape Town",
    "australia": "Australia",
    "sydney": "Sydney",
    "melbourne": "Melbourne",
    "new zealand": "New Zealand",
    "auckland": "Auckland",
    "canada": "Canada",
    "toronto": "Toronto",
    "vancouver": "Vancouver",
    "nepal": "Nepal",
    "kathmandu": "Kathmandu",
    "pokhara": "Pokhara",
    "bhutan": "Bhutan",
    "sri lanka": "Sri Lanka",
    "colombo": "Colombo",
    "malaysia": "Malaysia",
    "kuala lumpur": "Kuala Lumpur",
    "vietnam": "Vietnam",
    "hanoi": "Hanoi",
    "da nang": "Da Nang",
    "ho chi minh": "Ho Chi Minh City",
    "mauritius": "Mauritius",
    "seychelles": "Seychelles",
    "south korea": "South Korea",
    "seoul": "Seoul",
    "china": "China",
    "beijing": "Beijing",
    "russia": "Russia",
    "moscow": "Moscow",
    "brazil": "Brazil",
    "rio": "Rio de Janeiro",
    "austria": "Austria",
    "vienna": "Vienna",
    "prague": "Prague",
    "budapest": "Budapest",
    "portugal": "Portugal",
    "lisbon": "Lisbon",
    "ireland": "Ireland",
    "dublin": "Dublin",
    "belgium": "Belgium",
    "brussels": "Brussels",
    "sweden": "Sweden",
    "stockholm": "Stockholm",
    "norway": "Norway",
    "oslo": "Oslo",
    "denmark": "Denmark",
    "copenhagen": "Copenhagen",
    "finland": "Finland",
    "helsinki": "Helsinki",
    "iceland": "Iceland",
    "reykjavik": "Reykjavik"
}

NON_DESTINATIONS = {
    "hi", "hello", "hey", "hola", "namaste", "greetings", "good morning", "good evening", "good afternoon",
    "bye", "goodbye", "see you", "exit", "quit",
    "help", "menu", "info", "features", "options", "commands",
    "yes", "no", "yep", "nope", "ok", "okay", "sure", "fine", "alright", "cancel", "stop", "restart", "start over", "reset",
    "thanks", "thank you", "thx", "cool", "great", "awesome", "perfect", "sounds good", "nice",
    "solo", "family", "friends", "couple", "honeymoon", "alone", "myself", "partner", "wife", "husband", "kids", "parents",
    "flight", "flights", "plane", "planes", "train", "trains", "railway", "bus", "buses", "cab", "cabs", "car", "cars", "bike", "bikes", "scooter",
    "hotel", "hotels", "resort", "resorts", "hostel", "hostels", "homestay", "homestays", "stay", "stays", "accommodation", "dorm",
    "budget", "luxury", "cheap", "affordable", "economy", "premium", "standard",
    "beach", "beaches", "adventure", "nature", "heritage", "culture", "spirituality", "spiritual", "nightlife", "party", "food", "relaxation", "shopping", "sightseeing", "mountains", "hills", "trekking", "water sports",
    "today", "tomorrow", "yesterday", "weekend", "week", "month", "year", "day", "days", "night", "nights",
    "trip", "trips", "tour", "tours", "vacation", "vacations", "holiday", "holidays", "travel", "travelling", "traveling", "package", "packages", "itinerary", "plan", "plans",
    "booking", "book", "ticket", "tickets", "invoice", "pass", "download", "confirm", "confirmation",
    "weather", "climate", "temperature", "forecast", "season", "monsoon", "summer", "winter",
    "somewhere", "anywhere", "nowhere", "place", "places", "destination", "destinations", "city", "cities", "state", "states", "country", "countries",
    "anything", "nothing", "something", "everything",
    "what", "where", "when", "how", "why", "who", "which",
    "first", "second", "third", "fourth", "fifth",
    # Broken English & slang tokens
    "wid", "wth", "wit", "wiv", "frnd", "frnds", "frend", "frends", "freind", "freinds",
    "fmly", "famly", "fmli", "parnts", "kidz", "cpl", "copule", "cuple", "patner", "patnr", "wifey", "hubby", "husbnd",
    "alonee", "myslf", "singl", "akela",
    "trn", "trian", "railwayy", "flt", "flite", "plyt", "flightt", "bick", "skoter", "scoty",
    "chp", "chep", "sasta", "hotl", "hotle", "hotal", "resrt", "luxry", "luxary", "hstl", "hostle", "homstay",
    "bch", "bech", "beachs", "advntr", "adventur", "rfting", "raftng", "raftin", "scba", "dving", "treking", "paraglidng", "sking", "bungi", "cmping",
    "wat", "wats", "wht", "whr", "wer", "hw", "undr", "btwn", "bgdt", "bdgt", "budgt",
    "dys", "dy", "daes", "dayz", "din", "dins", "nts", "nit", "nits", "nite", "nites",
    "pln", "plz", "pls", "plzz", "plss", "wnt", "wana", "wanna",
    "karo", "banao", "jana", "jaana", "hai", "mein", "se", "ke", "sath", "ko", "bhi", "aur", "chahiye", "batao", "dekhna"
}

INTEREST_KEYWORDS = {
    "beach": ["beach", "beaches", "seashore", "coast", "coastal", "ocean", "sea"],
    "adventure": ["adventure", "trekking", "trek", "rafting", "hiking", "paragliding", "bungee", "water sports", "thrill", "safari"],
    "nature": ["nature", "scenic", "mountains", "mountain", "hills", "waterfall", "waterfalls", "valley", "lake", "lakes", "tea garden", "tea gardens", "greenery"],
    "heritage": ["heritage", "history", "historical", "fort", "forts", "palace", "palaces", "monument", "monuments", "temple", "temples", "monastery", "monasteries"],
    "spirituality": ["spiritual", "spirituality", "temple", "temples", "ghat", "ghats", "aarti", "puja", "monks", "meditation", "ashram"],
    "nightlife": ["nightlife", "party", "parties", "club", "clubs", "pub", "pubs", "bars", "music"],
    "food": ["food", "cuisine", "seafood", "cafe", "cafes", "street food", "culinary", "restaurant", "dining"],
    "relaxation": ["relax", "relaxing", "relaxation", "peaceful", "peace", "chill", "serene", "wellness", "spa", "backwaters", "boating"]
}

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

ACTIVITY_SYNONYM_MAP = {
    # River Rafting
    "river rafting": "river_rafting",
    "white water rafting": "river_rafting",
    "whitewater rafting": "river_rafting",
    "water rafting": "river_rafting",
    "river raft": "river_rafting",
    "rafting": "river_rafting",
    "raft": "river_rafting",

    # Trekking & Hiking
    "mountain trekking": "trekking",
    "mountain trek": "trekking",
    "mountain hike": "trekking",
    "trekking": "trekking",
    "trek": "trekking",
    "hiking": "trekking",
    "hike": "trekking",
    "backpacking": "trekking",

    # Scuba Diving
    "deep sea diving": "scuba_diving",
    "scuba diving": "scuba_diving",
    "scuba dive": "scuba_diving",
    "scuba": "scuba_diving",
    "diving": "scuba_diving",

    # Paragliding
    "tandem paragliding": "paragliding",
    "paragliding": "paragliding",
    "paraglide": "paragliding",
    "glide": "paragliding",
    "gliding": "paragliding",

    # Skiing & Snowboarding
    "snow skiing": "skiing",
    "snowboarding": "skiing",
    "snowboard": "skiing",
    "skiing": "skiing",
    "ski": "skiing",

    # Wildlife Safari
    "wildlife safari": "wildlife_safari",
    "jungle safari": "wildlife_safari",
    "tiger safari": "wildlife_safari",
    "jeep safari": "wildlife_safari",
    "safari": "wildlife_safari",
    "wildlife": "wildlife_safari",

    # Camping
    "bonfire camping": "camping",
    "tent stay": "camping",
    "glamping": "camping",
    "camping": "camping",
    "camp": "camping",

    # Snorkeling
    "reef snorkeling": "snorkeling",
    "snorkeling": "snorkeling",
    "snorkel": "snorkeling",

    # Bungee Jumping
    "bungy jumping": "bungee_jumping",
    "bungee jumping": "bungee_jumping",
    "bungee jump": "bungee_jumping",
    "bungee": "bungee_jumping",

    # Surfing
    "kite surfing": "surfing",
    "wind surfing": "surfing",
    "surfing": "surfing",
    "surf": "surfing",

    # Kayaking
    "kayaking": "kayaking",
    "kayak": "kayaking",
    "canoeing": "kayaking",
    "canoe": "kayaking",

    # Rock Climbing
    "rock climbing": "rock_climbing",
    "bouldering": "rock_climbing",
    "rappelling": "rock_climbing",

    # Ziplining
    "flying fox": "ziplining",
    "zip line": "ziplining",
    "ziplining": "ziplining",
    "zipline": "ziplining",

    # Beach Activities
    "beach activities": "beach_activities",
    "beach holiday": "beach_activities",
    "beach hopping": "beach_activities",
    "beach vacation": "beach_activities",
    "beach trip": "beach_activities",
    "beaches": "beach_activities",

    # Sightseeing / Heritage
    "historical sightseeing": "historical_sightseeing",
    "historical places": "heritage_and_culture",
    "historical spots": "historical_sightseeing",
    "sightseeing": "historical_sightseeing",
    "heritage tour": "heritage_and_culture",
    "heritage": "heritage_and_culture",
    "history": "heritage_and_culture",
    "historical": "heritage_and_culture",
    "cultural": "heritage_and_culture",
    "culture": "heritage_and_culture",

    # Pilgrimage & Spirituality
    "spiritual tour": "pilgrimage",
    "spiritual trip": "pilgrimage",
    "pilgrimage": "pilgrimage",

    # Shopping
    "bazaar shopping": "shopping",
    "shopping": "shopping",

    # Adventure Sports general
    "adventure sports": "adventure_sports",
    "adventure activities": "adventure_sports",
    "outdoor adventure": "adventure_sports",
    "adventure trip": "adventure_sports",
    "extreme sports": "adventure_sports",
    "adventure": "adventure_sports",
    "adventures": "adventure_sports",
    "thrill": "adventure_sports",

    # Nature & Mountains
    "nature and mountains": "nature_and_mountains",
    "mountains and nature": "nature_and_mountains",
    "mountain escape": "nature_and_mountains",
    "hill station": "nature_and_mountains",
    "nature trip": "nature_and_mountains",
    "mountains": "nature_and_mountains",
    "mountain": "nature_and_mountains",
    "waterfalls": "nature_and_mountains",
    "greenery": "nature_and_mountains",
    "valleys": "nature_and_mountains",
    "nature": "nature_and_mountains",
    "hills": "nature_and_mountains",

    # Relaxation & Wellness
    "relaxation and wellness": "relaxation_and_wellness",
    "relaxation": "relaxation_and_wellness",
    "relaxing": "relaxation_and_wellness",
    "peace of mind": "relaxation_and_wellness",
    "wellness": "relaxation_and_wellness",
    "peaceful": "relaxation_and_wellness",
    "relax": "relaxation_and_wellness"
}

UNSUPPORTED_ACTIVITIES = [
    "canyoning", "canyon", "skydiving", "skydive", "hot air balloon",
    "caving", "spelunking", "wakeboarding", "kiteboarding"
]


class EntityExtractor:
    def __init__(self):
        pass

    def extract_destination(self, text: str) -> str:
        """Extracts destination from text using the gazetteer and fuzzy matching."""
        if not text:
            return None
        candidates = [text.lower()]
        norm = normalize_broken_english(text.lower())
        if norm != text.lower():
            candidates.append(norm)

        # 1. Exact alias match (longest first)
        for cand in candidates:
            for alias in sorted(DESTINATION_MAP.keys(), key=lambda x: -len(x)):
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, cand):
                    return DESTINATION_MAP[alias]

        # 2. Fuzzy match on individual words against supported destinations
        for cand in candidates:
            words = re.findall(r'[a-zA-Z]{3,}', cand)
            for w in words:
                if w in NON_DESTINATIONS or w in SLANG_AND_TYPO_MAP:
                    continue
                matches = difflib.get_close_matches(w, list(DESTINATION_MAP.keys()), n=1, cutoff=0.80)
                if matches:
                    matched_key = matches[0]
                    # Avoid short word mismatch false positives
                    if len(w) <= 4 and len(matched_key) <= 4 and w != matched_key:
                        diffs = sum(1 for a, b in zip(w, matched_key) if a != b) + abs(len(w) - len(matched_key))
                        if diffs > 1:
                            continue
                    return DESTINATION_MAP[matched_key]

        return None

    def extract_duration(self, text: str) -> int:
        """Extracts trip duration in number of days, supporting broken English and abbreviations."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        # 1. Pattern like "4-day", "4 days", "3 nights", "5 d", "4 dys", "4 din", "2 nts"
        for t in [text_lower, norm]:
            m = re.search(r'\b(\d+)\s*(-|\s)?\s*(?:days?|nights?|d|dys?|dayz|dins?|nts?|nits?|daes?)\b', t)
            if m:
                days = int(m.group(1))
                return max(1, min(days, 14))

        # 2. Hindi / Hinglish numeral patterns (e.g. 'char din', 'teen din', 'do din', 'ek din')
        hindi_numerals = {
            "ek": 1, "one": 1, "do": 2, "two": 2, "teen": 3, "three": 3,
            "char": 4, "chaar": 4, "four": 4, "paanch": 5, "panch": 5, "five": 5,
            "chhe": 6, "che": 6, "six": 6, "saat": 7, "seven": 7
        }
        for word, num in hindi_numerals.items():
            pattern = r'\b' + word + r'\s*(-|\s)?\s*(?:days?|nights?|d|dys?|din|dins)\b'
            if re.search(pattern, text_lower) or re.search(pattern, norm):
                return num

        # 3. Word numbers: "three days", "four day"
        for word, num in WORD_TO_NUM.items():
            pattern = r'\b' + word + r'\s*(-|\s)?\s*(?:day|days|night|nights)\b'
            if re.search(pattern, text_lower) or re.search(pattern, norm):
                return num

        # 4. Special duration keywords with word boundaries
        for t in [text_lower, norm]:
            if re.search(r'\bweekend\b', t):
                return 2
            if re.search(r'\ba week\b|\bone week\b', t):
                return 7
            if re.search(r'(?<!\d-)\bday trip\b|\bone day\b', t):
                return 1

        # 5. Standalone single digit input (e.g. user answered duration prompt with just '4' or '3')
        m_digit = re.match(r'^\s*(\d{1,2})\s*$', text.strip())
        if m_digit:
            val = int(m_digit.group(1))
            if 1 <= val <= 14:
                return val

        return None

    def extract_budget(self, text: str) -> int:
        """Extracts budget amount in Indian Rupees, supporting 'k', 'hazar', and broken formats."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        for t in [text_lower, norm]:
            # Handle 'k' notation like '15k', '20.5k', '₹20k', '25 k', '15k rs'
            m_k = re.search(r'(?:₹|rs\.?|inr|budget\s*(?:of|is|:)?|under|within|around|upto)?\s*(\d+(?:\.\d+)?)\s*k\b', t)
            if m_k:
                try:
                    return int(float(m_k.group(1)) * 1000)
                except ValueError:
                    pass

            # Handle 'hazar' / 'thousand' notation like '15 hazar', '15 hazaar'
            m_hazar = re.search(r'\b(\d+)\s*(?:hazar|hazaari|hazaar|hazr|thousand)\b', t)
            if m_hazar:
                try:
                    return int(m_hazar.group(1)) * 1000
                except ValueError:
                    pass

            # Handle numbers with commas or explicit currency/budget pre-tags (e.g. '15,000', '₹15000', '15000 rs', '15000 tak')
            m_num = re.search(r'(?:₹|rs\.?|inr|under|around|approx|below|upto|budget\s*(?:of|is|:)?)\s*(\d{1,3}(?:,\d{3})+|\d{4,6})', t)
            if m_num:
                raw_val = m_num.group(1).replace(',', '')
                try:
                    val = int(raw_val)
                    if val >= 1000:
                        return val
                except ValueError:
                    pass

            # Number followed by currency / budget word (e.g. '15000 rupees', '15000 rs', '15000 budget', '15000 inr')
            m_post = re.search(r'\b(\d{4,6})\s*(?:rs|rupees?|inr|budget|tak|approx|only)\b', t)
            if m_post:
                try:
                    return int(m_post.group(1))
                except ValueError:
                    pass

            # Standalone 4-6 digit numbers with 'under/within/budget'
            m_standalone = re.search(r'\b(?:under|within|upto|below|with|budget)\s*(\d{4,6})\b', t)
            if m_standalone:
                try:
                    return int(m_standalone.group(1))
                except ValueError:
                    pass

        # Standalone large number between 2000 and 300000 (e.g. user just replies '15000' or '20000')
        m_any = re.search(r'\b(\d{4,6})\b', text_lower)
        if m_any:
            val = int(m_any.group(1))
            if 2000 <= val <= 300000:
                return val

        return None

    def extract_travelers(self, text: str) -> int:
        """Extracts number of travelers."""
        text_lower = text.lower()

        if re.search(r'\b(?:couple|honeymoon)\b', text_lower):
            return 2
        if re.search(r'\b(?:solo|myself|for me|alone)\b', text_lower):
            return 1
        if re.search(r'\bfamily of 4\b|\bfamily of four\b', text_lower):
            return 4
        if re.search(r'\bfamily of 3\b|\bfamily of three\b', text_lower):
            return 3
        if re.search(r'\bfamily of 5\b|\bfamily of five\b', text_lower):
            return 5

        # Regex for '2 people', '3 persons', '4 travelers', '2 friends'
        m = re.search(r'\b(\d+)\s*(?:people|persons|travelers|friends|adults|members|pax)\b', text_lower)
        if m:
            return int(m.group(1))

        for word, num in WORD_TO_NUM.items():
            pattern = r'\b' + word + r'\s*(?:people|persons|travelers|friends|adults|members|pax)\b'
            if re.search(pattern, text_lower):
                return num

        m_for = re.search(r'\bfor\s+(\d+)\s*(?:of us)?\b(?!\s*(?:day|days|night|nights|week|month|hour|hours|am|pm|k|rs|rupee))', text_lower)
        if m_for and not re.search(r'\bfor\s+\d+\s*(?:day|days|night|nights)\b', text_lower):
            return int(m_for.group(1))

        return None

    def extract_removals(self, text: str) -> List[str]:
        """Detects categories the user explicitly wishes to remove/exclude."""
        text_lower = text.lower()
        removals = []

        # Find clauses specifically after removal verbs up to conjunctions or punctuation
        removal_patterns = [
            r'\b(?:remove|exclude|no|without|drop|don\'t want|skip)\s+([^,.;]+?)(?=\s+(?:and\s+add|and\s+include|add|include|replace|instead|but)|[,.;]|$)',
            r'\breplace\s+([^,.;]+?)(?=\s+with|\s+by)'
        ]

        for pat in removal_patterns:
            matches = re.finditer(pat, text_lower)
            for m in matches:
                clause = m.group(1).strip()
                for category, keywords in INTEREST_KEYWORDS.items():
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', clause):
                            if category not in removals:
                                removals.append(category)
                            break

        return removals

    def extract_additions(self, text: str) -> List[str]:
        """Detects categories user explicitly wishes to add."""
        text_lower = text.lower()
        additions = []

        addition_patterns = [
            r'\b(?:add|include|more)\s+([^,.;]+)',
            r'\bwith\s+([^,.;]+)',
            r'\breplace\s+.*?with\s+([^,.;]+)'
        ]

        for pat in addition_patterns:
            matches = re.finditer(pat, text_lower)
            for m in matches:
                clause = m.group(1).strip()
                for category, keywords in INTEREST_KEYWORDS.items():
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', clause):
                            if category not in additions:
                                additions.append(category)
                            break

        return additions

    def extract_interests(self, text: str) -> List[str]:
        """Extracts general interests mentioned in text."""
        text_lower = text.lower()
        interests = []

        for category, keywords in INTEREST_KEYWORDS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    if category not in interests:
                        interests.append(category)
                    break

        return interests

    def extract_travel_with(self, text: str) -> Optional[str]:
        """Extracts companion/travel type, supporting broken English and abbreviations."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        for t in [text_lower, norm]:
            if re.search(r'\b(?:friends?|frnds?|frends?|freinds?|gang|buddies|colleagues|group of friends|with (?:my )?(?:friends?|frnds?|frends?)|wid (?:my )?(?:friends?|frnds?|frends?)|dost)\b', t):
                return "Friends"
            if re.search(r'\b(?:family|fmly|famly|fmli|parents|parnts|kids|kidz|children|with (?:my )?(?:family|fmly|famly)|wid (?:my )?(?:family|fmly|famly)|family ke sath)\b', t):
                return "Family"
            if re.search(r'\b(?:couple|copule|cuple|cpl|partner|patner|patnr|wife|wifey|husband|husbnd|girlfriend|boyfriend|gf|bf|honeymoon|with (?:my )?(?:wife|husband|partner|patner)|wid (?:my )?(?:wife|husband|partner|patner))\b', t):
                return "Couple"
            if re.search(r'\b(?:solo|alone|me alone|myself|myslf|just me|by myself|travelling alone|for me|single|me only|akela)\b', t):
                return "Solo"

        # Numerical index replies from "1. Solo  2. Family  3. Friends  4. Couple"
        m_num = re.match(r'^\s*([1-4])\s*$', text_lower)
        if m_num:
            return {"1": "Solo", "2": "Family", "3": "Friends", "4": "Couple"}[m_num.group(1)]
        return None

    def extract_transport(self, text: str) -> Optional[str]:
        """Extracts transport preference, supporting broken English and abbreviations."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        for t in [text_lower, norm]:
            if re.search(r'\b(?:trains?|trn|trian|trainn|railway|rail|irctc|express train|by train|train se|by trn)\b', t):
                return "Train"
            if re.search(r'\b(?:flights?|flite|flt|plyt|by flight|by air|planes?|aeroplane|airplan|by plane|flying|flight se|flite se)\b', t):
                return "Flight"
            if re.search(r'\b(?:buses?|by bus|volvo|sleeper bus|coach|bus se)\b', t):
                return "Bus"
            if re.search(r'\b(?:cabs?|taxis?|cars?|by car|drive|self-drive|rental car|car se|cab se)\b', t):
                return "Cab / Car"
            if re.search(r'\b(?:bikes?|bick|bikee|scooters?|scoty|skoter|activa|motorcycles?|two-wheeler|bullet|bike se)\b', t):
                return "Rental Bike / Scooter"

        m_num = re.match(r'^\s*([1-5])\s*$', text_lower)
        if m_num:
            return {"1": "Flight", "2": "Train", "3": "Bus", "4": "Cab / Car", "5": "Rental Bike / Scooter"}[m_num.group(1)]
        return None

    def extract_accommodation(self, text: str) -> Optional[str]:
        """Extracts accommodation preference, supporting broken English and abbreviations."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        for t in [text_lower, norm]:
            if re.search(r'\b(?:budget hotel|cheap hotel|chp hotel|chep hotel|budget stay|budget room|sasta hotel|economy hotel|affordable hotel|cheap stay|hotl|hotle|hotal|norml stay)\b', t):
                return "Budget Hotel"
            if re.match(r'^\s*(?:budget|cheap|economy|standard)\s*$', t):
                return "Budget Hotel"
            if re.search(r'\b(?:resorts?|resrt|resortt|beach resort|spa resort|luxury resort)\b', t):
                return "Luxury Resort"
            if re.search(r'\b(?:luxury hotel|luxry|luxary|5 star|five star|boutique hotel|heritage hotel|luxury|delux)\b', t):
                return "Luxury Hotel"
            if re.search(r'\b(?:hostels?|hstl|hostle|backpackers?|zostel|dorms?|homestays?|homstay|bnbs?|guest houses?)\b', t):
                return "Hostel / Homestay"
            if re.search(r'\b(?:hotel|hotels|stay)\b', t) and not re.search(r'\b(?:day|days|night|nights)\b', t):
                return "Budget Hotel"

        m_num = re.match(r'^\s*([1-4])\s*$', text_lower)
        if m_num:
            return {"1": "Budget Hotel", "2": "Luxury Resort", "3": "Luxury Hotel", "4": "Hostel / Homestay"}[m_num.group(1)]
        return None

    def extract_memory_query(self, text: str) -> Optional[str]:
        """Detects if user is querying conversation memory, supporting broken English."""
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        for t in [text_lower, norm]:
            if re.search(r'\b(?:what (?:was|is) my budget|how much is my budget|my budget amount|check my budget|wat is my bdgt|wat was my budget|hw mch budget|show budget)\b', t):
                return "budget"
            if re.search(r'\b(?:where am i going|what is my destination|where is my trip|which city am i visiting|whr am i going|whr to go)\b', t):
                return "destination"
            if re.search(r'\b(?:how many days|what is the duration|how long is my trip|duration of my trip|hw many dys|kitne din)\b', t):
                return "duration"
            if re.search(r'\b(?:who am i travelling with|who are my companions|travel type|travelling with whom|who travel wid|with who)\b', t):
                return "travel_with"
            if re.search(r'\b(?:what is my transport|how am i travelling|transport mode|which transport did i pick|wat transport|how travel)\b', t):
                return "transport"
            if re.search(r'\b(?:what hotel|where am i staying|accommodation type|which stay did i pick|wat hotel|where stay)\b', t):
                return "accommodation"
            if re.search(r'\b(?:what are my activities|what are my interests|what activities did i pick|wat activities)\b', t):
                return "interests"
            if re.search(r'\b(?:show my trip (?:summary|details|plan)|what are my trip details|what have we planned(?: so far)?|trip summary|show plan)\b', t):
                return "all"
        return None

    def extract_budget_calculation(self, text: str) -> Optional[int]:
        """Detects budget calculation inquiry like 'Can I do this trip under 10000?'."""
        text_lower = text.lower()
        m = re.search(r'\b(?:can i (?:do|make|visit|travel).*?(?:under|within|for)\s*(?:₹|rs\.?|inr)?\s*(\d{4,6}|(?:\d+k)))\b', text_lower)
        if m:
            raw = m.group(1).lower().replace('₹', '').replace('rs', '').strip()
            if 'k' in raw:
                try:
                    return int(float(raw.replace('k', '')) * 1000)
                except ValueError:
                    pass
            try:
                return int(raw)
            except ValueError:
                pass
        return None

    def extract_unavailable_destination(self, text: str) -> Optional[str]:
        """
        Detects if user specified a location/city that is NOT supported by TripWise.
        Returns the formatted location name if an unavailable location is detected, else None.
        """
        if not text:
            return None

        # If an available destination is present, it's NOT unavailable
        if self.extract_destination(text):
            return None

        # If this is an activity inquiry (e.g. 'I want to go river rafting', 'rafting near Mumbai'), do not treat as unavailable destination
        if self.extract_activity(text):
            return None

        # If user is answering companions, transport, stay, duration, budget, or memory query, do not treat as unavailable destination
        if (self.extract_travel_with(text) or 
            self.extract_transport(text) or 
            self.extract_accommodation(text) or 
            self.extract_duration(text) or 
            self.extract_budget(text) or
            self.extract_memory_query(text)):
            return None

        text_lower = text.lower().strip()
        norm = normalize_broken_english(text_lower)

        # 1. Match against extensive gazetteer of known cities/destinations
        for t in [text_lower, norm]:
            for alias in sorted(KNOWN_UNAVAILABLE_DESTINATIONS.keys(), key=lambda x: -len(x)):
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, t):
                    return KNOWN_UNAVAILABLE_DESTINATIONS[alias]

        # 2. Match linguistic intent patterns for travel destinations/locations
        patterns = [
            r'\b(?:visit|visiting|go to|going to|travel to|travelling to|trip to|tour to|vacation in|holiday in|explore|fly to|flight to|heading to)\s+([a-zA-Z\s]{2,30}?)(?=\s+(?:for|with|under|in|on|at|around|next|this|during|budget|day|days|night|nights)|[.,?!]|$)',
            r'\b(?:weather|places|food|hotels?|attractions?|sights?|budget)\s+(?:in|of|at|for)\s+([a-zA-Z\s]{2,30}?)(?=[.,?!]|$)',
            r'\b(?:how about|what about|can (?:i|we) (?:go|visit|travel) to)\s+([a-zA-Z\s]{2,30}?)(?=[.,?!]|$)',
            r'\b(?:in|at|for|about|of)\s+([a-zA-Z\s]{2,30}?)\s+(?:weather|places|food|hotels?|attractions?|sights?|budget)(?=[.,?!]|$)'
        ]

        for pat in patterns:
            for t in [text_lower, norm]:
                m = re.search(pat, t)
                if m:
                    cand = m.group(1).strip()
                    cand = re.sub(r'^(?:the|a|an|some|my)\s+', '', cand).strip()
                    cand_words = cand.lower().split()
                    if cand and cand.lower() not in DESTINATION_MAP and cand.lower() not in NON_DESTINATIONS and len(cand) >= 2:
                        if not any(w in NON_DESTINATIONS or w in SLANG_AND_TYPO_MAP for w in cand_words):
                            return cand.title()

        # 3. Match standalone 1-3 word place names if no other slot or command matched
        if not re.search(r'\d', text):
            cleaned = re.sub(r'[^a-zA-Z\s]', '', text).strip()
            words = cleaned.split()
            if 1 <= len(words) <= 3:
                cand_lower = cleaned.lower()
                norm_cand = norm.strip()
                if (cand_lower and cand_lower not in DESTINATION_MAP and 
                    norm_cand not in DESTINATION_MAP and 
                    cand_lower not in NON_DESTINATIONS and 
                    norm_cand not in NON_DESTINATIONS and 
                    len(cand_lower) >= 2):
                    if not any(w.lower() in NON_DESTINATIONS or w.lower() in SLANG_AND_TYPO_MAP for w in words):
                        for alias in KNOWN_UNAVAILABLE_DESTINATIONS:
                            if alias in cand_lower or cand_lower in alias or difflib.get_close_matches(cand_lower, [alias], cutoff=0.82):
                                return KNOWN_UNAVAILABLE_DESTINATIONS[alias]
                        if len(words) == 1 and len(cleaned) >= 3:
                            return cleaned.title()

        return None

    def extract_activity(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracts activity from natural language text, supporting broken English and typos.
        Returns a dict with 'activity', 'is_unsupported', and 'raw_activity' if found, else None.
        """
        if not text:
            return None
        text_lower = text.lower()
        norm = normalize_broken_english(text_lower)

        # Check unsupported activities first for fallback handling
        for unsupp in sorted(UNSUPPORTED_ACTIVITIES, key=lambda x: -len(x)):
            pattern = r'\b' + re.escape(unsupp) + r'\b'
            if re.search(pattern, text_lower) or re.search(pattern, norm):
                return {
                    "activity": unsupp.replace(" ", "_"),
                    "is_unsupported": True,
                    "raw_activity": unsupp
                }

        # Check supported activities across both normalized and raw text
        for t in [norm, text_lower]:
            for phrase in sorted(ACTIVITY_SYNONYM_MAP.keys(), key=lambda x: -len(x)):
                pattern = r'\b' + re.escape(phrase) + r'\b'
                if re.search(pattern, t):
                    norm_key = ACTIVITY_SYNONYM_MAP[phrase]
                    return {
                        "activity": norm_key,
                        "is_unsupported": False,
                        "raw_activity": phrase
                    }

        return None

    def extract_origin(self, text: str) -> Optional[str]:
        """Extracts user location or proximity preference (e.g. 'near Mumbai', 'from Delhi')."""
        text_lower = text.lower()
        patterns = [
            r'\b(?:near|around|close to|nearby)\s+([a-zA-Z\s]{2,20}?)(?=\s+(?:for|with|under|in|and)|[.,?!]|$)',
            r'\bi (?:live|stay|am) in\s+([a-zA-Z\s]{2,20}?)(?=[.,?!]|$)',
            r'\bfrom\s+([a-zA-Z\s]{2,20}?)(?=\s+(?:for|with|under|to)|[.,?!]|$)'
        ]
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                cand = m.group(1).strip()
                cand_clean = re.sub(r'^(?:the|a)\s+', '', cand).strip()
                if cand_clean and cand_clean not in NON_DESTINATIONS and len(cand_clean) >= 2:
                    return cand_clean.title()
        return None

    def extract_sort_preference(self, text: str) -> Optional[str]:
        """Detects if user is asking for cheaper/budget-friendly options."""
        text_lower = text.lower()
        if re.search(r'\b(?:which (?:is|one is)?\s*(?:cheaper|cheapest|more affordable|low cost)|cheaper|cheapest|lowest cost|lowest budget|budget friendly)\b', text_lower):
            return "cost"
        return None

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Runs the entire entity extraction suite and returns structured entities."""
        norm_text = normalize_broken_english(text)

        destination = self.extract_destination(text) or self.extract_destination(norm_text)
        duration = self.extract_duration(text) or self.extract_duration(norm_text)
        budget = self.extract_budget(text) or self.extract_budget(norm_text)
        travelers = self.extract_travelers(text) or self.extract_travelers(norm_text)
        travel_with = self.extract_travel_with(text) or self.extract_travel_with(norm_text)
        transport = self.extract_transport(text) or self.extract_transport(norm_text)
        accommodation = self.extract_accommodation(text) or self.extract_accommodation(norm_text)
        memory_query = self.extract_memory_query(text) or self.extract_memory_query(norm_text)
        budget_calc = self.extract_budget_calculation(text) or self.extract_budget_calculation(norm_text)
        removals = self.extract_removals(text) or self.extract_removals(norm_text)
        additions = self.extract_additions(text) or self.extract_additions(norm_text)
        general_interests = self.extract_interests(text) or self.extract_interests(norm_text)
        activity_data = self.extract_activity(text) or self.extract_activity(norm_text)
        origin_city = self.extract_origin(text) or self.extract_origin(norm_text)
        sort_preference = self.extract_sort_preference(text) or self.extract_sort_preference(norm_text)

        unavailable_destination = self.extract_unavailable_destination(text)

        # Merge interests: general interests minus removals, plus additions
        active_interests = [i for i in general_interests if i not in removals]
        for a in additions:
            if a not in active_interests:
                active_interests.append(a)

        return {
            "destination": destination,
            "unavailable_destination": unavailable_destination,
            "duration": duration,
            "budget": budget,
            "travelers": travelers,
            "travel_with": travel_with,
            "transport": transport,
            "accommodation": accommodation,
            "memory_query": memory_query,
            "budget_calc": budget_calc,
            "interests": active_interests,
            "removals": removals,
            "additions": additions,
            "activity_data": activity_data,
            "origin_city": origin_city,
            "sort_preference": sort_preference
        }
