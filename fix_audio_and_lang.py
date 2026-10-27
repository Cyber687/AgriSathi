import re

# ============================================================
# 1. FIX AUDIO (Add Punjabi & Tamil Voices to text_to_speech.py)
# ============================================================
tts_path = 'voice/text_to_speech.py'
with open(tts_path, 'r', encoding='utf-8') as f:
    tts = f.read()

old_voices = """    DEFAULT_VOICES = {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
    }"""
new_voices = """    DEFAULT_VOICES = {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
        "pa": "pa-IN-GaganNeural",
        "ta": "ta-IN-PallaviNeural"
    }"""
tts = tts.replace(old_voices, new_voices)
with open(tts_path, 'w', encoding='utf-8') as f:
    f.write(tts)
print("✅ Backend: Added Punjabi & Tamil voices to TextToSpeech.")

# ============================================================
# 2. FIX UI TRANSLATIONS (Add Punjabi & Tamil to script.js)
# ============================================================
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Find the end of the translations object
old_trans_end = """        liveDataNotice: "Retrieved data is informational."
    }
};"""

new_trans_end = """        liveDataNotice: "Retrieved data is informational."
    },
    pa: {
        pageTitle: "ਖੇਤੀਬਾੜੀ ਸਹਾਇਕ",
        navAI: "AI ਸਹਾਇਕ", navWeather: "ਮੌਸਮ", navMandi: "ਮੰਡੀ ਭਾਅ",
        sectionWorkspace: "ਕਾਰਜ ਸਥਾਨ", sectionTools: "ਖੇਤੀ ਸੰਦ",
        cardWeather: "ਮੌਸਮ", cardMarket: "ਬਾਜ਼ਾਰ", cardSafety: "ਸੁਰੱਖਿਆ",
        verificationStatus: "ਤੁਹਾਡੇ ਸਵਾਲ ਦੀ ਉਡੀਕ ਹੈ",
        liveLabel: "ਲਾਈਵ ਡੇਟਾ ਉਪਲਬਧ ਹੋਣ 'ਤੇ",
        sendBtn: "ਸਵਾਲ ਭੇਜੋ", newChatBtn: "＋ ਨਵੀਂ ਗੱਲਬਾਤ",
        cropLabel: "ਫਸਲ ਮਾਰਗਦਰਸ਼ਨ", pestLabel: "ਕੀੜੇ ਪ੍ਰਬੰਧਨ", 
        irrigLabel: "ਸਿੰਚਾਈ", fertLabel: "ਖਾਦ ਸਲਾਹ",
        questionPlaceholder: "ਆਪਣੀ ਫਸਲ, ਮਿੱਟੀ, ਸਿੰਚਾਈ ਜਾਂ ਕੀੜਿਆਂ ਬਾਰੇ ਪੁੱਛੋ...",
        typing: "AgriSathi ਜਵਾਬ ਤਿਆਰ ਕਰ ਰਿਹਾ ਹੈ...", connecting: "ਕਨੈਕਟ ਹੋ ਰਿਹਾ ਹੈ...", connected: "ਸਰਗਰਮ", disconnected: "ਬੰਦ",
        emptyQuestion: "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਸਵਾਲ ਲਿਖੋ।", requestError: "AgriSathi ਨਾਲ ਕਨੈਕਸ਼ਨ ਨਹੀਂ ਹੋ ਸਕਿਆ।",
        serverError: "ਸਰਵਰ ਤੁਹਾਡੇ ਸਵਾਲ ਦਾ ਜਵਾਬ ਨਹੀਂ ਦੇ ਸਕਿਆ।", approved: "ਸੁਰੱਖਿਆ ਜਾਂਚ ਮਨਜ਼ੂਰ",
        unverified: "ਤਸਦੀਕ ਨਹੀਂ ਹੋਈ", blocked: "ਸੁਰੱਖਿਆ ਜਾਂਚ ਵੱਲੋਂ ਮਨਜ਼ੂਰ ਨਹੀਂ", noWeatherLocation: "ਪਹਿਲਾਂ ਆਪਣੇ ਸ਼ਹਿਰ ਦਾ ਨਾਮ ਦਰਜ ਕਰੋ।",
        weatherUnavailable: "ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਨਹੀਂ ਹੈ", mandiUnavailable: "ਮੰਡੀ ਦੇ ਭਾਅ ਉਪਲਬਧ ਨਹੀਂ ਹਨ",
        listening: "ਸੁਣ ਰਿਹਾ ਹਾਂ...", speechUnsupported: "ਇਸ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਵੌਇਸ ਇਨਪੁਟ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।",
        copied: "ਜਵਾਬ ਕਾਪੀ ਹੋ ਗਿਆ।", newChat: "ਗੱਲਬਾਤ ਸਾਫ਼ ਕਰ ਦਿੱਤੀ ਗਈ ਹੈ।", darkMode: "ਡਾਰਕ ਮੋਡ", lightMode: "ਲਾਈਟ ਮੋਡ",
        noSources: "ਕੋਈ ਸਰੋਤ ਨਹੀਂ ਦਿੱਤਾ ਗਿਆ।", safetyNotice: "ਖੇਤੀਬਾੜੀ ਸਲਾਹ ਦੀ ਪੁਸ਼ਟੀ ਸਥਾਨਕ ਮਾਹਿਰ ਤੋਂ ਕਰੋ।",
        liveDataNotice: "ਪ੍ਰਾਪਤ ਡਾਟਾ ਜਾਣਕਾਰੀ ਲਈ ਹੈ।"
    },
    ta: {
        pageTitle: "வேளாண் உதவியாளர்",
        navAI: "AI உதவியாளர்", navWeather: "வானிலை", navMandi: "மண்டி விலை",
        sectionWorkspace: "பணியிடம்", sectionTools: "வேளாண் கருவிகள்",
        cardWeather: "வானிலை", cardMarket: "சந்தை", cardSafety: "பாதுகாப்பு",
        verificationStatus: "உங்கள் கேள்விக்காக காத்திருக்கிறது",
        liveLabel: "நேரடி தரவு கிடைக்கும்போது",
        sendBtn: "கேள்வியை அனுப்பு", newChatBtn: "＋ புதிய உரையாடல்",
        cropLabel: "பயிர் வழிகாட்டுதல்", pestLabel: "பூச்சி மேலாண்மை", 
        irrigLabel: "நீர்ப்பாசனம்", fertLabel: "உரம் ஆலோசனை",
        questionPlaceholder: "உங்கள் பயிர், மண், நீர்ப்பாசனம் அல்லது பூச்சிகள் பற்றி கேளுங்கள்...",
        typing: "AgriSathi பதிலை தயார் செய்கிறது...", connecting: "இணைக்கிறது...", connected: "செயலில் உள்ளது", disconnected: "ஆஃப்லைன்",
        emptyQuestion: "உங்கள் கேள்வியை உள்ளிடவும்.", requestError: "AgriSathi உடன் இணைக்க முடியவில்லை.",
        serverError: "சர்வர் பதிலளிக்க முடியவில்லை.", approved: "பாதுகாப்பு சோதனை அனுமதிக்கப்பட்டது",
        unverified: "சரிபார்க்கப்படவில்லை", blocked: "அனுமதிக்கப்படவில்லை", noWeatherLocation: "முதலில் உங்கள் நகரத்தை உள்ளிடவும்.",
        weatherUnavailable: "வானிலை தகவல் இல்லை", mandiUnavailable: "மண்டி விலை தகவல் இல்லை",
        listening: "கேட்கிறது...", speechUnsupported: "குரல் உள்ளீடு ஆதரிக்கப்படவில்லை.",
        copied: "நகலெடுக்கப்பட்டது.", newChat: "உரையாடல் அழிக்கப்பட்டது.", darkMode: "டார்க் மோட்", lightMode: "லைட் மோட்",
        noSources: "ஆதாரங்கள் இல்லை.", safetyNotice: "நிபுணரிடம் சரிபார்க்கவும்.",
        liveDataNotice: "தரவு தகவலுக்காக மட்டுமே."
    }
};"""

js = js.replace(old_trans_end, new_trans_end)
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ Frontend: Added Punjabi & Tamil dictionaries to script.js.")

# ============================================================
# 3. Force Voice Language mapping in script.js
# ============================================================
old_voice_lang = """    const voiceLanguages = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", te: "te-IN", ta: "ta-IN", ml: "ml-IN", ur: "ur-PK" };"""
new_voice_lang = """    const voiceLanguages = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", ta: "ta-IN" };"""
js = js.replace(old_voice_lang, new_voice_lang)
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ Frontend: Cleaned up voice language mappings.")
