"""AI phrase generation with permanent no-repeat history."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime

import requests

import config
from config import CATEGORIES, CATEGORIES_NATIVE, HISTORY_DIR, MAX_RECENT_CATEGORIES

PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"

PHRASE_KEY = config.LANGUAGE["history_key"]
LANGUAGE_NAME = config.LANGUAGE["name"]
NATIVE_NAME = config.LANGUAGE["native_name"]

# ==== FALLBACK PHRASES START ====
FALLBACK_PHRASES = [
    {"english": "Hello, nice to meet you.", "native": "வணக்கம், உங்களை சந்திப்பதில் மகிழ்ச்சி.", "transliteration": "Vanakkam, ungalaithi sandipapathil magizhchi."},
    {"english": "Good morning!", "native": "காலை வணக்கம்!", "transliteration": "Kalai vanakkam!"},
    {"english": "Good evening, how are you?", "native": "மாலை வணக்கம், எப்படி இருக்கிறீர்கள்?", "transliteration": "Malai vanakkam, eppadi irukkireergal?"},
    {"english": "See you tomorrow!", "native": "நாளை சந்திப்போம்!", "transliteration": "Naalai santhippom!"},
    {"english": "Goodbye, take care.", "native": "பிரியாவிடை, கவனமாக இருங்கள்.", "transliteration": "Priyaavidai, kavanamaga irungal."},
    {"english": "Thank you very much.", "native": "மிகவும் நன்றி.", "transliteration": "Migavum nandri."},
    {"english": "You're welcome.", "native": "நல்வரவு.", "transliteration": "Nalvaravu."},
    {"english": "I'm sorry, excuse me.", "native": "மன்னிக்கவும்.", "transliteration": "Mannikkavum."},
    {"english": "Yes, that's correct.", "native": "ஆம், அது சரியானது.", "transliteration": "Aam, athu thariyaanathu."},
    {"english": "No, I don't think so.", "native": "இல்லை, எனக்கு அப்படி தோன்றவில்லை.", "transliteration": "Illai, enakku appadi thondravailai."},
    {"english": "How are you doing today?", "native": "இன்று எப்படி இருக்கிறீர்கள்?", "transliteration": "Indru eppadi irukkireergal?"},
    {"english": "I'm fine, thank you.", "native": "நான் நன்றாக இருக்கிறேன், நன்றி.", "transliteration": "Naan nandraaga irukkirean, nandri."},
    {"english": "What's your name?", "native": "உங்கள் பெயர் என்ன?", "transliteration": "Ungal peyar enna?"},
    {"english": "My name is...", "native": "என் பெயர்...", "transliteration": "En peyar..."},
    {"english": "Nice to meet you too.", "native": "உங்களை சந்திப்பதில் மகிழ்ச்சி.", "transliteration": "Ungalaithi sandipapathil magizhchi."},
    {"english": "Where is the bathroom?", "native": "குளியலறை எங்கே உள்ளது?", "transliteration": "Kuliyalarai enge ullathu?"},
    {"english": "How do I get there?", "native": "அங்கே எப்படி போவது?", "transliteration": "Ange eppadi pohvathu?"},
    {"english": "I need a taxi, please.", "native": "எனக்கு டாக்ஸி வேண்டும், தயவுசெய்ய.", "transliteration": "Enakku thaxi vaendum, dhayavu seiya."},
    {"english": "Take me to the hotel.", "native": "ஹோட்டலுக்கு கூட்டிச் செல்லுங்கள்.", "transliteration": "Hottalukku kootti sellungal."},
    {"english": "How much does it cost?", "native": "இது எவ்வளவு விலை?", "transliteration": "Ithu evvalavu vilai?"},
    {"english": "Can I see the menu?", "native": "மெனுவைப் பார்க்கலாமா?", "transliteration": "Menuvaip paarkkalaama?"},
    {"english": "This looks delicious!", "native": "இது ருசியாகத் தெரிகிறது!", "transliteration": "Ithu ruchiyaaga therigirathu!"},
    {"english": "Water, please.", "native": "தண்ணீர், தயவுசெய்ய.", "transliteration": "Thanneer, dhayavu seiya."},
    {"english": "Check, please.", "native": "பில், தயவுசெய்ய.", "transliteration": "Bill, dhayavu seiya."},
    {"english": "It was delicious!", "native": "மிகவும் ருசியாக இருந்தது!", "transliteration": "Migavum ruchiyaaga irunthathu!"},
    {"english": "How much is this?", "native": "இது எவ்வளவு?", "transliteration": "Ithu evvalavu?"},
    {"english": "Can I try this on?", "native": "இதை முயற்சிக்கலாமா?", "transliteration": "Ithai muyarithiikkalaamaa?"},
    {"english": "Do you have a smaller size?", "native": "சிறிய அளவு உள்ளதா?", "transliteration": "Siriyas alavu ullatha?"},
    {"english": "I'll take this one.", "native": "இதை நான் எடுத்துக்கொள்கிறேன்.", "transliteration": "Ithai naan eduththukolligiraen."},
    {"english": "Can I pay by card?", "native": "கார்டு மூலம் செலுத்தலாமா?", "transliteration": "Card moolam selluthalaamo?"},
    {"english": "Help me, please!", "native": "எனக்கு உதவி செய்யுங்கள்!", "transliteration": "Enakku uthavi seiyungal!"},
    {"english": "Call the police!", "native": "காவல்துறையை அழையுங்கள்!", "transliteration": "Kaavalthuraiyai azhaiyungal!"},
    {"english": "I need a doctor.", "native": "எனக்கு மருத்துவர் வேண்டும்.", "transliteration": "Enakku maruththuvar vaendum."},
    {"english": "Where is the hospital?", "native": "மருத்துவமனை எங்கே உள்ளது?", "transliteration": "Maruththuvamanai enge ullathu?"},
    {"english": "I'm lost, can you help?", "native": "நான் வழி தவறிவிட்டேன், உதவ முடியுமா?", "transliteration": "Naan vazhi thavari vittaeang, uthava mudiyumaa?"},
    {"english": "This is my mother.", "native": "இது என் தாய்.", "transliteration": "Ithu en thaai."},
    {"english": "This is my father.", "native": "இது என் தந்தை.", "transliteration": "Ithu en thanthai."},
    {"english": "I have an older brother.", "native": "எனக்கு அண்ணன் இருக்கிறார்.", "transliteration": "Enakku annan irukkiraar."},
    {"english": "I have a younger sister.", "native": "எனக்கு தங்கை இருக்கிறாள்.", "transliteration": "Enakku thangai irukkiraal."},
    {"english": "These are my parents.", "native": "இவர்கள் என் பெற்றோர்கள்.", "transliteration": "Ivargal en petrorhgal."},
    {"english": "One, two, three.", "native": "ஒன்று, இரண்டு, மூன்று.", "transliteration": "Onru, irandu, moonru."},
    {"english": "Four, five, six.", "native": "நான்கு, ஐந்து, ஆறு.", "transliteration": "Naangu, ainthu, aaru."},
    {"english": "Seven, eight, nine, ten.", "native": "ஏழு, எட்டு, ஒன்பது, பத்து.", "transliteration": "Ezhu, ettu, onbadhu, pathu."},
    {"english": "What number is this?", "native": "இது எந்த எண்?", "transliteration": "Ithu endha en?"},
    {"english": "Give me two, please.", "native": "இரண்டு தாருங்கள், தயவுசெய்ய.", "transliteration": "Irandu thaarungal, dhayavu seiya."},
    {"english": "What time is it?", "native": "இப்போது எவ்வளவு மணி?", "transliteration": "Ippoathu evvalavu mani?"},
    {"english": "It's three o'clock.", "native": "மூன்று மணி ஆகிவிட்டது.", "transliteration": "Moonru mani aahivittadhu."},
    {"english": "See you at noon.", "native": "நண்பகலில் சந்திப்போம்.", "transliteration": "Nanpagalil santhippom."},
    {"english": "I'll be there in five minutes.", "native": "ஐந்து நிமிடங்களில் வந்துவிடுகிறேன்.", "transliteration": "Ainthu nimidangalil vandhuvidugiraen."},
    {"english": "What day is today?", "native": "இன்று என்ன நாள்?", "transliteration": "Indru enna naal?"},
    {"english": "Believe in yourself.", "native": "உங்கள் மீது நம்பிக்கை வையுங்கள்.", "transliteration": "Ungal meedhu nambikkai vaiyungal."},
    {"english": "You are capable of amazing things.", "native": "நீங்கள் அற்புதமான விஷயங்களைச் செய்ய முடியும்.", "transliteration": "Neengal arputhamaana vishayangalaich seyya mudiyaum."},
    {"english": "Dream big, start small.", "native": "பெரிய கனவு காணுங்கள், சிறியதில் தொடங்குங்கள்.", "transliteration": "Periya kanavu kaanungal, siriyathil thodangungal."},
    {"english": "Your future is created by your actions.", "native": "உங்கள் எதிர்காலம் உங்கள் செயல்களால் உருவாக்கப்படுகிறது.", "transliteration": "Ungal edhirkalam ungal seiyalalaal uruvaakkappadugirathu."},
    {"english": "Never give up on your dreams.", "native": "உங்கள் கனவுகளை ஒருபோதும் விடாதீர்கள்.", "transliteration": "Ungal kanavugalai orupodhum vidaatheergal."},
    {"english": "Love yourself first.", "native": "முதலில் உங்களை நேசியுங்கள்.", "transliteration": "Mudhalil ungalai nesiyungal."},
    {"english": "Love makes everything possible.", "native": "அன்பு எல்லாவற்றையும் சாத்தியமாக்குகிறது.", "transliteration": "Anbu ellavatraiyum saathiyamaakkugirathu."},
    {"english": "You are loved more than you know.", "native": "நீங்கள் நினைப்பதை விட அதிகமாக நேசிக்கப்படுகிறீர்கள்.", "transliteration": "Neengal ninaippathai vida adhigamaaga nesikkappadugireergal."},
    {"english": "Love is the greatest power.", "native": "அன்பே மிகப்பெரிய சக்தி.", "transliteration": "Anbae migapperiya sakthi."},
    {"english": "Spread love everywhere you go.", "native": "நீங்கள் செல்லும் இடங்களிலெல்லாம் அன்பைப் பரப்புங்கள்.", "transliteration": "Neengal sellum idangalilellaam anbaip parappungal."},
    {"english": "Success comes from hard work.", "native": "வெற்றி கடின உழைப்பிலிருந்து வருகிறது.", "transliteration": "Verri kadina ulaippilirundhu varugirathu."},
    {"english": "Keep going, you're getting there.", "native": "தொடர்ந்து செல்லுங்கள், நீங்கள் சென்று கொண்டிருக்கிறீர்கள்.", "transliteration": "Thodarndhu sellungal, neengal sendru kondirukkireergal."},
    {"english": "Every step counts toward success.", "native": "வெற்றிக்கு ஒவ்வொரு அடியும் முக்கியம்.", "transliteration": "Verrikku ovvoru adiyum mukkiyam."},
    {"english": "Your effort will pay off.", "native": "உங்கள் முயற்சி பலிக்கும்.", "transliteration": "Ungal muyarchi palikkum."},
    {"english": "Success is a journey, not a destination.", "native": "வெற்றி ஒரு பயணம், இலக்கு அல்ல.", "transliteration": "Verri oru payanam, ilakku alla."},
    {"english": "Knowledge is power.", "native": "அறிவு என்பது சக்தி.", "transliteration": "Arivu enbadhu sakthi."},
    {"english": "Learn from yesterday, live for today.", "native": "நேற்றிலிருந்து கற்றுக்கொள், இன்றைக்காக வாழ்.", "transliteration": "Nettrilirundhu katrukkoi, indraikkaaga vaazh."},
    {"english": "The wise learn from others' mistakes.", "native": "ஞானிகள் மற்றவர்களின் தவறுகளிலிருந்து கற்றுக்கொள்வார்கள்.", "transliteration": "Gnaanigal matravarhgalin thavargalilirundhu katrukkolvaargal."},
    {"english": "Experience is the best teacher.", "native": "அனுபவமே சிறந்த ஆசிரியர்.", "transliteration": "Anubavamae sirandha aasiriyar."},
    {"english": "Wisdom comes with age.", "native": "ஞானம் வயதுடன் வருகிறது.", "transliteration": "Gnaanam vayadudan varugirathu."},
    {"english": "Happiness is a choice.", "native": "மகிழ்ச்சி என்பது ஒரு தேர்வு.", "transliteration": "Magizhchi enbadhu oru thaervu."},
    {"english": "Find joy in the little things.", "native": "சிறு விஷயங்களில் மகிழ்ச்சியைக் காணுங்கள்.", "transliteration": "Siru vishayangalil magizhchiyaik kaanungal."},
    {"english": "Your happiness matters most.", "native": "உங்கள் மகிழ்ச்சியே மிக முக்கியம்.", "transliteration": "Ungal magizhchiyae miga mukkiyam."},
    {"english": "Smile, it makes others happy.", "native": "புன்னகையுங்கள், இது மற்றவர்களை மகிழ்ச்சிக்குள்ளாக்கும்.", "transliteration": "Punnagaiyungal, idhu matravarhgalai magizhchikku llaakku."},
    {"english": "Happiness is contagious, spread it.", "native": "மகிழ்ச்சி பரவும், பரப்புங்கள்.", "transliteration": "Magizhchi paravum, parappungal."},
    {"english": "Better today than yesterday.", "native": "நேற்றை விட இன்று மேம்பாடு.", "transliteration": "Netrae vida indru maempaadu."},
    {"english": "Small steps lead to big changes.", "native": "சிறு அடிகள் பெரிய மாற்றங்களுக்கு வழிவகுக்கும்.", "transliteration": "Siru adigal periya maatrangalukku vazhivakkum."},
    {"english": "Invest in yourself daily.", "native": "தினமும் உங்களில் முதலீடு செய்யுங்கள்.", "transliteration": "Thidhamum ungalil muthalaid seiyungal."},
    {"english": "Growth requires discomfort.", "native": "வளர்ச்சிக்கு சவால்கள் தேவை.", "transliteration": "Valarchikku savaigal thevai."},
    {"english": "Be your own competition.", "native": "உங்களுக்கு நீங்களே போட்டியாக இருங்கள்.", "transliteration": "Ungalukku neengalae poattiyaaga irungal."},
    {"english": "I am grateful for today.", "native": "இன்றைக்கு நான் நன்றி உடையவன்.", "transliteration": "Indraikku naan nandri udaiyavan."},
    {"english": "Thank you for everything.", "native": "எல்லாவற்றிற்கும் நன்றி.", "transliteration": "Ellavatraikum nandri."},
    {"english": "Gratitude turns what we have into enough.", "native": "நன்றி உணர்வு நமக்கு உள்ளதைப் போதுமாக்கும்.", "transliteration": "Nandri unarvu namakku ullathaip podhumaakku."},
    {"english": "Count your blessings daily.", "native": "தினமும் உங்கள் ஆசீர்வாதங்களை எண்ணுங்கள்.", "transliteration": "Thidhamum ungal aaseervaadangalai ennungal."},
    {"english": "A grateful heart is a happy heart.", "native": "நன்றி உள்ள இதயம் மகிழ்ச்சி உள்ள இதயம்.", "transliteration": "Nandri ulla idayam magizhchi ulla idayam."},
    {"english": "Friends make life better.", "native": "நண்பர்கள் வாழ்க்கையை மேம்படுத்துகிறார்கள்.", "transliteration": "Nanbargal vaazhkkayae maemppaduththugiraargal."},
    {"english": "A true friend is always there.", "native": "உண்மையான நண்பர் எப்போதும் இருப்பார்.", "transliteration": "Unmaiyana nanbar eppodhum iruppaar."},
    {"english": "Friendship is a precious gift.", "native": "நட்பு என்பது விலைமதிப்பற்ற கொடை.", "transliteration": "Natpu enbadhu vilaimathippatra kodai."},
    {"english": "Good friends are like stars.", "native": "நல்ல நண்பர்கள் நட்சத்திரங்கள் போன்றவர்கள்.", "transliteration": "Nalla nanbargal nachatthirangal pondravaargal."},
    {"english": "Cherish your true friends.", "native": "உங்கள் உண்மையான நண்பர்களை விலை மதியுங்கள்.", "transliteration": "Ungal unmaiyana nanbargalai vilai madiyungal."},
    {"english": "Hope never dies.", "native": "நம்பிக்கை ஒருபோதும் சாவதில்லை.", "transliteration": "Nambikkai orupodhum saavadhillai."},
    {"english": "Tomorrow is a new beginning.", "native": "நாளை ஒரு புதிய தொடக்கம்.", "transliteration": "Naalai oru pudhiya thodakkam."},
    {"english": "Keep hope alive in your heart.", "native": "உங்கள் இதயத்தில் நம்பிக்கையை உயிர்ப்போடு வையுங்கள்.", "transliteration": "Ungal idhayatthil nambikkkaiyai uyirpodu vaiyungal."},
    {"english": "Hope is the light in darkness.", "native": "நம்பிக்கை இருளில் ஒளி.", "transliteration": "Nambikkai irulil oli."},
    {"english": "Where there's hope, there's life.", "native": "நம்பிக்கை இருக்கும் இடத்தில் வாழ்க்கை உண்டு.", "transliteration": "Nambikkai irukkum idathil vaazhkkai undu."},
    {"english": "Create something beautiful today.", "native": "இன்று ஏதாவது அழகானதை உருவாக்குங்கள்.", "transliteration": "Indru aedhaavudhu azhagaanathai uruvaakkungal."},
    {"english": "Your creativity is unique.", "native": "உங்கள் படைப்பாற்றல் தனித்துவமானது.", "transliteration": "Ungal padaipparral thanithuvamaanarthu."},
    {"english": "Let your imagination run wild.", "native": "உங்கள் கற்பனையை சுதந்திரமாக விடுங்கள்.", "transliteration": "Ungal karpaniyai sudhandiramaga vidungal."},
    {"english": "Art comes from the heart.", "native": "கலை இதயத்திலிருந்து வருகிறது.", "transliteration": "Kalai idhayathilirundhu varugiradhu."},
    {"english": "Every day is a canvas.", "native": "ஒவ்வொரு நாளும் ஒரு கேன்வாஸ்.", "transliteration": "Ovvoru naalum oru canvas."},
    {"english": "Find peace within yourself.", "native": "உங்களுக்குள் அமைதியைக் காணுங்கள்.", "transliteration": "Ungalukkul amaidhiyaik kaanungal."},
    {"english": "Calm mind, happy heart.", "native": "அமைதியான மனம், மகிழ்ச்சியான இதயம்.", "transliteration": "Amaidiyaana manam, magizhchiyaana idayam."},
    {"english": "Peace begins with a smile.", "native": "அமைதி ஒரு புன்னகையுடன் தொடங்குகிறது.", "transliteration": "Amaidhi oru punnagayudan thodangugiradhu."},
    {"english": "Breathe deeply, let go.", "native": "ஆழமாக மூச்செடுத்து, விடுங்கள்.", "transliteration": "Aazhamaaga mooschetta, vidungal."},
    {"english": "Your inner peace is precious.", "native": "உங்கள் உள் அமைதி விலைமதிப்பற்றது.", "transliteration": "Ungal ul amaidhi vilaimathippatrathu."},
    {"english": "Believe you can, you're right.", "native": "நீங்கள் முடியும் என்று நம்புங்கள், நீங்கள் சரியானவர்கள்.", "transliteration": "Neengal mudiyaum endru nambungal, neengal thariyaanavaargal."},
    {"english": "You are stronger than you think.", "native": "நீங்கள் நினைப்பதை விட வலிமையாக இருக்கிறீர்கள்.", "transliteration": "Neengal ninaippathai vida valimaiyaaga irukkireergal."},
    {"english": "Confidence comes from within.", "native": "நம்பிக்கை உள்ளிருந்து வருகிறது.", "transliteration": "Nambikkai ullirundhu varugiradhu."},
    {"english": "Stand tall, be proud.", "native": "நேராக நில்லுங்கள், பெருமையாக இருங்கள்.", "transliteration": "Naeraaga nillungal, perumaiyaaga irungal."},
    {"english": "You have what it takes.", "native": "உங்களுக்குத் தேவையானது உங்களுக்கு உள்ளது.", "transliteration": "Ungalukku thevaiyaanadhu ungalukku ullaadhu."},
    {"english": "Never give up, keep going.", "native": "ஒருபோதும் விடாதீர்கள், தொடர்ந்து செல்லுங்கள்.", "transliteration": "Orupodhum vidaatheergal, thodarndhu sellungal."},
    {"english": "Persistence beats talent.", "native": "விடாமுயற்சி மேதைமையை வெல்கிறது.", "transliteration": "Vidaamuyarchi maedhaimaiyai velgiradhu."},
    {"english": "Fall seven times, rise eight.", "native": "ஏழுமுறை விழுந்தால் எட்டுமுறை எழுந்திரு.", "transliteration": "Ezhu murai vizhundhaal ettu murai ezhundhiru."},
    {"english": "Hard work pays off eventually.", "native": "கடின உழைப்பு இறுதியில் பலிக்கும்.", "transliteration": "Kadina ulaippu idthiyil palikkum."},
    {"english": "Stay the course, don't quit.", "native": "பாதையில் தொடருங்கள், விட்டுவிடாதீர்கள்.", "transliteration": "Paathaiyil thodarungal, vittuvidaatheergal."},
    {"english": "Let inspiration guide you.", "native": "உத்வேகம் உங்களை வழிநடத்தட்டும்.", "transliteration": "Udhvegam ungalai vazhinatathattum."},
    {"english": "Be the inspiration others need.", "native": "மற்றவர்களுக்குத் தேவையான உத்வேகமாக இருங்கள்.", "transliteration": "Matravaargalukku thevaiyaana udhvegamaga irungal."},
    {"english": "Inspire by example, not words.", "native": "வார்த்தைகளால் அல்ல, முன்னுதாரணத்தால் உத்வேகமூட்டுங்கள்.", "transliteration": "Vaarththaihgalaal alla, munnuhdhaaranathaal udhvegamootungal."},
    {"english": "Your story inspires others.", "native": "உங்கள் கதை மற்றவர்களுக்கு உத்வேகம் அளிக்கிறது.", "transliteration": "Ungal kadhai matravaargalukku udhvegam alikkiradhu."},
    {"english": "Find inspiration in nature.", "native": "இயற்கையில் உத்வேகத்தைக் காணுங்கள்.", "transliteration": "Iyarkaiyil udhvegaththai kkaanungal."},
    {"english": "Choose positivity every day.", "native": "தினமும் நேர்மறையைத் தேர்ந்தெடுங்கள்.", "transliteration": "Thidhamum naermayai thaerantheidungal."},
    {"english": "Positive thoughts create positive life.", "native": "நேர்மறை எண்ணங்கள் நேர்மறை வாழ்க்கையை உருவாக்குகின்றன.", "transliteration": "Naermai ennamgal naermai vaazhkkaiyai uruvaakku kinrana."},
    {"english": "Surround yourself with positivity.", "native": "உங்களை நேர்மறையால் சூழ்ந்து கொள்ளுங்கள்.", "transliteration": "Ungalai naermaiyaal soozhnthu kollungal."},
    {"english": "Every day is a fresh start.", "native": "ஒவ்வொரு நாளும் ஒரு புதிய தொடக்கம்.", "transliteration": "Ovvoru naalum oru pudhiya thodakkam."},
    {"english": "Live life with a positive heart.", "native": "நேர்மறை இதயத்துடன் வாழுங்கள்.", "transliteration": "Naermai idhayathudan vaazhunggal."},
    {"english": "Be brave, take the leap.", "native": "தைரியமாக இருங்கள், முன்னேறுங்கள்.", "transliteration": "Thairiyamaaga irungal, munnaerunggal."},
    {"english": "Courage is not absence of fear.", "native": "தைரியம் என்பது பயம் இன்மை அல்ல.", "transliteration": "Thairiyam enbadhu bayam inmai alla."},
    {"english": "Face your fears with courage.", "native": "தைரியத்துடன் உங்கள் பயங்களைச் சந்தியுங்கள்.", "transliteration": "Thairiyathudan ungal bayangalaich sandhiyungal."},
    {"english": "Brave hearts change the world.", "native": "தைரியமான இதயங்கள் உலகை மாற்றுகின்றன.", "transliteration": "Thairiyaamana idhayangal ulagai maattrukinrana."},
    {"english": "Courage grows with use.", "native": "தைரியம் பயன்படுத்தும்போது வளரும்.", "transliteration": "Thairiyam payanpaduththumpodhu valarum."},
    {"english": "Be kind to everyone you meet.", "native": "நீங்கள் சந்திக்கும் ஒவ்வொருவரிடமும் கனிவாக இருங்கள்.", "transliteration": "Neengal santhikkum ovvoruvaridamum kaniyaaha irungal."},
    {"english": "Kindness costs nothing, means everything.", "native": "கனிவுக்கு விலை இல்லை, ஆனால் அது எல்லாமே.", "transliteration": "Kaniukku vilai illai, aanaal adhu ellame."},
    {"english": "A kind word warms the heart.", "native": "கனிவான வார்த்தை இதயத்தை வெப்பப்படுத்துகிறது.", "transliteration": "Kaniyaana vaarththai idhayathai veppappaduththugiradhu."},
    {"english": "Spread kindness wherever you go.", "native": "நீங்கள் செல்லும் இடங்களிலெல்லாம் கனிவைப் பரப்புங்கள்.", "transliteration": "Neengal sellum idangalilellaam kanivaip parappungal."},
    {"english": "Kindness makes the world better.", "native": "கனிவு உலகை மேம்படுத்துகிறது.", "transliteration": "Kanivu ulagai maemppaduththugiradhu."},
    {"english": "Good things come to those who wait.", "native": "காத்திருப்பவர்களுக்கு நல்ல விஷயங்கள் வரும்.", "transliteration": "Kaaithiruppavargalukku nalla vishayangal varum."},
    {"english": "Patience is a virtue.", "native": "பொறுமை ஒரு நற்குணம்.", "transliteration": "Porumai oru nargunam."},
    {"english": "Take your time, don't rush.", "native": "உங்கள் நேரத்தை எடுத்துக்கொள்ளுங்கள், அவசரப்படாதீர்கள்.", "transliteration": "Ungal naerathei eduththukollungal, avasarappadaatheergal."},
    {"english": "Patience brings peace of mind.", "native": "பொறுமை மன அமைதியைத் தருகிறது.", "transliteration": "Porumai mana amaithiyai tharugiradhu."},
    {"english": "Wait patiently, trust the process.", "native": "பொறுமையாகக் காத்திருங்கள், செயல்முறையை நம்புங்கள்.", "transliteration": "Porumaiyaaga kaaththirungal, seialmuraiyai nambungal."},
    {"english": "Forgive and set yourself free.", "native": "மன்னித்து உங்களை விடுவித்துக் கொள்ளுங்கள்.", "transliteration": "Mannithu ungalai viduviththu kollungal."},
    {"english": "Forgiveness is a gift to yourself.", "native": "மன்னிப்பு உங்களுக்கு நீங்களே கொடுக்கும் கொடை.", "transliteration": "Mannippu ungalukku neengalae kodukkum kodai."},
    {"english": "Let go of grudges, find peace.", "native": "பகைமையை விடுங்கள், அமைதியைக் காணுங்கள்.", "transliteration": "Pakaimaiyai vidungal, amaithiyai kkaanungal."},
    {"english": "To err is human, to forgive divine.", "native": "தவறு செய்வது மனித இயல்பு, மன்னிப்பது தெய்வீகம்.", "transliteration": "Thavaru seivadhu manitha iyalbu, mannippadhu theyvikam."},
    {"english": "Forgiveness heals all wounds.", "native": "மன்னிப்பு அனைத்து காயங்களையும் ஆற்றுகிறது.", "transliteration": "Mannippu anaitthu kaayangalaiyum aatrugiradhu."},
    {"english": "You are stronger than you know.", "native": "நீங்கள் அறிவதை விட வலிமையாக இருக்கிறீர்கள்.", "transliteration": "Neengal arivathai vida valimaiyaaga irukkireergal."},
    {"english": "Strength comes from within.", "native": "வலிமை உள்ளிருந்து வருகிறது.", "transliteration": "Valimai ullirundhu varugiradhu."},
    {"english": "Your struggles develop your strength.", "native": "உங்கள் போராட்டங்கள் உங்கள் வலிமையை வளர்க்கின்றன.", "transliteration": "Ungal pooraatangal ungal valimaiyai valarkkinrana"},
    {"english": "Be strong, stay steady.", "native": "வலிமையாக இருங்கள், உறுதியாக இருங்கள்.", "transliteration": "Valimaiyaaga irungal, uthiyaaga irungal."},
    {"english": "Inner strength conquers all.", "native": "உள் வலிமை அனைத்தையும் வெல்கிறது.", "transliteration": "Ull valimai anaittaiyum velgiradhu."},
    {"english": "Find joy in every moment.", "native": "ஒவ்வொரு கணத்திலும் ஆனந்தத்தைக் காணுங்கள்.", "transliteration": "Ovvoru kanathilum aanandhathei kkaanungal."},
    {"english": "Joy is contagious, spread it.", "native": "ஆனந்தம் பரவும், பரப்புங்கள்.", "transliteration": "Aanandham paravum, parappungal."},
    {"english": "Let joy fill your heart today.", "native": "இன்று ஆனந்தம் உங்கள் இதயத்தை நிரப்பட்டும்.", "transliteration": "Indru aanandham ungal idhayathai nirappattum."},
    {"english": "Choose joy over worry.", "native": "கவலைக்கு பதிலாக ஆனந்தத்தைத் தேர்ந்தெடுங்கள்.", "transliteration": "Kavalaiku pathilaaga aanandhathei thaerantheidungal."},
    {"english": "Joy is the simplest form of gratitude.", "native": "ஆனந்தம் என்பது நன்றியுணர்வின் எளிய வடிவம்.", "transliteration": "Aanandham enbadhu nandriyunarvin eliya vadivam."},
    {"english": "Find balance in your life.", "native": "உங்கள் வாழ்க்கையில் சமநிலையைக் காணுங்கள்.", "transliteration": "Ungal vaazhkkaivl samanilaiyai kkaanungal."},
    {"english": "Balance is the key to happiness.", "native": "சமநிலையே மகிழ்ச்சிக்கான வழி.", "transliteration": "Samanilaiyae magizhchikkaarana vazhi."},
    {"english": "Work hard, rest well.", "native": "கடினமாக உழையுங்கள், நன்றாக ஓய்வெடுயுங்கள்.", "transliteration": "Kadinamaaga ulaiyungal, nandraaga oiyrv eduiyungal."},
    {"english": "A balanced life is a peaceful life.", "native": "சமநிலையான வாழ்க்கையே அமைதியான வாழ்க்கை.", "transliteration": "Samanilaiyaana vaazhkkaiyae amaithiyaana vaazhkkai."},
    {"english": "Prioritize what matters most.", "native": "மிக முக்கியமானதை முன்னுரிமை கொடுங்கள்.", "transliteration": "Miga mukkiyamaanathai munurimai kodungal."},
    {"english": "Growth happens outside your comfort zone.", "native": "வளர்ச்சி உங்கள் ஆறுதல் மண்டலத்திற்கு வெளியே நிகழ்கிறது.", "transliteration": "Valarchi ungal aaruthal mandalathirku veliye nigazhkiradhu."},
    {"english": "Embrace change, grow stronger.", "native": "மாற்றத்தை ஏற்றுக்கொள்ளுங்கள், வலிமையாக வளருங்கள்.", "transliteration": "Maattrathai aetrukkollungal, valimaiyaaga valaerunggal."},
    {"english": "Every challenge is a growth opportunity.", "native": "ஒவ்வொரு சவாலும் வளர்ச்சிக்கான வாய்ப்பு.", "transliteration": "Ovvoru savaalum valarchikkaaana vaayppu."},
    {"english": "Grow through what you go through.", "native": "நீங்கள் அனுபவிப்பவற்றின் மூலம் வளருங்கள்.", "transliteration": "Neengal anubavippavattrin moolam valaerunggal."},
    {"english": "Personal growth is a lifelong journey.", "native": "தனிப்பட்ட வளர்ச்சி வாழ்நாள் பயணம்.", "transliteration": "Thanipatta valarchi vaazhnaal payanam."},
    {"english": "Find your purpose, live it.", "native": "உங்கள் நோக்கத்தைக் கண்டுபிடியுங்கள், அதை வாழுங்கள்.", "transliteration": "Ungal nokkaththai kandupidiyungal, adhai vaazhunggal."},
    {"english": "Purpose gives life meaning.", "native": "நோக்கம் வாழ்க்கைக்கு அர்த்தத்தைக் கொடுக்கிறது.", "transliteration": "Nokkam vaazhkkaikku arthathaik kodukkugiradhu."},
    {"english": "Live with purpose and passion.", "native": "நோக்கத்துடனும் ஆர்வத்துடனும் வாழுங்கள்.", "transliteration": "Nokkatthudanum aarvatthudanum vaazhunggal."},
    {"english": "Your purpose is your calling.", "native": "உங்கள் நோக்கமே உங்கள் அழைப்பு.", "transliteration": "Ungal nokkamae ungal azhaippu."},
    {"english": "Discover purpose in everyday moments.", "native": "அன்றாட நிகழ்வுகளில் நோக்கத்தைக் கண்டுபிடியுங்கள்.", "transliteration": "Andraada nigazhuvugalil nokkathai kandupidiyungal."},
    {"english": "Be present in this moment.", "native": "இந்த நிமிஷத்தில் இருங்கள்.", "transliteration": "Indha nimishathil irungal."},
    {"english": "Mindfulness brings inner peace.", "native": "நுண்ணிய அறிவு உள் அமைதியைத் தருகிறது.", "transliteration": "Nunnlya arivu ull amaidhiyai tharugiradhu."},
    {"english": "Breathe deeply, stay mindful.", "native": "ஆழமாக மூச்செடுத்து, விழிப்புடன் இருங்கள்.", "transliteration": "Aazhamaaga mooschetta, vizhuppudan irungal."},
    {"english": "The present moment is all we have.", "native": "நிகழ் கணமே நமக்கு உள்ளது.", "transliteration": "Nigazh kanamae namakku ullaadhu."},
    {"english": "Practice mindfulness daily.", "native": "தினமும் நுண்ணிய அறிவைப் பயிற்சி செய்யுங்கள்.", "transliteration": "Thidhamum nunnlya arivaip prayirchi seiyungal."},
]
# ==== FALLBACK PHRASES END ====


def _load_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_phrase_history():
    data = _load_json(PHRASE_HISTORY_FILE, {"phrases": [], "last_updated": None})
    data.setdefault("phrases", [])
    return data


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    _save_json(PHRASE_HISTORY_FILE, data)


def is_phrase_used(english):
    english_lower = english.lower().strip()
    for p in load_phrase_history()["phrases"]:
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def _history_native(p):
    for key in (PHRASE_KEY, "vietnamese", "native", "translation", "target"):
        value = p.get(key)
        if value:
            return str(value)
    return ""


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            PHRASE_KEY: phrase["native"],
            "transliteration": phrase.get("transliteration", ""),
            "category": category,
            "generated_at": datetime.now().isoformat(),
        })
    save_phrase_history(history)
    print(f"[content] Saved {len(phrases)} phrases (history total: {len(history['phrases'])})")


def get_available_category():
    data = _load_json(RECENT_CATEGORIES_FILE, {"recent_categories": [], "last_updated": None})
    recent = data.get("recent_categories", [])
    available = [c for c in CATEGORIES if c not in recent]
    if not available:
        recent = recent[-5:]
        available = [c for c in CATEGORIES if c not in recent]
        print("[rotation] Reset recent categories")
    selected = random.choice(available)
    recent.append(selected)
    data["recent_categories"] = recent[-MAX_RECENT_CATEGORIES:]
    data["last_updated"] = datetime.now().isoformat()
    _save_json(RECENT_CATEGORIES_FILE, data)
    print(f"[rotation] Category: {selected} ({len(available)} available)")
    return selected


def _normalize_phrase(item):
    if not isinstance(item, dict):
        return None
    english = str(item.get("english", "")).strip()
    native = str(
        item.get(PHRASE_KEY)
        or item.get("native")
        or item.get("vietnamese")
        or item.get("translation")
        or ""
    ).strip()
    translit = str(item.get("transliteration") or item.get("romanization") or item.get("romaji") or "").strip()
    if not english or not native:
        return None
    if len(english.split()) > 16:
        return None
    if "/" in native or "|" in native:
        native = native.split("/")[0].split("|")[0].strip()
    return {
        "english": english.replace("  ", " ").strip(),
        "native": native.strip(),
        "transliteration": translit.strip().strip("[]"),
    }


def _history_keys(history):
    used_en = set()
    used_nat = set()
    for p in history.get("phrases", []):
        en = str(p.get("english", "")).lower().strip()
        nat = _history_native(p).lower().strip()
        if en:
            used_en.add(en)
        if nat:
            used_nat.add(nat)
    return used_en, used_nat


def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    category_native = CATEGORIES_NATIVE[category_english]
    history = load_phrase_history()
    used_en, used_nat = _history_keys(history)
    recent_english = [
        p["english"] for p in history["phrases"] if p.get("category") == category_english
    ][-30:]

    models = [config.AI_MODEL]
    if "gemini-fast" not in models:
        models.append("gemini-fast")

    if config.POLLINATIONS_API_KEY:
        for attempt in range(5):
            model = models[0] if attempt < 3 else models[-1]
            try:
                phrases = _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model)
                unique = []
                for item in phrases:
                    p = _normalize_phrase(item)
                    if not p:
                        continue
                    key_en = p["english"].lower().strip()
                    key_nat = p["native"].lower().strip()
                    if key_en in used_en or key_nat in used_nat:
                        continue
                    if any(key_en == u["english"].lower().strip() for u in unique):
                        continue
                    used_en.add(key_en)
                    used_nat.add(key_nat)
                    unique.append(p)
                    if len(unique) >= num_phrases:
                        break
                if len(unique) >= num_phrases:
                    add_phrases_to_history(unique[:num_phrases], category_english)
                    return unique[:num_phrases]
                print(f"[content] Attempt {attempt + 1}: only {len(unique)} fresh phrases (need {num_phrases})")
            except Exception as exc:  # noqa: BLE001 - network boundary
                print(f"[content] Attempt {attempt + 1} failed ({model}): {exc}")
            time.sleep(1.5 * (attempt + 1))
    else:
        print("[content] No POLLINATIONS_API_KEY, using fallback phrases")

    fresh_fallback = []
    for p in FALLBACK_PHRASES:
        if p["english"].lower().strip() in used_en or p["native"].lower().strip() in used_nat:
            continue
        fresh_fallback.append(p)
    if not fresh_fallback:
        raise RuntimeError("Phrase API unavailable and no unused fallback phrases left; refusing to reuse phrases")
    chosen = fresh_fallback[:num_phrases]
    if len(chosen) < num_phrases:
        print(f"[content] Only {len(chosen)} fresh fallback phrases; building a shorter lesson")
    add_phrases_to_history(chosen, category_english)
    return chosen


def _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model=None):
    avoid = ""
    if recent_english:
        avoid = "\nDo NOT reuse any of these phrases:\n" + "\n".join(f"- {p}" for p in recent_english)

    prompt = f"""Create {num_phrases * 6} unique {category_english} phrases for English speakers learning {LANGUAGE_NAME}.
{avoid}

Rules:
1. Keep every phrase short and natural (4-11 words in English).
2. Use natural commas for TTS breathing pauses.
3. Each phrase must be speakable in 2-4 seconds.
4. Write clean {LANGUAGE_NAME} in {NATIVE_NAME} with correct accents and orthography. One translation only, no slashes.
5. Transliteration is a friendly Roman-script pronunciation guide for English speakers (not IPA).
6. Vary the sentence patterns and emotions. No duplicates.
7. Phrases must feel like real everyday language, not textbook filler.

Return ONLY a JSON array:
[{{"english": "...", "native": "...", "transliteration": "..."}}]"""

    response = requests.post(
        "https://gen.pollinations.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.POLLINATIONS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or config.AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are a {LANGUAGE_NAME} teacher creating short, natural, varied bilingual phrases. Reply with JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": min(0.95 + attempt * 0.02, 1.0),
        },
        timeout=90,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    start = content.find("[")
    end = content.rfind("]")
    if start >= 0 and end > start:
        content = content[start:end + 1]

    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("AI did not return a JSON array")
    return data
