"""VELOCITY TAMIL - language pack, brand and motion design constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY TAMIL"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "TAMIL"
HANDLE = "@velocitytamil"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {
    "code": "ta",
    "name": "Tamil",
    "native_name": "தமிழ்",
    "history_key": "tamil",
    "english_voice": "en-US-AvaNeural",
    "english_fallback_voice": "en-US-GuyNeural",
    "native_voice": "ta-IN-ValluvarNeural",
    "native_fallback_voice": "ta-IN-PallaviNeural",
    "native_engine": "edge",
    "native_lang_code": "ta",
    "english_rate": "-2%",
    "native_rate": "-6%",
    "english_pitch": "+0Hz",
    "native_pitch": "+0Hz",
    "native_label": "தமிழ்",
    "translit_label": "SAY IT LIKE",
    "greeting": "வணக்கம்!",
    "encouragement": "அருமை!",
    "rtl": False,
    "char_tiles": False,
    "script_font": "NotoSansTamil-Bold.ttf",
}
# ==== LANGUAGE PACK END ====

AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 4.0
OUTRO_DURATION = 5.2
EN_CARD_IN = 0.55
GAP_EN_NATIVE = 0.5
NATIVE_CARD_LEAD = 0.35
GAP_BEFORE_REPEAT = 0.8
TAIL_HOLD = 1.4
MAX_REEL_DURATION = 88.0

# ---------------------------------------------------------------- palette

INK = "#3C3C3C"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#A560E8"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

PALETTE = [GREEN, BLUE, PURPLE, ORANGE, RED, YELLOW, TEAL, PINK]

# ---------------------------------------------------------------- categories
# (english, native, icon, accent)

# ==== CATEGORY TABLE START ====
CATEGORY_TABLE = [
    ("Greetings", "வணக்கங்கள்", "hand", "#1CB0F6"),
    ("Basic Phrases", "அடிப்படை சொற்றொடர்கள்", "chat", "#58CC02"),
    ("Common Expressions", "பொதுவான வாக்கியங்கள்", "chat", "#1CB0F6"),
    ("Travel", "பயணம்", "plane", "#1CB0F6"),
    ("Restaurant", "உணவகம்", "fork", "#FF7A00"),
    ("Shopping", "ஷாப்பிங்", "bag", "#E056A0"),
    ("Emergency", "அவசரம்", "siren", "#FF4B4B"),
    ("Family Terms", "குடும்ப சொற்கள்", "heart", "#E056A0"),
    ("Numbers", "எண்கள்", "hash", "#A560E8"),
    ("Time", "நேரம்", "clock", "#00A889"),
    ("Motivation", "ஊக்கம்", "rocket", "#A560E8"),
    ("Love", "காதல்", "heart", "#FF4B4B"),
    ("Success", "வெற்றி", "trophy", "#F5A700"),
    ("Wisdom", "ஞானம்", "book", "#A560E8"),
    ("Happiness", "மகிழ்ச்சி", "smile", "#F5A700"),
    ("Self Improvement", "சுய மேம்பாடு", "leaf", "#58CC02"),
    ("Gratitude", "நன்றி", "heart", "#FF7A00"),
    ("Friendship", "நட்பு", "users", "#00A889"),
    ("Hope", "நம்பிக்கை", "sun", "#FF7A00"),
    ("Creativity", "படைப்பாற்றல்", "palette", "#E056A0"),
    ("Inner Peace", "உள் அமைதி", "lotus", "#00A889"),
    ("Confidence", "நம்பிக்கை", "shield", "#1CB0F6"),
    ("Perseverance", "விடாமுயற்சி", "mountain", "#FF7A00"),
    ("Inspiration", "உத்வேகம்", "sparkles", "#A560E8"),
    ("Positive Life", "நேர்மறை வாழ்க்கை", "sun", "#58CC02"),
    ("Courage", "தைரியம்", "shield", "#FF4B4B"),
    ("Kindness", "கனிவு", "heart", "#E056A0"),
    ("Patience", "பொறுமை", "hourglass", "#00A889"),
    ("Forgiveness", "மன்னிப்பு", "hands", "#FF7A00"),
    ("Strength", "வலிமை", "dumbbell", "#FF4B4B"),
    ("Joy", "ஆனந்தம்", "smile", "#F5A700"),
    ("Balance", "சமநிலை", "scale", "#00A889"),
    ("Growth", "வளர்ச்சி", "sprout", "#58CC02"),
    ("Purpose", "நோக்கம்", "target", "#A560E8"),
    ("Mindfulness", "நுண்ணிய அறிவு", "lotus", "#00A889"),
]
# ==== CATEGORY TABLE END ====

CATEGORIES = [c[0] for c in CATEGORY_TABLE]
CATEGORIES_NATIVE = {c[0]: c[1] for c in CATEGORY_TABLE}
CATEGORY_META = {c[0]: {"native": c[1], "icon": c[2], "accent": c[3]} for c in CATEGORY_TABLE}
MAX_RECENT_CATEGORIES = 25

# ==== HASHTAGS START ====
HASHTAGS = [
    "#learntamil",
    "#tamillessons",
    "#tamilforbeginners",
    "#languagelearning",
    "#tamilvocabulary",
    "#velocitytamil",
    "#dailytamil",
    "#tamil",
    "#learnlanguages",
    "#speaktamil",
    "#bilingual",
    "#languagetips",
]
# ==== HASHTAGS END ====
