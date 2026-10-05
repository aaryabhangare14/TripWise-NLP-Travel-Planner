import re
import string

# Safe NLTK imports with local fallback
try:
    import nltk
    from nltk.stem import PorterStemmer
    _stemmer = PorterStemmer()
except Exception:
    _stemmer = None

# Curated English stop words for travel NLP (carefully preserves negation/preposition signals like 'under', 'for', 'with', 'not', 'without')
STANDARD_STOP_WORDS = {
    "a", "an", "the", "and", "or", "is", "am", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "to", "of", "at", "by",
    "from", "in", "into", "on", "onto", "this", "that", "these", "those", "i",
    "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "will", "would",
    "shall", "should", "can", "could", "may", "might", "must", "so", "than",
    "too", "very", "just", "please", "want", "like", "need", "give", "show", "tell"
}

CONTRACTIONS = {
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "can't": "cannot",
    "couldn't": "could not",
    "won't": "will not",
    "wouldn't": "would not",
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "it's": "it is",
    "let's": "let us",
    "there's": "there is",
    "what's": "what is"
}

# Extensive lexical normalization map for broken English, SMS lingo, phonetic typos, and colloquialisms
SLANG_AND_TYPO_MAP = {
    # Pronouns, Auxiliaries & Connectives
    "u": "you",
    "ur": "your",
    "urs": "yours",
    "r": "are",
    "m": "am",
    "im": "i am",
    "wnt": "want",
    "wana": "want",
    "wanna": "want",
    "wants": "want",
    "wld": "would",
    "shld": "should",
    "cud": "could",
    "plz": "please",
    "pls": "please",
    "plzz": "please",
    "plss": "please",
    "thx": "thanks",
    "ty": "thank you",
    "bcoz": "because",
    "bcz": "because",
    "cuz": "because",
    "coz": "because",
    "abt": "about",
    "wat": "what",
    "wats": "what is",
    "wht": "what",
    "whr": "where",
    "wer": "where",
    "hw": "how",
    "undr": "under",
    "btwn": "between",
    "wid": "with",
    "wth": "with",
    "wit": "with",
    "wiv": "with",
    "n": "and",
    "nd": "and",

    # Travel & Itinerary Vocabulary
    "pln": "plan",
    "plann": "plan",
    "itinry": "itinerary",
    "itenary": "itinerary",
    "itinery": "itinerary",
    "itineraryy": "itinerary",
    "itenerary": "itinerary",
    "itnerary": "itinerary",
    "tourr": "tour",
    "holida": "holiday",
    "vacay": "vacation",
    "vacatn": "vacation",
    "locatn": "destination",
    "locashun": "destination",
    "destinatn": "destination",
    "plac": "place",
    "placs": "places",

    # Duration & Time abbreviations
    "dys": "days",
    "dy": "days",
    "dae": "days",
    "daes": "days",
    "dayz": "days",
    "din": "days",
    "dins": "days",
    "nts": "nights",
    "nit": "nights",
    "nits": "nights",
    "nite": "nights",
    "nites": "nights",
    "wknd": "weekend",
    "wk": "week",

    # Budget & Financial abbreviations
    "bgdt": "budget",
    "bdgt": "budget",
    "budgt": "budget",
    "bugdet": "budget",
    "budjet": "budget",
    "hazar": "thousand",
    "hazaari": "thousand",
    "hazaar": "thousand",
    "hazr": "thousand",
    "rs": "rupees",
    "rupy": "rupees",
    "rupes": "rupees",
    "rupe": "rupees",
    "inr": "rupees",

    # Companions
    "frnd": "friends",
    "frnds": "friends",
    "frend": "friends",
    "frends": "friends",
    "freind": "friends",
    "freinds": "friends",
    "buddies": "friends",
    "gangg": "friends",
    "fmly": "family",
    "famly": "family",
    "fmli": "family",
    "parnts": "family",
    "kidz": "family",
    "cpl": "couple",
    "copule": "couple",
    "cuple": "couple",
    "patner": "couple",
    "patnr": "couple",
    "wifey": "couple",
    "hubby": "couple",
    "husbnd": "couple",
    "alonee": "alone",
    "myslf": "myself",
    "singl": "single",
    "akela": "solo",

    # Transport
    "trn": "train",
    "trian": "train",
    "trainn": "train",
    "railwayy": "train",
    "flt": "flight",
    "flite": "flight",
    "plyt": "flight",
    "flightt": "flight",
    "aeroplan": "flight",
    "airplan": "flight",
    "bick": "bike",
    "bikee": "bike",
    "skoter": "scooter",
    "scoty": "scooter",

    # Accommodation
    "chp": "cheap",
    "chep": "cheap",
    "sasta": "budget",
    "hotl": "hotel",
    "hotle": "hotel",
    "hotal": "hotel",
    "hotls": "hotel",
    "resrt": "resort",
    "resortt": "resort",
    "luxry": "luxury",
    "luxary": "luxury",
    "hstl": "hostel",
    "hostle": "hostel",
    "homstay": "homestay",

    # Activities & Interests
    "bch": "beaches",
    "bech": "beaches",
    "beachs": "beaches",
    "bechez": "beaches",
    "advntr": "adventure",
    "adventur": "adventure",
    "adventures": "adventure",
    "rfting": "rafting",
    "raftng": "rafting",
    "raftin": "rafting",
    "scba": "scuba",
    "skuba": "scuba",
    "dving": "diving",
    "diveing": "diving",
    "divin": "diving",
    "treking": "trekking",
    "traeking": "trekking",
    "trekkin": "trekking",
    "hyking": "hiking",
    "hikin": "hiking",
    "paraglidng": "paragliding",
    "paraglidin": "paragliding",
    "glidng": "gliding",
    "sking": "skiing",
    "skiin": "skiing",
    "bungi": "bungee",
    "bungy": "bungee",
    "cmping": "camping",
    "campin": "camping",
    "snorkling": "snorkeling",
    "snorkle": "snorkeling",
    "serfing": "surfing",
    "surfin": "surfing",
    "kayking": "kayaking",
    "ziplinin": "ziplining",
    "natur": "nature",
    "mountan": "mountains",
    "montains": "mountains",
    "mounatins": "mountains",

    # Destinations Common Phonetic Typos & Aliases
    "goaa": "goa",
    "goo": "goa",
    "manli": "manali",
    "mnaali": "manali",
    "kerla": "kerala",
    "keral": "kerala",
    "kerela": "kerala",
    "karala": "kerala",
    "rishkesh": "rishikesh",
    "rshikesh": "rishikesh",
    "rishkes": "rishikesh",
    "jaipr": "jaipur",
    "jaypur": "jaipur",
    "jaipure": "jaipur",
    "ladak": "ladakh",
    "ladkh": "ladakh",
    "ooti": "ooty",
    "oti": "ooty",
    "otty": "ooty",
    "udaipr": "udaipur",
    "udaipoor": "udaipur",
    "udaypur": "udaipur",
    "darjiling": "darjeeling",
    "darjeling": "darjeeling",
    "darjling": "darjeeling",
    "banaras": "varanasi",
    "benares": "varanasi",
    "kashi": "varanasi",
    "varnasi": "varanasi",
    "varnsi": "varanasi",
    "aggra": "agra",
    "agraa": "agra"
}


