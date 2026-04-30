"""
Facebook Reels Automation - Bilingual English/Tamil Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Tamil branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file. "
        "For GitHub Actions: Add AI_MODEL to repository secrets."
    )

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for learners of Tamil)
# Essential Tamil learning categories + Motivational categories
CATEGORIES_ENGLISH = [
    "Greetings", "Basic Phrases", "Common Expressions", "Travel Tamil", "Restaurant Tamil",
    "Shopping Tamil", "Emergency Tamil", "Family Terms", "Numbers Tamil", "Time Tamil",
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Tamil translations for display
CATEGORIES_TAMIL = {
    "Greetings": "வணக்கங்கள்",
    "Basic Phrases": "அடிப்படை சொற்றொடர்கள்",
    "Common Expressions": "பொதுவான வாக்கியங்கள்",
    "Travel Tamil": "பயண தமிழ்",
    "Restaurant Tamil": "உணவக தமிழ்",
    "Shopping Tamil": "ஷாப்பிங் தமிழ்",
    "Emergency Tamil": "அவசர தமிழ்",
    "Family Terms": "குடும்ப சொற்கள்",
    "Numbers Tamil": "எண்கள்",
    "Time Tamil": "நேரம்",
    "Motivation": "ஊக்கம்",
    "Love": "காதல்",
    "Success": "வெற்றி",
    "Wisdom": "ஞானம்",
    "Happiness": "மகிழ்ச்சி",
    "Self Improvement": "சுய மேம்பாடு",
    "Gratitude": "நன்றி",
    "Friendship": "நட்பு",
    "Hope": "நம்பிக்கை",
    "Creativity": "படைப்பாற்றல்",
    "Inner Peace": "உள் அமைதி",
    "Confidence": "நம்பிக்கை",
    "Perseverance": "விடாமுயற்சி",
    "Inspiration": "உத்வேகம்",
    "Positive Life": "நேர்மறை வாழ்க்கை",
    "Courage": "தைரியம்",
    "Kindness": "கனிவு",
    "Patience": "பொறுமை",
    "Forgiveness": "மன்னிப்பு",
    "Strength": "வலிமை",
    "Joy": "ஆனந்தம்",
    "Balance": "சமநிலை",
    "Growth": "வளர்ச்சி",
    "Purpose": "நோக்கம்",
    "Mindfulness": "நுண்ணிய அறிவு",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
TAMIL_VOICE = "ta-IN-ValluvarNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Recent categories file (for rotation - prevents category repeats)
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"
MAX_RECENT_CATEGORIES = 15


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "tamil": phrase["tamil"],
            "transliteration": phrase.get("transliteration", ""),
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CATEGORY ROTATION MANAGEMENT (Prevent Repeats) ==============

def load_recent_categories():
    """Load recently used categories"""
    if RECENT_CATEGORIES_FILE.exists():
        with open(RECENT_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"recent_categories": [], "last_updated": None}


def save_recent_categories(data):
    """Save recent categories"""
    data["last_updated"] = datetime.now().isoformat()
    with open(RECENT_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_category():
    """Get a category that hasn't been used recently - ensures rotation across ALL 35 categories"""
    recent_data = load_recent_categories()
    recent = recent_data.get("recent_categories", [])

    available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent]

    if not available:
        recent_data["recent_categories"] = recent[-5:]
        save_recent_categories(recent_data)
        available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent_data["recent_categories"]]
        print(f"[rotation] All categories used recently - cleared old ones, {len(available)} available")

    selected = random.choice(available)

    recent.append(selected)

    if len(recent) > MAX_RECENT_CATEGORIES:
        recent = recent[-MAX_RECENT_CATEGORIES:]

    recent_data["recent_categories"] = recent
    save_recent_categories(recent_data)

    print(f"[rotation] Selected '{selected}' ({len(available)} available, {len(recent)} in recent history)")
    return selected


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""

    category_tamil = CATEGORIES_TAMIL[category_english]

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Tamil.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Tamil text should be CLEAN - use standard Tamil script
7. Do NOT include multiple versions or slashes - just ONE clean Tamil translation
8. Transliteration should be in Roman script (e.g., "vanakkam")

For each phrase:
1. English phrase (with commas for natural pauses)
2. Tamil translation (in Tamil script)
3. Transliteration (Roman script pronunciation, e.g., "vanakkam")