def expand_contractions(text: str) -> str:
    """Expands common English contractions."""
    lower_text = text.lower()
    for contraction, expansion in CONTRACTIONS.items():
        lower_text = re.sub(r'\b' + re.escape(contraction) + r'\b', expansion, lower_text)
    return lower_text


def normalize_repeated_chars(text: str) -> str:
    """
    Collapses 3+ identical consecutive characters down to 1 or 2
    (e.g. goaaaa -> goa, hiiiii -> hi, pleaaase -> please, plzzz -> plz).
    """
    def repl(m):
        char = m.group(1)
        if char in ('e', 'o', 's', 'l'):
            return char * 2
        return char
    return re.sub(r'([a-zA-Z])\1{2,}', repl, text)


def normalize_broken_english(text: str) -> str:
    """
    Lexical normalizer that translates broken English, SMS abbreviations,
    phonetic typos, and colloquial numbers into standard English.
    """
    if not text:
        return ""
    t = text.lower()

    # 1. Normalize 'k' notation into standard numbers (e.g. 15k -> 15000, 20.5k -> 20500)
    def repl_k(m):
        num = float(m.group(1))
        return str(int(num * 1000))
    t = re.sub(r'\b(\d+(?:\.\d+)?)\s*k\b', repl_k, t, flags=re.I)

    # 2. Normalize Hindi/Hinglish hazar into thousands (e.g. 15 hazar -> 15000)
    t = re.sub(r'\b(\d+)\s*(?:hazar|hazaari|hazaar|hazr)\b', lambda m: str(int(m.group(1)) * 1000), t, flags=re.I)

    # 3. Normalize single letter 'd' or 'din' into 'days' when preceded by numbers
    t = re.sub(r'\b(\d+)\s*d\b', r'\1 days', t, flags=re.I)
    t = re.sub(r'\b(\d+)\s*(?:din|dins|dys?|dayz)\b', r'\1 days', t, flags=re.I)

    # 4. Normalize single letter 'n' or 'nts' into 'nights' when preceded by numbers
    t = re.sub(r'\b(\d+)\s*n\b', r'\1 nights', t, flags=re.I)
    t = re.sub(r'\b(\d+)\s*(?:nts?|nits?|nite|nites)\b', r'\1 nights', t, flags=re.I)

    # 5. Collapse repeated characters
    t = normalize_repeated_chars(t)

    # 6. Replace broken English, slang, and typo tokens using word boundaries
    tokens = re.split(r'(\W+)', t)
    normalized_tokens = []
    for tok in tokens:
        normalized_tokens.append(SLANG_AND_TYPO_MAP.get(tok, tok))

    return ''.join(normalized_tokens)


def tokenize(text: str) -> list:
    """
    Robust regex-based tokenizer that preserves hyphenated words,
    numbers, and standard alphanumeric words.
    """
    # Pattern matches words, numbers, and currency-like numbers
    tokens = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text)
    return tokens


def stem_word(word: str) -> str:
    """Applies Porter Stemmer if available, else simple suffix rules."""
    if _stemmer:
        try:
            return _stemmer.stem(word)
        except Exception:
            pass
    # Basic rule-based fallback
    word_lower = word.lower()
    for suffix in ["ing", "ies", "es", "s", "ed"]:
        if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 2:
            return word_lower[:-len(suffix)]
    return word_lower


def clean_text(text: str) -> str:
    """Clean, normalize broken English / slang, and normalize raw query text."""
    if not text:
        return ""
    text = expand_contractions(text)
    text = normalize_broken_english(text)
    # Remove commas in numbers (e.g. 15,000 -> 15000)
    text = re.sub(r'(?<=\d),(?=\d)', '', text)
    # Replace rupees symbols
    text = re.sub(r'[₹$€£]', ' ', text)
    # Remove punctuation except hyphens between words
    text = re.sub(r'[^\w\s\-]', ' ', text)
    # Collapse multiple whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess(text: str, remove_stopwords: bool = True, stem: bool = False) -> str:
    """
    Standard preprocessing pipeline:
    Clean -> Tokenize -> Filter Stopwords -> Stem (optional) -> Rejoin
    """
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    if remove_stopwords:
        tokens = [t for t in tokens if t.lower() not in STANDARD_STOP_WORDS]
    if stem:
        tokens = [stem_word(t) for t in tokens]
    return " ".join(tokens)


def preprocess_with_trace(text: str) -> dict:
    """
    Generates step-by-step NLP transformation trace for educational visualization
    and UI Academic Inspector.
    """
    normalized = normalize_broken_english(expand_contractions(text))
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    filtered = [t for t in tokens if t.lower() not in STANDARD_STOP_WORDS]
    stemmed = [stem_word(t) for t in filtered]

    return {
        "raw_text": text,
        "normalized_text": normalized,
        "cleaned_text": cleaned,
        "token_count": len(tokens),
        "tokens": tokens,
        "stopwords_removed": [t for t in tokens if t.lower() in STANDARD_STOP_WORDS],
        "filtered_tokens": filtered,
        "stemmed_tokens": stemmed,
        "processed_text": " ".join(filtered)
    }