Return as JSON array:
[{{"english": "...", "tamil": "...", "transliteration": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.
IMPORTANT: Tamil text must be clean - no slashes, no multiple versions."""

            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a Tamil teacher. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            phrases = json.loads(content)

            for p in phrases:
                if "transliteration" not in p and "romaji" in p:
                    p["transliteration"] = p.pop("romaji")

            unique_phrases = []
            for phrase in phrases:
                if len(phrase["english"].split()) > 15:
                    continue
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break

            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""

    all_fallbacks = {
        "Greetings": [
            {"english": "Hello, nice to meet you.", "tamil": "வணக்கம், உங்களை சந்திப்பதில் மகிழ்ச்சி.", "transliteration": "Vanakkam, ungalaithi sandipapathil magizhchi."},
            {"english": "Good morning!", "tamil": "காலை வணக்கம்!", "transliteration": "Kalai vanakkam!"},
            {"english": "Good evening, how are you?", "tamil": "மாலை வணக்கம், எப்படி இருக்கிறீர்கள்?", "transliteration": "Malai vanakkam, eppadi irukkireergal?"},
            {"english": "See you tomorrow!", "tamil": "நாளை சந்திப்போம்!", "transliteration": "Naalai santhippom!"},
            {"english": "Goodbye, take care.", "tamil": "பிரியாவிடை, கவனமாக இருங்கள்.", "transliteration": "Priyaavidai, kavanamaga irungal."},
        ],
        "Basic Phrases": [
            {"english": "Thank you very much.", "tamil": "மிகவும் நன்றி.", "transliteration": "Migavum nandri."},
            {"english": "You're welcome.", "tamil": "நல்வரவு.", "transliteration": "Nalvaravu."},
            {"english": "I'm sorry, excuse me.", "tamil": "மன்னிக்கவும்.", "transliteration": "Mannikkavum."},
            {"english": "Yes, that's correct.", "tamil": "ஆம், அது சரியானது.", "transliteration": "Aam, athu thariyaanathu."},
            {"english": "No, I don't think so.", "tamil": "இல்லை, எனக்கு அப்படி தோன்றவில்லை.", "transliteration": "Illai, enakku appadi thondravailai."},
        ],
        "Common Expressions": [
            {"english": "How are you doing today?", "tamil": "இன்று எப்படி இருக்கிறீர்கள்?", "transliteration": "Indru eppadi irukkireergal?"},
            {"english": "I'm fine, thank you.", "tamil": "நான் நன்றாக இருக்கிறேன், நன்றி.", "transliteration": "Naan nandraaga irukkirean, nandri."},
            {"english": "What's your name?", "tamil": "உங்கள் பெயர் என்ன?", "transliteration": "Ungal peyar enna?"},
            {"english": "My name is...", "tamil": "என் பெயர்...", "transliteration": "En peyar..."},
            {"english": "Nice to meet you too.", "tamil": "உங்களை சந்திப்பதில் மகிழ்ச்சி.", "transliteration": "Ungalaithi sandipapathil magizhchi."},
        ],
        "Travel Tamil": [
            {"english": "Where is the bathroom?", "tamil": "குளியலறை எங்கே உள்ளது?", "transliteration": "Kuliyalarai enge ullathu?"},
            {"english": "How do I get there?", "tamil": "அங்கே எப்படி போவது?", "transliteration": "Ange eppadi pohvathu?"},
            {"english": "I need a taxi, please.", "tamil": "எனக்கு டாக்ஸி வேண்டும், தயவுசெய்ய.", "transliteration": "Enakku thaxi vaendum, dhayavu seiya."},
            {"english": "Take me to the hotel.", "tamil": "ஹோட்டலுக்கு கூட்டிச் செல்லுங்கள்.", "transliteration": "Hottalukku kootti sellungal."},
            {"english": "How much does it cost?", "tamil": "இது எவ்வளவு விலை?", "transliteration": "Ithu evvalavu vilai?"},
        ],
        "Restaurant Tamil": [
            {"english": "Can I see the menu?", "tamil": "மெனுவைப் பார்க்கலாமா?", "transliteration": "Menuvaip paarkkalaama?"},
            {"english": "This looks delicious!", "tamil": "இது ருசியாகத் தெரிகிறது!", "transliteration": "Ithu ruchiyaaga therigirathu!"},
            {"english": "Water, please.", "tamil": "தண்ணீர், தயவுசெய்ய.", "transliteration": "Thanneer, dhayavu seiya."},
            {"english": "Check, please.", "tamil": "பில், தயவுசெய்ய.", "transliteration": "Bill, dhayavu seiya."},
            {"english": "It was delicious!", "tamil": "மிகவும் ருசியாக இருந்தது!", "transliteration": "Migavum ruchiyaaga irunthathu!"},
        ],
        "Shopping Tamil": [
            {"english": "How much is this?", "tamil": "இது எவ்வளவு?", "transliteration": "Ithu evvalavu?"},
            {"english": "Can I try this on?", "tamil": "இதை முயற்சிக்கலாமா?", "transliteration": "Ithai muyarithiikkalaamaa?"},
            {"english": "Do you have a smaller size?", "tamil": "சிறிய அளவு உள்ளதா?", "transliteration": "Siriyas alavu ullatha?"},
            {"english": "I'll take this one.", "tamil": "இதை நான் எடுத்துக்கொள்கிறேன்.", "transliteration": "Ithai naan eduththukolligiraen."},
            {"english": "Can I pay by card?", "tamil": "கார்டு மூலம் செலுத்தலாமா?", "transliteration": "Card moolam selluthalaamo?"},
        ],
        "Emergency Tamil": [
            {"english": "Help me, please!", "tamil": "எனக்கு உதவி செய்யுங்கள்!", "transliteration": "Enakku uthavi seiyungal!"},
            {"english": "Call the police!", "tamil": "காவல்துறையை அழையுங்கள்!", "transliteration": "Kaavalthuraiyai azhaiyungal!"},
            {"english": "I need a doctor.", "tamil": "எனக்கு மருத்துவர் வேண்டும்.", "transliteration": "Enakku maruththuvar vaendum."},
            {"english": "Where is the hospital?", "tamil": "மருத்துவமனை எங்கே உள்ளது?", "transliteration": "Maruththuvamanai enge ullathu?"},
            {"english": "I'm lost, can you help?", "tamil": "நான் வழி தவறிவிட்டேன், உதவ முடியுமா?", "transliteration": "Naan vazhi thavari vittaeang, uthava mudiyumaa?"},
        ],
        "Family Terms": [
            {"english": "This is my mother.", "tamil": "இது என் தாய்.", "transliteration": "Ithu en thaai."},
            {"english": "This is my father.", "tamil": "இது என் தந்தை.", "transliteration": "Ithu en thanthai."},
            {"english": "I have an older brother.", "tamil": "எனக்கு அண்ணன் இருக்கிறார்.", "transliteration": "Enakku annan irukkiraar."},
            {"english": "I have a younger sister.", "tamil": "எனக்கு தங்கை இருக்கிறாள்.", "transliteration": "Enakku thangai irukkiraal."},
            {"english": "These are my parents.", "tamil": "இவர்கள் என் பெற்றோர்கள்.", "transliteration": "Ivargal en petrorhgal."},
        ],
        "Numbers Tamil": [
            {"english": "One, two, three.", "tamil": "ஒன்று, இரண்டு, மூன்று.", "transliteration": "Onru, irandu, moonru."},
            {"english": "Four, five, six.", "tamil": "நான்கு, ஐந்து, ஆறு.", "transliteration": "Naangu, ainthu, aaru."},
            {"english": "Seven, eight, nine, ten.", "tamil": "ஏழு, எட்டு, ஒன்பது, பத்து.", "transliteration": "Ezhu, ettu, onbadhu, pathu."},
            {"english": "What number is this?", "tamil": "இது எந்த எண்?", "transliteration": "Ithu endha en?"},
            {"english": "Give me two, please.", "tamil": "இரண்டு தாருங்கள், தயவுசெய்ய.", "transliteration": "Irandu thaarungal, dhayavu seiya."},
        ],
        "Time Tamil": [
            {"english": "What time is it?", "tamil": "இப்போது எவ்வளவு மணி?", "transliteration": "Ippoathu evvalavu mani?"},
            {"english": "It's three o'clock.", "tamil": "மூன்று மணி ஆகிவிட்டது.", "transliteration": "Moonru mani aahivittadhu."},
            {"english": "See you at noon.", "tamil": "நண்பகலில் சந்திப்போம்.", "transliteration": "Nanpagalil santhippom."},
            {"english": "I'll be there in five minutes.", "tamil": "ஐந்து நிமிடங்களில் வந்துவிடுகிறேன்.", "transliteration": "Ainthu nimidangalil vandhuvidugiraen."},
            {"english": "What day is today?", "tamil": "இன்று என்ன நாள்?", "transliteration": "Indru enna naal?"},
        ],
        "Motivation": [
            {"english": "Believe in yourself.", "tamil": "உங்கள் மீது நம்பிக்கை வையுங்கள்.", "transliteration": "Ungal meedhu nambikkai vaiyungal."},
            {"english": "You are capable of amazing things.", "tamil": "நீங்கள் அற்புதமான விஷயங்களைச் செய்ய முடியும்.", "transliteration": "Neengal arputhamaana vishayangalaich seyya mudiyaum."},
            {"english": "Dream big, start small.", "tamil": "பெரிய கனவு காணுங்கள், சிறியதில் தொடங்குங்கள்.", "transliteration": "Periya kanavu kaanungal, siriyathil thodangungal."},
            {"english": "Your future is created by your actions.", "tamil": "உங்கள் எதிர்காலம் உங்கள் செயல்களால் உருவாக்கப்படுகிறது.", "transliteration": "Ungal edhirkalam ungal seiyalalaal uruvaakkappadugirathu."},
            {"english": "Never give up on your dreams.", "tamil": "உங்கள் கனவுகளை ஒருபோதும் விடாதீர்கள்.", "transliteration": "Ungal kanavugalai orupodhum vidaatheergal."},
        ],
        "Love": [
            {"english": "Love yourself first.", "tamil": "முதலில் உங்களை நேசியுங்கள்.", "transliteration": "Mudhalil ungalai nesiyungal."},
            {"english": "Love makes everything possible.", "tamil": "அன்பு எல்லாவற்றையும் சாத்தியமாக்குகிறது.", "transliteration": "Anbu ellavatraiyum saathiyamaakkugirathu."},
            {"english": "You are loved more than you know.", "tamil": "நீங்கள் நினைப்பதை விட அதிகமாக நேசிக்கப்படுகிறீர்கள்.", "transliteration": "Neengal ninaippathai vida adhigamaaga nesikkappadugireergal."},
            {"english": "Love is the greatest power.", "tamil": "அன்பே மிகப்பெரிய சக்தி.", "transliteration": "Anbae migapperiya sakthi."},
            {"english": "Spread love everywhere you go.", "tamil": "நீங்கள் செல்லும் இடங்களிலெல்லாம் அன்பைப் பரப்புங்கள்.", "transliteration": "Neengal sellum idangalilellaam anbaip parappungal."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "tamil": "வெற்றி கடின உழைப்பிலிருந்து வருகிறது.", "transliteration": "Verri kadina ulaippilirundhu varugirathu."},
            {"english": "Keep going, you're getting there.", "tamil": "தொடர்ந்து செல்லுங்கள், நீங்கள் சென்று கொண்டிருக்கிறீர்கள்.", "transliteration": "Thodarndhu sellungal, neengal sendru kondirukkireergal."},
            {"english": "Every step counts toward success.", "tamil": "வெற்றிக்கு ஒவ்வொரு அடியும் முக்கியம்.", "transliteration": "Verrikku ovvoru adiyum mukkiyam."},
            {"english": "Your effort will pay off.", "tamil": "உங்கள் முயற்சி பலிக்கும்.", "transliteration": "Ungal muyarchi palikkum."},
            {"english": "Success is a journey, not a destination.", "tamil": "வெற்றி ஒரு பயணம், இலக்கு அல்ல.", "transliteration": "Verri oru payanam, ilakku alla."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "tamil": "அறிவு என்பது சக்தி.", "transliteration": "Arivu enbadhu sakthi."},
            {"english": "Learn from yesterday, live for today.", "tamil": "நேற்றிலிருந்து கற்றுக்கொள், இன்றைக்காக வாழ்.", "transliteration": "Nettrilirundhu katrukkoi, indraikkaaga vaazh."},
            {"english": "The wise learn from others' mistakes.", "tamil": "ஞானிகள் மற்றவர்களின் தவறுகளிலிருந்து கற்றுக்கொள்வார்கள்.", "transliteration": "Gnaanigal matravarhgalin thavargalilirundhu katrukkolvaargal."},
            {"english": "Experience is the best teacher.", "tamil": "அனுபவமே சிறந்த ஆசிரியர்.", "transliteration": "Anubavamae sirandha aasiriyar."},
            {"english": "Wisdom comes with age.", "tamil": "ஞானம் வயதுடன் வருகிறது.", "transliteration": "Gnaanam vayadudan varugirathu."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "tamil": "மகிழ்ச்சி என்பது ஒரு தேர்வு.", "transliteration": "Magizhchi enbadhu oru thaervu."},
            {"english": "Find joy in the little things.", "tamil": "சிறு விஷயங்களில் மகிழ்ச்சியைக் காணுங்கள்.", "transliteration": "Siru vishayangalil magizhchiyaik kaanungal."},
            {"english": "Your happiness matters most.", "tamil": "உங்கள் மகிழ்ச்சியே மிக முக்கியம்.", "transliteration": "Ungal magizhchiyae miga mukkiyam."},
            {"english": "Smile, it makes others happy.", "tamil": "புன்னகையுங்கள், இது மற்றவர்களை மகிழ்ச்சிக்குள்ளாக்கும்.", "transliteration": "Punnagaiyungal, idhu matravarhgalai magizhchikku llaakku."},
            {"english": "Happiness is contagious, spread it.", "tamil": "மகிழ்ச்சி பரவும், பரப்புங்கள்.", "transliteration": "Magizhchi paravum, parappungal."},
        ],
        "Self Improvement": [
            {"english": "Better today than yesterday.", "tamil": "நேற்றை விட இன்று மேம்பாடு.", "transliteration": "Netrae vida indru maempaadu."},
            {"english": "Small steps lead to big changes.", "tamil": "சிறு அடிகள் பெரிய மாற்றங்களுக்கு வழிவகுக்கும்.", "transliteration": "Siru adigal periya maatrangalukku vazhivakkum."},
            {"english": "Invest in yourself daily.", "tamil": "தினமும் உங்களில் முதலீடு செய்யுங்கள்.", "transliteration": "Thidhamum ungalil muthalaid seiyungal."},
            {"english": "Growth requires discomfort.", "tamil": "வளர்ச்சிக்கு சவால்கள் தேவை.", "transliteration": "Valarchikku savaigal thevai."},
            {"english": "Be your own competition.", "tamil": "உங்களுக்கு நீங்களே போட்டியாக இருங்கள்.", "transliteration": "Ungalukku neengalae poattiyaaga irungal."},
        ],
        "Gratitude": [
            {"english": "I am grateful for today.", "tamil": "இன்றைக்கு நான் நன்றி உடையவன்.", "transliteration": "Indraikku naan nandri udaiyavan."},
            {"english": "Thank you for everything.", "tamil": "எல்லாவற்றிற்கும் நன்றி.", "transliteration": "Ellavatraikum nandri."},
            {"english": "Gratitude turns what we have into enough.", "tamil": "நன்றி உணர்வு நமக்கு உள்ளதைப் போதுமாக்கும்.", "transliteration": "Nandri unarvu namakku ullathaip podhumaakku."},
            {"english": "Count your blessings daily.", "tamil": "தினமும் உங்கள் ஆசீர்வாதங்களை எண்ணுங்கள்.", "transliteration": "Thidhamum ungal aaseervaadangalai ennungal."},
            {"english": "A grateful heart is a happy heart.", "tamil": "நன்றி உள்ள இதயம் மகிழ்ச்சி உள்ள இதயம்.", "transliteration": "Nandri ulla idayam magizhchi ulla idayam."},
        ],
        "Friendship": [
            {"english": "Friends make life better.", "tamil": "நண்பர்கள் வாழ்க்கையை மேம்படுத்துகிறார்கள்.", "transliteration": "Nanbargal vaazhkkayae maemppaduththugiraargal."},
            {"english": "A true friend is always there.", "tamil": "உண்மையான நண்பர் எப்போதும் இருப்பார்.", "transliteration": "Unmaiyana nanbar eppodhum iruppaar."},
            {"english": "Friendship is a precious gift.", "tamil": "நட்பு என்பது விலைமதிப்பற்ற கொடை.", "transliteration": "Natpu enbadhu vilaimathippatra kodai."},
            {"english": "Good friends are like stars.", "tamil": "நல்ல நண்பர்கள் நட்சத்திரங்கள் போன்றவர்கள்.", "transliteration": "Nalla nanbargal nachatthirangal pondravaargal."},
            {"english": "Cherish your true friends.", "tamil": "உங்கள் உண்மையான நண்பர்களை விலை மதியுங்கள்.", "transliteration": "Ungal unmaiyana nanbargalai vilai madiyungal."},
        ],
        "Hope": [
            {"english": "Hope never dies.", "tamil": "நம்பிக்கை ஒருபோதும் சாவதில்லை.", "transliteration": "Nambikkai orupodhum saavadhillai."},
            {"english": "Tomorrow is a new beginning.", "tamil": "நாளை ஒரு புதிய தொடக்கம்.", "transliteration": "Naalai oru pudhiya thodakkam."},
            {"english": "Keep hope alive in your heart.", "tamil": "உங்கள் இதயத்தில் நம்பிக்கையை உயிர்ப்போடு வையுங்கள்.", "transliteration": "Ungal idhayatthil nambikkkaiyai uyirpodu vaiyungal."},
            {"english": "Hope is the light in darkness.", "tamil": "நம்பிக்கை இருளில் ஒளி.", "transliteration": "Nambikkai irulil oli."},
            {"english": "Where there's hope, there's life.", "tamil": "நம்பிக்கை இருக்கும் இடத்தில் வாழ்க்கை உண்டு.", "transliteration": "Nambikkai irukkum idathil vaazhkkai undu."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "tamil": "இன்று ஏதாவது அழகானதை உருவாக்குங்கள்.", "transliteration": "Indru aedhaavudhu azhagaanathai uruvaakkungal."},
            {"english": "Your creativity is unique.", "tamil": "உங்கள் படைப்பாற்றல் தனித்துவமானது.", "transliteration": "Ungal padaipparral thanithuvamaanarthu."},
            {"english": "Let your imagination run wild.", "tamil": "உங்கள் கற்பனையை சுதந்திரமாக விடுங்கள்.", "transliteration": "Ungal karpaniyai sudhandiramaga vidungal."},
            {"english": "Art comes from the heart.", "tamil": "கலை இதயத்திலிருந்து வருகிறது.", "transliteration": "Kalai idhayathilirundhu varugiradhu."},
            {"english": "Every day is a canvas.", "tamil": "ஒவ்வொரு நாளும் ஒரு கேன்வாஸ்.", "transliteration": "Ovvoru naalum oru canvas."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "tamil": "உங்களுக்குள் அமைதியைக் காணுங்கள்.", "transliteration": "Ungalukkul amaidhiyaik kaanungal."},
            {"english": "Calm mind, happy heart.", "tamil": "அமைதியான மனம், மகிழ்ச்சியான இதயம்.", "transliteration": "Amaidiyaana manam, magizhchiyaana idayam."},
            {"english": "Peace begins with a smile.", "tamil": "அமைதி ஒரு புன்னகையுடன் தொடங்குகிறது.", "transliteration": "Amaidhi oru punnagayudan thodangugiradhu."},
            {"english": "Breathe deeply, let go.", "tamil": "ஆழமாக மூச்செடுத்து, விடுங்கள்.", "transliteration": "Aazhamaaga mooschetta, vidungal."},
            {"english": "Your inner peace is precious.", "tamil": "உங்கள் உள் அமைதி விலைமதிப்பற்றது.", "transliteration": "Ungal ul amaidhi vilaimathippatrathu."},
        ],
        "Confidence": [
            {"english": "Believe you can, you're right.", "tamil": "நீங்கள் முடியும் என்று நம்புங்கள், நீங்கள் சரியானவர்கள்.", "transliteration": "Neengal mudiyaum endru nambungal, neengal thariyaanavaargal."},
            {"english": "You are stronger than you think.", "tamil": "நீங்கள் நினைப்பதை விட வலிமையாக இருக்கிறீர்கள்.", "transliteration": "Neengal ninaippathai vida valimaiyaaga irukkireergal."},
            {"english": "Confidence comes from within.", "tamil": "நம்பிக்கை உள்ளிருந்து வருகிறது.", "transliteration": "Nambikkai ullirundhu varugiradhu."},
            {"english": "Stand tall, be proud.", "tamil": "நேராக நில்லுங்கள், பெருமையாக இருங்கள்.", "transliteration": "Naeraaga nillungal, perumaiyaaga irungal."},
            {"english": "You have what it takes.", "tamil": "உங்களுக்குத் தேவையானது உங்களுக்கு உள்ளது.", "transliteration": "Ungalukku thevaiyaanadhu ungalukku ullaadhu."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep going.", "tamil": "ஒருபோதும் விடாதீர்கள், தொடர்ந்து செல்லுங்கள்.", "transliteration": "Orupodhum vidaatheergal, thodarndhu sellungal."},
            {"english": "Persistence beats talent.", "tamil": "விடாமுயற்சி மேதைமையை வெல்கிறது.", "transliteration": "Vidaamuyarchi maedhaimaiyai velgiradhu."},
            {"english": "Fall seven times, rise eight.", "tamil": "ஏழுமுறை விழுந்தால் எட்டுமுறை எழுந்திரு.", "transliteration": "Ezhu murai vizhundhaal ettu murai ezhundhiru."},
            {"english": "Hard work pays off eventually.", "tamil": "கடின உழைப்பு இறுதியில் பலிக்கும்.", "transliteration": "Kadina ulaippu idthiyil palikkum."},
            {"english": "Stay the course, don't quit.", "tamil": "பாதையில் தொடருங்கள், விட்டுவிடாதீர்கள்.", "transliteration": "Paathaiyil thodarungal, vittuvidaatheergal."},
        ],
        "Inspiration": [
            {"english": "Let inspiration guide you.", "tamil": "உத்வேகம் உங்களை வழிநடத்தட்டும்.", "transliteration": "Udhvegam ungalai vazhinatathattum."},
            {"english": "Be the inspiration others need.", "tamil": "மற்றவர்களுக்குத் தேவையான உத்வேகமாக இருங்கள்.", "transliteration": "Matravaargalukku thevaiyaana udhvegamaga irungal."},
            {"english": "Inspire by example, not words.", "tamil": "வார்த்தைகளால் அல்ல, முன்னுதாரணத்தால் உத்வேகமூட்டுங்கள்.", "transliteration": "Vaarththaihgalaal alla, munnuhdhaaranathaal udhvegamootungal."},
            {"english": "Your story inspires others.", "tamil": "உங்கள் கதை மற்றவர்களுக்கு உத்வேகம் அளிக்கிறது.", "transliteration": "Ungal kadhai matravaargalukku udhvegam alikkiradhu."},
            {"english": "Find inspiration in nature.", "tamil": "இயற்கையில் உத்வேகத்தைக் காணுங்கள்.", "transliteration": "Iyarkaiyil udhvegaththai kkaanungal."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "tamil": "தினமும் நேர்மறையைத் தேர்ந்தெடுங்கள்.", "transliteration": "Thidhamum naermayai thaerantheidungal."},
            {"english": "Positive thoughts create positive life.", "tamil": "நேர்மறை எண்ணங்கள் நேர்மறை வாழ்க்கையை உருவாக்குகின்றன.", "transliteration": "Naermai ennamgal naermai vaazhkkaiyai uruvaakku kinrana."},
            {"english": "Surround yourself with positivity.", "tamil": "உங்களை நேர்மறையால் சூழ்ந்து கொள்ளுங்கள்.", "transliteration": "Ungalai naermaiyaal soozhnthu kollungal."},
            {"english": "Every day is a fresh start.", "tamil": "ஒவ்வொரு நாளும் ஒரு புதிய தொடக்கம்.", "transliteration": "Ovvoru naalum oru pudhiya thodakkam."},
            {"english": "Live life with a positive heart.", "tamil": "நேர்மறை இதயத்துடன் வாழுங்கள்.", "transliteration": "Naermai idhayathudan vaazhunggal."},
        ],
        "Courage": [
            {"english": "Be brave, take the leap.", "tamil": "தைரியமாக இருங்கள், முன்னேறுங்கள்.", "transliteration": "Thairiyamaaga irungal, munnaerunggal."},
            {"english": "Courage is not absence of fear.", "tamil": "தைரியம் என்பது பயம் இன்மை அல்ல.", "transliteration": "Thairiyam enbadhu bayam inmai alla."},
            {"english": "Face your fears with courage.", "tamil": "தைரியத்துடன் உங்கள் பயங்களைச் சந்தியுங்கள்.", "transliteration": "Thairiyathudan ungal bayangalaich sandhiyungal."},
            {"english": "Brave hearts change the world.", "tamil": "தைரியமான இதயங்கள் உலகை மாற்றுகின்றன.", "transliteration": "Thairiyaamana idhayangal ulagai maattrukinrana."},
            {"english": "Courage grows with use.", "tamil": "தைரியம் பயன்படுத்தும்போது வளரும்.", "transliteration": "Thairiyam payanpaduththumpodhu valarum."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "tamil": "நீங்கள் சந்திக்கும் ஒவ்வொருவரிடமும் கனிவாக இருங்கள்.", "transliteration": "Neengal santhikkum ovvoruvaridamum kaniyaaha irungal."},
            {"english": "Kindness costs nothing, means everything.", "tamil": "கனிவுக்கு விலை இல்லை, ஆனால் அது எல்லாமே.", "transliteration": "Kaniukku vilai illai, aanaal adhu ellame."},
            {"english": "A kind word warms the heart.", "tamil": "கனிவான வார்த்தை இதயத்தை வெப்பப்படுத்துகிறது.", "transliteration": "Kaniyaana vaarththai idhayathai veppappaduththugiradhu."},
            {"english": "Spread kindness wherever you go.", "tamil": "நீங்கள் செல்லும் இடங்களிலெல்லாம் கனிவைப் பரப்புங்கள்.", "transliteration": "Neengal sellum idangalilellaam kanivaip parappungal."},
            {"english": "Kindness makes the world better.", "tamil": "கனிவு உலகை மேம்படுத்துகிறது.", "transliteration": "Kanivu ulagai maemppaduththugiradhu."},
        ],
        "Patience": [
            {"english": "Good things come to those who wait.", "tamil": "காத்திருப்பவர்களுக்கு நல்ல விஷயங்கள் வரும்.", "transliteration": "Kaaithiruppavargalukku nalla vishayangal varum."},
            {"english": "Patience is a virtue.", "tamil": "பொறுமை ஒரு நற்குணம்.", "transliteration": "Porumai oru nargunam."},
            {"english": "Take your time, don't rush.", "tamil": "உங்கள் நேரத்தை எடுத்துக்கொள்ளுங்கள், அவசரப்படாதீர்கள்.", "transliteration": "Ungal naerathei eduththukollungal, avasarappadaatheergal."},
            {"english": "Patience brings peace of mind.", "tamil": "பொறுமை மன அமைதியைத் தருகிறது.", "transliteration": "Porumai mana amaithiyai tharugiradhu."},
            {"english": "Wait patiently, trust the process.", "tamil": "பொறுமையாகக் காத்திருங்கள், செயல்முறையை நம்புங்கள்.", "transliteration": "Porumaiyaaga kaaththirungal, seialmuraiyai nambungal."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "tamil": "மன்னித்து உங்களை விடுவித்துக் கொள்ளுங்கள்.", "transliteration": "Mannithu ungalai viduviththu kollungal."},
            {"english": "Forgiveness is a gift to yourself.", "tamil": "மன்னிப்பு உங்களுக்கு நீங்களே கொடுக்கும் கொடை.", "transliteration": "Mannippu ungalukku neengalae kodukkum kodai."},
            {"english": "Let go of grudges, find peace.", "tamil": "பகைமையை விடுங்கள், அமைதியைக் காணுங்கள்.", "transliteration": "Pakaimaiyai vidungal, amaithiyai kkaanungal."},
            {"english": "To err is human, to forgive divine.", "tamil": "தவறு செய்வது மனித இயல்பு, மன்னிப்பது தெய்வீகம்.", "transliteration": "Thavaru seivadhu manitha iyalbu, mannippadhu theyvikam."},
            {"english": "Forgiveness heals all wounds.", "tamil": "மன்னிப்பு அனைத்து காயங்களையும் ஆற்றுகிறது.", "transliteration": "Mannippu anaitthu kaayangalaiyum aatrugiradhu."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "tamil": "நீங்கள் அறிவதை விட வலிமையாக இருக்கிறீர்கள்.", "transliteration": "Neengal arivathai vida valimaiyaaga irukkireergal."},
            {"english": "Strength comes from within.", "tamil": "வலிமை உள்ளிருந்து வருகிறது.", "transliteration": "Valimai ullirundhu varugiradhu."},
            {"english": "Your struggles develop your strength.", "tamil": "உங்கள் போராட்டங்கள் உங்கள் வலிமையை வளர்க்கின்றன.", "transliteration": "Ungal pooraatangal ungal valimaiyai valarkkinrana"},
            {"english": "Be strong, stay steady.", "tamil": "வலிமையாக இருங்கள், உறுதியாக இருங்கள்.", "transliteration": "Valimaiyaaga irungal, uthiyaaga irungal."},
            {"english": "Inner strength conquers all.", "tamil": "உள் வலிமை அனைத்தையும் வெல்கிறது.", "transliteration": "Ull valimai anaittaiyum velgiradhu."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "tamil": "ஒவ்வொரு கணத்திலும் ஆனந்தத்தைக் காணுங்கள்.", "transliteration": "Ovvoru kanathilum aanandhathei kkaanungal."},
            {"english": "Joy is contagious, spread it.", "tamil": "ஆனந்தம் பரவும், பரப்புங்கள்.", "transliteration": "Aanandham paravum, parappungal."},
            {"english": "Let joy fill your heart today.", "tamil": "இன்று ஆனந்தம் உங்கள் இதயத்தை நிரப்பட்டும்.", "transliteration": "Indru aanandham ungal idhayathai nirappattum."},
            {"english": "Choose joy over worry.", "tamil": "கவலைக்கு பதிலாக ஆனந்தத்தைத் தேர்ந்தெடுங்கள்.", "transliteration": "Kavalaiku pathilaaga aanandhathei thaerantheidungal."},
            {"english": "Joy is the simplest form of gratitude.", "tamil": "ஆனந்தம் என்பது நன்றியுணர்வின் எளிய வடிவம்.", "transliteration": "Aanandham enbadhu nandriyunarvin eliya vadivam."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "tamil": "உங்கள் வாழ்க்கையில் சமநிலையைக் காணுங்கள்.", "transliteration": "Ungal vaazhkkaivl samanilaiyai kkaanungal."},
            {"english": "Balance is the key to happiness.", "tamil": "சமநிலையே மகிழ்ச்சிக்கான வழி.", "transliteration": "Samanilaiyae magizhchikkaarana vazhi."},
            {"english": "Work hard, rest well.", "tamil": "கடினமாக உழையுங்கள், நன்றாக ஓய்வெடுயுங்கள்.", "transliteration": "Kadinamaaga ulaiyungal, nandraaga oiyrv eduiyungal."},
            {"english": "A balanced life is a peaceful life.", "tamil": "சமநிலையான வாழ்க்கையே அமைதியான வாழ்க்கை.", "transliteration": "Samanilaiyaana vaazhkkaiyae amaithiyaana vaazhkkai."},
            {"english": "Prioritize what matters most.", "tamil": "மிக முக்கியமானதை முன்னுரிமை கொடுங்கள்.", "transliteration": "Miga mukkiyamaanathai munurimai kodungal."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "tamil": "வளர்ச்சி உங்கள் ஆறுதல் மண்டலத்திற்கு வெளியே நிகழ்கிறது.", "transliteration": "Valarchi ungal aaruthal mandalathirku veliye nigazhkiradhu."},
            {"english": "Embrace change, grow stronger.", "tamil": "மாற்றத்தை ஏற்றுக்கொள்ளுங்கள், வலிமையாக வளருங்கள்.", "transliteration": "Maattrathai aetrukkollungal, valimaiyaaga valaerunggal."},
            {"english": "Every challenge is a growth opportunity.", "tamil": "ஒவ்வொரு சவாலும் வளர்ச்சிக்கான வாய்ப்பு.", "transliteration": "Ovvoru savaalum valarchikkaaana vaayppu."},
            {"english": "Grow through what you go through.", "tamil": "நீங்கள் அனுபவிப்பவற்றின் மூலம் வளருங்கள்.", "transliteration": "Neengal anubavippavattrin moolam valaerunggal."},
            {"english": "Personal growth is a lifelong journey.", "tamil": "தனிப்பட்ட வளர்ச்சி வாழ்நாள் பயணம்.", "transliteration": "Thanipatta valarchi vaazhnaal payanam."},
        ],
        "Purpose": [
            {"english": "Find your purpose, live it.", "tamil": "உங்கள் நோக்கத்தைக் கண்டுபிடியுங்கள், அதை வாழுங்கள்.", "transliteration": "Ungal nokkaththai kandupidiyungal, adhai vaazhunggal."},
            {"english": "Purpose gives life meaning.", "tamil": "நோக்கம் வாழ்க்கைக்கு அர்த்தத்தைக் கொடுக்கிறது.", "transliteration": "Nokkam vaazhkkaikku arthathaik kodukkugiradhu."},
            {"english": "Live with purpose and passion.", "tamil": "நோக்கத்துடனும் ஆர்வத்துடனும் வாழுங்கள்.", "transliteration": "Nokkatthudanum aarvatthudanum vaazhunggal."},
            {"english": "Your purpose is your calling.", "tamil": "உங்கள் நோக்கமே உங்கள் அழைப்பு.", "transliteration": "Ungal nokkamae ungal azhaippu."},
            {"english": "Discover purpose in everyday moments.", "tamil": "அன்றாட நிகழ்வுகளில் நோக்கத்தைக் கண்டுபிடியுங்கள்.", "transliteration": "Andraada nigazhuvugalil nokkathai kandupidiyungal."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "tamil": "இந்த நிமிஷத்தில் இருங்கள்.", "transliteration": "Indha nimishathil irungal."},
            {"english": "Mindfulness brings inner peace.", "tamil": "நுண்ணிய அறிவு உள் அமைதியைத் தருகிறது.", "transliteration": "Nunnlya arivu ull amaidhiyai tharugiradhu."},
            {"english": "Breathe deeply, stay mindful.", "tamil": "ஆழமாக மூச்செடுத்து, விழிப்புடன் இருங்கள்.", "transliteration": "Aazhamaaga mooschetta, vizhuppudan irungal."},
            {"english": "The present moment is all we have.", "tamil": "நிகழ் கணமே நமக்கு உள்ளது.", "transliteration": "Nigazh kanamae namakku ullaadhu."},
            {"english": "Practice mindfulness daily.", "tamil": "தினமும் நுண்ணிய அறிவைப் பயிற்சி செய்யுங்கள்.", "transliteration": "Thidhamum nunnlya arivaip prayirchi seiyungal."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]
    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


async def generate_audio_with_retries(text: str, voice: str, output_path: str, max_retries: int = 3):
    """Generate audio with retry logic for TTS failures"""
    import asyncio
    for attempt in range(1, max_retries + 1):
        success = await generate_single_audio(text, voice, output_path)
        if success:
            if Path(output_path).exists() and Path(output_path).stat().st_size > 100:
                return True
            else:
                print(f"    TTS file too small or missing, retrying ({attempt}/{max_retries})...")
                await asyncio.sleep(2 * attempt)
                continue
        else:
            if attempt < max_retries:
                wait = 2 * attempt
                print(f"    TTS retry {attempt}/{max_retries} in {wait}s...")
                await asyncio.sleep(wait)
            else:
                print(f"    TTS failed after {max_retries} attempts, using silence fallback")
                return False
    return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        tamil_file = output_dir / f"tamil_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    TA: {phrase['tamil']}")

        # Generate English audio
        en_success = asyncio.run(generate_audio_with_retries(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    - English: {english_file.name}")
        else:
            print(f"    - English: SILENCE FALLBACK (TTS failed)")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Tamil audio
        ta_success = asyncio.run(generate_audio_with_retries(phrase["tamil"], TAMIL_VOICE, str(tamil_file)))
        if ta_success:
            print(f"    - Tamil: {tamil_file.name}")
        else:
            print(f"    - Tamil: SILENCE FALLBACK (TTS failed)")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(tamil_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        ta_duration = get_audio_duration(str(tamil_file))

        # Add pause between English and Tamil
        pause_between = 0.5
        total_duration = en_duration + pause_between + ta_duration

        print(f"    Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + TA: {ta_duration:.2f}s)")

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(tamil_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{tamil_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "tamil": str(tamil_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "ta_duration": ta_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

NOTO_TAMIL_FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosanstamil/NotoSansTamil%5BBDU%5D.ttf"
FONTS_DIR = BASE_DIR / "fonts"


def ensure_tamil_font():
    """Download NotoSansTamil font if not available locally"""
    font_file = FONTS_DIR / "NotoSansTamil-Bold.ttf"
    if font_file.exists():
        return str(font_file)

    FONTS_DIR.mkdir(exist_ok=True)

    try:
        import urllib.request
        print("[font] Downloading NotoSansTamil font (Tamil script support)...")
        urllib.request.urlretrieve(NOTO_TAMIL_FONT_URL, str(font_file))
        print(f"[font] Downloaded: {font_file}")
        return str(font_file)
    except Exception as e:
        print(f"[font] Download failed: {e}")
        alt_url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Bold.ttf"
        try:
            import urllib.request
            urllib.request.urlretrieve(alt_url, str(font_file))
            print(f"[font] Downloaded from alternate: {font_file}")
            return str(font_file)
        except Exception as e2:
            print(f"[font] Alternate download also failed: {e2}")
    return None


def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    category_colors = {
        "Greetings": [(70, 130, 180), (255, 140, 0), (255, 255, 0), (255, 99, 71)],
        "Basic Phrases": [(60, 179, 113), (255, 215, 0), (144, 238, 144), (255, 140, 0)],
        "Common Expressions": [(138, 43, 226), (255, 20, 147), (75, 0, 130), (255, 105, 180)],
        "Travel Tamil": [(0, 191, 255), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Restaurant Tamil": [(255, 69, 0), (255, 215, 0), (220, 20, 60), (255, 140, 0)],
        "Shopping Tamil": [(255, 105, 180), (0, 100, 80), (255, 192, 203), (0, 200, 160)],
        "Emergency Tamil": [(255, 0, 0), (139, 0, 0), (255, 69, 0), (220, 20, 60)],
        "Family Terms": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],
        "Numbers Tamil": [(255, 215, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],
        "Time Tamil": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],
        "Love": [(255, 0, 100), (139, 0, 0), (255, 105, 180), (255, 192, 203)],
        "Success": [(255, 215, 0), (0, 100, 0), (255, 140, 0), (34, 139, 34)],
        "Wisdom": [(0, 0, 139), (255, 215, 0), (70, 130, 180), (255, 255, 0)],
        "Happiness": [(255, 255, 0), (255, 0, 255), (255, 165, 0), (147, 112, 219)],
        "Self Improvement": [(0, 128, 0), (255, 215, 0), (0, 255, 0), (255, 140, 0)],
        "Gratitude": [(255, 127, 80), (75, 0, 130), (255, 160, 122), (138, 43, 226)],
        "Friendship": [(255, 192, 203), (0, 100, 80), (255, 105, 180), (0, 200, 160)],
        "Hope": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],
        "Creativity": [(255, 0, 127), (0, 0, 139), (255, 20, 147), (75, 0, 130)],
        "Inner Peace": [(135, 206, 235), (0, 0, 100), (176, 224, 230), (75, 0, 130)],
        "Confidence": [(255, 69, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],
        "Perseverance": [(139, 69, 19), (255, 215, 0), (160, 82, 45), (255, 140, 0)],
        "Inspiration": [(255, 0, 255), (75, 0, 130), (255, 20, 147), (0, 0, 139)],
        "Positive Life": [(50, 205, 50), (255, 0, 127), (144, 238, 144), (255, 20, 147)],
        "Courage": [(178, 34, 34), (255, 215, 0), (220, 20, 60), (255, 140, 0)],
        "Kindness": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],
        "Patience": [(34, 139, 34), (255, 255, 0), (60, 179, 113), (255, 215, 0)],
        "Forgiveness": [(230, 230, 250), (75, 0, 130), (216, 191, 216), (138, 43, 226)],
        "Strength": [(100, 100, 100), (255, 69, 0), (150, 150, 150), (255, 140, 0)],
        "Joy": [(255, 255, 0), (255, 0, 127), (255, 215, 0), (147, 112, 219)],
        "Balance": [(60, 179, 113), (138, 43, 226), (152, 251, 152), (75, 0, 130)],
        "Growth": [(0, 100, 0), (255, 215, 0), (34, 139, 34), (255, 140, 0)],
        "Purpose": [(75, 0, 130), (255, 215, 0), (138, 43, 226), (255, 140, 0)],
        "Mindfulness": [(210, 180, 140), (75, 0, 130), (245, 245, 220), (138, 43, 226)],
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def _find_tamil_font_file():
    """Find the best Tamil font file path for HarfBuzz rendering"""
    candidates = [
        str(FONTS_DIR / "NotoSansTamil-Bold.ttf"),
        str(FONTS_DIR / "NotoSansTamil-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTamil-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/latha.ttf",
        "C:/Windows/Fonts/mangal.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path

    for search_dir in ["/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts"]:
        if not Path(search_dir).exists():
            continue
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                fname_lower = fname.lower()
                if any(t.lower() in fname_lower for t in ["notosanstamil", "nirmala", "latha", "mangal"]):
                    return str(Path(root) / fname)

    return None


def _render_text_harfbuzz(text, font_path, font_size, fill_color, stroke_color=None, stroke_width=0):
    """Render Tamil text with proper HarfBuzz shaping and FreeType rasterization.
    Returns a PIL Image with the rendered text on transparent background."""
    import uharfbuzz as hb
    import freetype as ft
    from PIL import Image, ImageDraw, ImageChops

    blob = hb.Blob.from_file_path(font_path)
    hb_face = hb.Face(blob)
    hb_font = hb.Font(hb_face)
    hb_font.scale = (font_size * 64, font_size * 64)

    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(hb_font, buffer)

    infos = buffer.glyph_infos
    positions = buffer.glyph_positions

    ft_face = ft.Face(font_path)
    ft_face.set_char_size(font_size * 64)

    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    x_cursor = 0.0
    y_cursor = 0.0
    glyph_metrics = []

    for info, pos in zip(infos, positions):
        ft_face.load_glyph(info.codepoint)
        bitmap = ft_face.glyph.bitmap
        bitmap_left = ft_face.glyph.bitmap_left
        bitmap_top = ft_face.glyph.bitmap_top
        x_off = pos.x_offset / 64.0
        y_off = pos.y_offset / 64.0
        x_adv = pos.x_advance / 64.0

        px = x_cursor + x_off + bitmap_left
        py = y_cursor + y_off - bitmap_top

        if bitmap.width > 0 and bitmap.rows > 0:
            min_x = min(min_x, px - stroke_width)
            min_y = min(min_y, py - stroke_width)
            max_x = max(max_x, px + bitmap.width + stroke_width)
            max_y = max(max_y, py + bitmap.rows + stroke_width)

        glyph_metrics.append({
            'codepoint': info.codepoint,
            'x': px, 'y': py,
            'width': bitmap.width, 'height': bitmap.rows,
            'x_advance': x_adv,
        })
        x_cursor += x_adv

    if min_x == float('inf'):
        total_width = max(x_cursor, 50)
        total_height = int(font_size * 1.5)
        min_x = 0
        min_y = 0
    else:
        total_width = max(max_x - min_x + stroke_width * 2, x_cursor + stroke_width * 2)
        total_height = max_y - min_y + stroke_width * 2

    total_width = int(total_width) + stroke_width * 2 + 4
    total_height = int(total_height) + stroke_width * 2 + 4

    img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

    def _draw_glyphs(target_img, color):
        draw = ImageDraw.Draw(target_img)
        for gm in glyph_metrics:
            ft_face.load_glyph(gm['codepoint'])
            bitmap = ft_face.glyph.bitmap
            if bitmap.width > 0 and bitmap.rows > 0:
                glyph_img = Image.frombytes('L', (bitmap.width, bitmap.rows), bytes(bitmap.buffer))
                paste_x = int(gm['x'] - min_x + stroke_width)
                paste_y = int(gm['y'] - min_y + stroke_width)
                if color[-1] == 255:
                    colored_glyph = Image.new('RGBA', glyph_img.size, color)
                    colored_glyph.putalpha(glyph_img)
                    target_img.paste(colored_glyph, (paste_x, paste_y), glyph_img)
                else:
                    blended = Image.new('RGBA', glyph_img.size, color)
                    mask = glyph_img.point(lambda p: min(255, int(p * color[-1] / 255)))
                    blended.putalpha(mask)
                    target_img.paste(blended, (paste_x, paste_y), blended)

    if stroke_width > 0 and stroke_color:
        stroke_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx * dx + dy * dy <= stroke_width * stroke_width + 1:
                    shifted = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
                    _draw_glyphs(shifted, stroke_color)
                    stroke_img = Image.alpha_composite(stroke_img, ImageChops.offset(shifted, dx, dy))
        img = Image.alpha_composite(img, stroke_img)

    fill_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    _draw_glyphs(fill_img, fill_color)
    img = Image.alpha_composite(img, fill_img)

    return img, int(x_cursor)


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageChops
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    downloaded_font = ensure_tamil_font()

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # English text fonts (bold, professional)
    english_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    tamil_font_paths = [
        str(FONTS_DIR / "NotoSansTamil-Bold.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTamil-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansTamil-Regular.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/nirmala.ttf",
        "C:/Windows/Fonts/latha.ttf",
        "C:/Windows/Fonts/mangal.ttf",
    ]

    def load_font(font_paths, size):
        """Load font with fallback - searches directories if direct paths fail"""
        for font_path in font_paths:
            try:
                f = ImageFont.truetype(font_path, size)
                test_bbox = f.getbbox("தமிழ்")
                if test_bbox[2] - test_bbox[0] > size * 0.5:
                    return f
            except (IOError, OSError):
                continue

        font_search_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "C:/Windows/Fonts",
        ]
        tamil_font_names = [
            "NotoSansTamil-Bold.ttf", "NotoSansTamil-Regular.ttf",
            "NotoSansTamil-Bold.ttc", "NotoSansTamil-Regular.ttc",
            "Nirmala.ttc", "latha.ttf", "mangal.ttf", "latha.ttf",
        ]

        for search_dir in font_search_dirs:
            if not Path(search_dir).exists():
                continue
            for root, dirs, files in os.walk(search_dir):
                for fname in files:
                    fname_lower = fname.lower()
                    if any(t.lower() in fname_lower for t in tamil_font_names):
                        try:
                            f = ImageFont.truetype(str(Path(root) / fname), size)
                            test_bbox = f.getbbox("தமிழ்")
                            if test_bbox[2] - test_bbox[0] > size * 0.5:
                                print(f"  [font] Found Tamil font: {fname}")
                                return f
                        except (IOError, OSError):
                            continue

        print("  [WARNING] No Tamil-capable font found! Tamil text may not render.")
        return ImageFont.load_default()

    # English text fonts (bold, professional)
    font_category = load_font(english_font_paths, 60)
    font_large = load_font(english_font_paths, 85)
    font_branding = load_font(english_font_paths, 52)

    # Tamil text fonts (supports Tamil characters, bold)
    font_tamil = load_font(tamil_font_paths, 65)

    # Transliteration fonts - BOLD and LARGER for better visibility
    font_transliteration = load_font(english_font_paths, 55)

    english = phrase_data.get("english", "")
    tamil = phrase_data.get("tamil", "")
    transliteration = phrase_data.get("transliteration", phrase_data.get("romaji", ""))

    def wrap_text(text, font, max_width):
        """Wrap text to fit within max_width - handles both English and Tamil"""
        lines = []

        is_tamil = any('\u0b80' <= c <= '\u0bff' for c in text)

        if is_tamil:
            words = text.split(' ')
            current_line = ''
            for word in words:
                test_line = (current_line + ' ' + word).strip() if current_line else word
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    width = bbox[2] - bbox[0]
                except Exception:
                    width = len(test_line) * 40
                if width <= max_width or not current_line:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            if not lines:
                lines = [text]
        else:
            words = text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

        return lines

    # Category at top
    category_text = category_english.upper()
    category_bbox = draw.textbbox((VIDEO_WIDTH // 2, 140), category_text, font=font_category, anchor="mm")
    padding = 25
    draw.rectangle(
        [(category_bbox[0] - padding, category_bbox[1] - padding),
         (category_bbox[2] + padding, category_bbox[3] + padding)],
        fill=(0, 0, 0, 200)
    )
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    # English text
    english_y = 470
    english_lines = wrap_text(english, font_large, VIDEO_WIDTH - 140)
    total_height = len(english_lines) * 95

    draw.rectangle(
        [(60, english_y - 55), (VIDEO_WIDTH - 60, english_y + total_height + 15)],
        fill=(20, 30, 80, 220)
    )

    for i, line in enumerate(english_lines):
        y_pos = english_y + (i * 95)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 255),
            font=font_large,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    # Tamil text - rendered with HarfBuzz for proper conjunct shaping
    tamil_y = english_y + total_height + 110
    tamil_font_path = _find_tamil_font_file()
    use_harfbuzz = tamil_font_path is not None

    if use_harfbuzz:
        try:
            import uharfbuzz as hb
            import freetype as ft
        except ImportError:
            use_harfbuzz = False
            print("  [WARNING] uharfbuzz/freetype not available, falling back to Pillow")

    if use_harfbuzz:
        max_tamil_width = VIDEO_WIDTH - 200
        tamil_words = tamil.split(' ')
        tamil_lines = []
        current_line_words = []

        for word in tamil_words:
            test_line = ' '.join(current_line_words + [word]) if current_line_words else word
            _, test_w = _render_text_harfbuzz(
                test_line, tamil_font_path, 65,
                fill_color=(255, 255, 0, 255)
            )
            single_word_w = 0
            if current_line_words:
                _, single_word_w = _render_text_harfbuzz(
                    word, tamil_font_path, 65,
                    fill_color=(255, 255, 0, 255)
                )

            if test_w <= max_tamil_width or not current_line_words:
                current_line_words.append(word)
            else:
                tamil_lines.append(' '.join(current_line_words))
                current_line_words = [word]

        if current_line_words:
            tamil_lines.append(' '.join(current_line_words))

        if not tamil_lines:
            tamil_lines = [tamil]

        line_spacing = 85
        total_height = len(tamil_lines) * line_spacing

        tamil_padding = 60
        draw.rectangle(
            [(50, tamil_y - tamil_padding), (VIDEO_WIDTH - 50, tamil_y + total_height + tamil_padding - 10)],
            fill=(80, 30, 30, 220)
        )

        for i, line in enumerate(tamil_lines):
            rendered, text_w = _render_text_harfbuzz(
                line, tamil_font_path, 65,
                fill_color=(255, 255, 0, 255),
                stroke_color=(0, 0, 0, 255),
                stroke_width=2
            )
            x_pos = (VIDEO_WIDTH - rendered.width) // 2
            y_pos = tamil_y + (i * line_spacing) - rendered.height // 2
            img.paste(rendered, (x_pos, y_pos), rendered)
    else:
        tamil_lines = wrap_text(tamil, font_tamil, VIDEO_WIDTH - 200)
        total_height = len(tamil_lines) * 75

        tamil_padding = 60
        draw.rectangle(
            [(50, tamil_y - tamil_padding), (VIDEO_WIDTH - 50, tamil_y + total_height + tamil_padding - 10)],
            fill=(80, 30, 30, 220)
        )

        for i, line in enumerate(tamil_lines):
            y_pos = tamil_y + (i * 75)
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                line,
                fill=(255, 255, 0),
                font=font_tamil,
                anchor="mm",
                stroke_width=3,
                stroke_fill=(0, 0, 0)
            )

    # Transliteration with FILLED BOX - BOLDER text for better visibility
    transliteration_y = tamil_y + total_height + 90
    transliteration_text = f"[{transliteration}]"
    transliteration_lines = wrap_text(transliteration_text, font_transliteration, VIDEO_WIDTH - 160)

    if transliteration_lines:
        transliteration_total_height = len(transliteration_lines) * 60
        draw.rectangle(
            [(70, transliteration_y - 25), (VIDEO_WIDTH - 70, transliteration_y + transliteration_total_height + 15)],
            fill=(40, 40, 40, 230)
        )

        for i, transliteration_line in enumerate(transliteration_lines):
            y_pos = transliteration_y + (i * 60)
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                transliteration_line,
                fill=(255, 255, 255),
                font=font_transliteration,
                anchor="mm",
                stroke_width=3,
                stroke_fill=(0, 0, 0, 220)
            )

    # Branding
    branding_y = VIDEO_HEIGHT - 100
    draw.rectangle(
        [(0, branding_y - 30), (VIDEO_WIDTH, branding_y + 50)],
        fill=(0, 0, 0, 180)
    )
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY TAMIL",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + TE: {audio_info.get('te_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        category_english = get_available_category()

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_TAMIL[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['tamil']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        print(f"  Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Tamil with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_tamil": CATEGORIES_TAMIL[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"REEL COMPLETE!")
    print(f"  {reel_dir}")
    print(f"  {output_video.name}")
    print(f"  Branding: Velocity Tamil")
    print(f"{'='*80}\n")

    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print("VELOCITY TAMIL - FACEBOOK REELS AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  - Natural pauses with commas (non-robotic TTS)")
    print("  - Perfect audio-video synchronization")
    print("  - Complete audio playback guaranteed")
    print("  - English category names (for learners)")
    print("  - Velocity Tamil branding at bottom")
    print("  - NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_TAMIL[cat]})")
    print(f"\nDAILY CAPACITY:")
    print(f"  4 reels per day = 20 unique phrases daily")
    print(f"  {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  Phrase history is PERMANENT (never deletes)")
    print(f"  AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)