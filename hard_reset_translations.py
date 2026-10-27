import re

js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Replace the entire translations object
start_trans = js.find('const translations = {')
end_trans = js.find('};', start_trans) + 2

new_trans = '''const translations = {
    en: { 
        pageTitle: "Agricultural Assistant", questionPlaceholder: "Ask about your crop, soil, irrigation, pests...",
        sendBtn: "Send question", newChatBtn: "＋ New conversation", cropLabel: "CROP GUIDANCE", pestLabel: "PEST MANAGEMENT", irrigLabel: "IRRIGATION", fertLabel: "FERTILIZER ADVICE",
        navAI: "AI Assistant", navWeather: "Weather", navMandi: "Mandi Prices",
        sectionWorkspace: "WORKSPACE", sectionTools: "FARMING TOOLS",
        cardWeather: "WEATHER", cardMarket: "MARKET", cardSafety: "SAFETY",
        verificationStatus: "Waiting for your question", liveLabel: "LIVE DATA WHEN AVAILABLE",
        typing: "AgriSathi is preparing an answer...", connecting: "Connecting...", connected: "Active", disconnected: "Offline", emptyQuestion: "Please enter a question.", requestError: "I could not connect to AgriSathi.", serverError: "The backend could not process your question.", approved: "Safety checks approved", unverified: "Not verified — use caution", blocked: "Not approved by safety checks", noWeatherLocation: "Enter your city first.", weatherUnavailable: "Weather data unavailable", mandiUnavailable: "Mandi price data unavailable", listening: "Listening... speak your question.", speechUnsupported: "Speech recognition is not supported in this browser.", copied: "Answer copied.", newChat: "Conversation cleared.", darkMode: "Dark mode", lightMode: "Light mode", noSources: "No source references were returned.", safetyNotice: "Verify agricultural advice with a qualified local expert.", liveDataNotice: "Retrieved data is informational.",
        welcomeHead: 'Growing better, <span>together.</span>', welcomeDesc: 'Your farming companion for crop guidance, weather updates, market prices, and responsible agricultural decisions.', askBtn: 'Ask AgriSathi',
        dashTitle: 'Your farming dashboard', dashSub: 'FARM AT A GLANCE',
        card1Label: 'Current conditions', card1Desc: 'Enter a location to retrieve weather.', card2Label: 'Modal mandi price', card2Desc: 'Select a crop and market.', card3Label: 'Responsible guidance', card3Title: 'Evidence first', card3Desc: 'Recommendations should be checked against reliable agricultural sources.',
        sug1: 'Crop guidance', sug1D: 'Growing requirements and seasons', sug2: 'Pest management', sug2D: 'Identification and safe practices', sug3: 'Irrigation', sug3D: 'Water and crop requirements', sug4: 'Soil and fertilizer', sug4D: 'Understand nutrient requirements',
        disclaimer: '⚠️ <strong>Important:</strong> This AI provides information based on official databases. It does not replace professional agronomic advice. Always consult your local KVK before applying chemicals.'
    },
    hi: { 
        pageTitle: "कृषि सहायक", questionPlaceholder: "अपनी फसल, मिट्टी, सिंचाई या कीटों के बारे में पूछें...",
        sendBtn: "प्रश्न भेजें", newChatBtn: "＋ नई बातचीत", cropLabel: "फसल मार्गदर्शन", pestLabel: "कीट प्रबंधन", irrigLabel: "सिंचाई", fertLabel: "उर्वरक सलाह",
        navAI: "एआई सहायक", navWeather: "मौसम", navMandi: "मंडी भाव", sectionWorkspace: "कार्यक्षेत्र", sectionTools: "कृषि उपकरण",
        cardWeather: "मौसम", cardMarket: "बाज़ार", cardSafety: "सुरक्षा", verificationStatus: "आपके प्रश्न की प्रतीक्षा है", liveLabel: "लाइव डेटा उपलब्ध होने पर",
        typing: "AgriSathi उत्तर तैयार कर रहा है...", connecting: "कनेक्ट हो रहा है...", connected: "सक्रिय", disconnected: "बंद", emptyQuestion: "कृपया अपना प्रश्न लिखें।", requestError: "AgriSathi से कनेक्शन नहीं हो सका।", serverError: "सर्वर प्रश्न का उत्तर नहीं दे सका।", approved: "सुरक्षा जाँच स्वीकृत", unverified: "सत्यापित नहीं", blocked: "स्वीकृति नहीं मिली", noWeatherLocation: "पहले अपने शहर का नाम लिखें।", weatherUnavailable: "मौसम उपलब्ध नहीं है", mandiUnavailable: "मंडी भाव उपलब्ध नहीं हैं", listening: "सुन रहा हूँ...", speechUnsupported: "वॉइस इनपुट समर्थित नहीं है।", copied: "उत्तर कॉपी हो गया।", newChat: "बातचीत साफ कर दी गई।", darkMode: "डार्क मोड", lightMode: "लाइट मोड", noSources: "कोई स्रोत नहीं।", safetyNotice: "विशेषज्ञ से पुष्टि करें।", liveDataNotice: "डेटा जानकारी के लिए है।",
        welcomeHead: 'बेहतर खेती, <span>साथ मिलकर।</span>', welcomeDesc: 'फसल मार्गदर्शन, मौसम, मंडी भाव और जिम्मेदार कृषि निर्णयों के लिए आपका साथी।', askBtn: 'AgriSathi से पूछें',
        dashTitle: 'आपका कृषि डैशबोर्ड', dashSub: 'एक नज़र में खेत', card1Label: 'वर्तमान स्थिति', card1Desc: 'मौसम देखने के लिए स्थान दर्ज करें।', card2Label: 'मॉडल मंडी भाव', card2Desc: 'फसल और मंडी चुनें।', card3Label: 'जिम्मेदार मार्गदर्शन', card3Title: 'सबसे पहले सबूत', card3Desc: 'सिफारिशों को विश्वसनीय कृषि स्रोतों से जांचा जाना चाहिए।',
        sug1: 'फसल मार्गदर्शन', sug1D: 'उगाने की आवश्यकताएं और मौसम', sug2: 'कीट प्रबंधन', sug2D: 'पहचान और सुरक्षित तरीके', sug3: 'सिंचाई', sug3D: 'पानी और फसल की आवश्यकताएं', sug4: 'मिट्टी और खाद', sug4D: 'पोषक तत्वों की आवश्यकताओं को समझें',
        disclaimer: '⚠️ <strong>महत्वपूर्ण:</strong> यह AI आधिकारिक डेटाबेस के आधार पर जानकारी प्रदान करता है। यह पेशेवर कृषि सलाह नहीं है। रसायनों का उपयोग करने से पहले हमेशा अपने स्थानीय KVK से परामर्श करें।'
    },
    pa: { 
        pageTitle: "ਖੇਤੀਬਾੜੀ ਸਹਾਇਕ", questionPlaceholder: "ਆਪਣੀ ਫਸਲ, ਮਿੱਟੀ, ਸਿੰਚਾਈ ਜਾਂ ਕੀੜਿਆਂ ਬਾਰੇ ਪੁੱਛੋ...",
        sendBtn: "ਸਵਾਲ ਭੇਜੋ", newChatBtn: "＋ ਨਵੀਂ ਗੱਲਬਾਤ", cropLabel: "ਫਸਲ ਮਾਰਗਦਰਸ਼ਨ", pestLabel: "ਕੀੜੇ ਪ੍ਰਬੰਧਨ", irrigLabel: "ਸਿੰਚਾਈ", fertLabel: "ਖਾਦ ਸਲਾਹ",
        navAI: "AI ਸਹਾਇਕ", navWeather: "ਮੌਸਮ", navMandi: "ਮੰਡੀ ਭਾਅ", sectionWorkspace: "ਕਾਰਜ ਸਥਾਨ", sectionTools: "ਖੇਤੀ ਸੰਦ",
        cardWeather: "ਮੌਸਮ", cardMarket: "ਬਾਜ਼ਾਰ", cardSafety: "ਸੁਰੱਖਿਆ", verificationStatus: "ਤੁਹਾਡੇ ਸਵਾਲ ਦੀ ਉਡੀਕ ਹੈ", liveLabel: "ਲਾਈਵ ਡੇਟਾ ਉਪਲਬਧ ਹੋਣ 'ਤੇ",
        typing: "AgriSathi ਜਵਾਬ ਤਿਆਰ ਕਰ ਰਿਹਾ ਹੈ...", connecting: "ਕਨੈਕਟ ਹੋ ਰਿਹਾ ਹੈ...", connected: "ਸਰਗਰਮ", disconnected: "ਬੰਦ", emptyQuestion: "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਸਵਾਲ ਲਿਖੋ।", requestError: "AgriSathi ਨਾਲ ਕਨੈਕਸ਼ਨ ਨਹੀਂ ਹੋ ਸਕਿਆ।", serverError: "ਸਰਵਰ ਤੁਹਾਡੇ ਸਵਾਲ ਦਾ ਜਵਾਬ ਨਹੀਂ ਦੇ ਸਕਿਆ।", approved: "ਸੁਰੱਖਿਆ ਜਾਂਚ ਮਨਜ਼ੂਰ", unverified: "ਤਸਦੀਕ ਨਹੀਂ ਹੋਈ", blocked: "ਸੁਰੱਖਿਆ ਜਾਂਚ ਵੱਲੋਂ ਮਨਜ਼ੂਰ ਨਹੀਂ", noWeatherLocation: "ਪਹਿਲਾਂ ਆਪਣੇ ਸ਼ਹਿਰ ਦਾ ਨਾਮ ਦਰਜ ਕਰੋ।", weatherUnavailable: "ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਨਹੀਂ ਹੈ", mandiUnavailable: "ਮੰਡੀ ਦੇ ਭਾਅ ਉਪਲਬਧ ਨਹੀਂ ਹਨ", listening: "ਸੁਣ ਰਿਹਾ ਹਾਂ...", speechUnsupported: "ਇਸ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਵੌਇਸ ਇਨਪੁਟ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।", copied: "ਜਵਾਬ ਕਾਪੀ ਹੋ ਗਿਆ।", newChat: "ਗੱਲਬਾਤ ਸਾਫ਼ ਕਰ ਦਿੱਤੀ ਗਈ ਹੈ।", darkMode: "ਡਾਰਕ ਮੋਡ", lightMode: "ਲਾਈਟ ਮੋਡ", noSources: "ਕੋਈ ਸਰੋਤ ਨਹੀਂ ਦਿੱਤਾ ਗਿਆ।", safetyNotice: "ਖੇਤੀਬਾੜੀ ਸਲਾਹ ਦੀ ਪੁਸ਼ਟੀ ਸਥਾਨਕ ਮਾਹਿਰ ਤੋਂ ਕਰੋ।", liveDataNotice: "ਪ੍ਰਾਪਤ ਡਾਟਾ ਜਾਣਕਾਰੀ ਲਈ ਹੈ।",
        welcomeHead: 'ਵਧੀਆ ਖੇਤੀ, <span>ਇਕੱਠੇ ਮਿਲ ਕੇ।</span>', welcomeDesc: 'ਫਸਲਾਂ ਦੀ ਸਲਾਹ, ਮੌਸਮ, ਮੰਡੀ ਭਾਅ ਅਤੇ ਜ਼ਿੰਮੇਵਾਰ ਖੇਤੀਬਾੜੀ ਫੈਸਲਿਆਂ ਲਈ ਤੁਹਾਡਾ ਸਾਥੀ।', askBtn: 'AgriSathi ਨੂੰ ਪੁੱਛੋ',
        dashTitle: 'ਤੁਹਾਡਾ ਖੇਤੀ ਡੈਸ਼ਬੋਰਡ', dashSub: 'ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਖੇਤ', card1Label: 'ਮੌਜੂਦਾ ਹਾਲਾਤ', card1Desc: 'ਮੌਸਮ ਦੇਖਣ ਲਈ ਸਥਾਨ ਦਰਜ ਕਰੋ।', card2Label: 'ਮਾਡਲ ਮੰਡੀ ਭਾਅ', card2Desc: 'ਫਸਲ ਅਤੇ ਮੰਡੀ ਚੁਣੋ।', card3Label: 'ਜ਼ਿੰਮੇਵਾਰ ਮਾਰਗਦਰਸ਼ਨ', card3Title: 'ਪਹਿਲਾਂ ਸਬੂਤ', card3Desc: 'ਸਿਫ਼ਾਰਸ਼ਾਂ ਦੀ ਭਰੋਸੇਯੋਗ ਖੇਤੀਬਾੜੀ ਸਰੋਤਾਂ ਨਾਲ ਜਾਂਚ ਕੀਤੀ ਜਾਣੀ ਚਾਹੀਦੀ ਹੈ।',
        sug1: 'ਫਸਲ ਮਾਰਗਦਰਸ਼ਨ', sug1D: 'ਉਗਾਉਣ ਦੀਆਂ ਲੋੜਾਂ ਅਤੇ ਮੌਸਮ', sug2: 'ਕੀੜੇ ਪ੍ਰਬੰਧਨ', sug2D: 'ਪਛਾਣ ਅਤੇ ਸੁਰੱਖਿਅਤ ਤਰੀਕੇ', sug3: 'ਸਿੰਚਾਈ', sug3D: 'ਪਾਣੀ ਅਤੇ ਫਸਲ ਦੀਆਂ ਲੋੜਾਂ', sug4: 'ਮਿੱਟੀ ਅਤੇ ਖਾਦ', sug4D: 'ਪੋਸ਼ਕ ਤੱਤਾਂ ਦੀਆਂ ਲੋੜਾਂ ਨੂੰ ਸਮਝੋ',
        disclaimer: '⚠️ <strong>ਮਹੱਤਵਪੂਰਨ:</strong> ਇਹ AI ਅਧਿਕਾਰਤ ਡੇਟਾਬੇਸ ਦੇ ਅਧਾਰ ਤੇ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰਦਾ ਹੈ। ਇਹ ਪੇਸ਼ੇਵਰ ਖੇਤੀਬਾੜੀ ਸਲਾਹ ਨਹੀਂ ਹੈ। ਰਸਾਇਣਾਂ ਦੀ ਵਰਤੋਂ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਹਮੇਸ਼ਾ ਆਪਣੇ ਸਥਾਨਕ KVK ਨਾਲ ਸਲਾਹ ਕਰੋ।'
    },
    ta: { 
        pageTitle: "வேளாண் உதவியாளர்", questionPlaceholder: "உங்கள் பயிர், மண், நீர்ப்பாசனம் அல்லது பூச்சிகள் பற்றி கேளுங்கள்...",
        sendBtn: "கேள்வியை அனுப்பு", newChatBtn: "＋ புதிய உரையாடல்", cropLabel: "பயிர் வழிகாட்டுதல்", pestLabel: "பூச்சி மேலாண்மை", irrigLabel: "நீர்ப்பாசனம்", fertLabel: "உரம் ஆலோசனை",
        navAI: "AI உதவியாளர்", navWeather: "வானிலை", navMandi: "மண்டி விலை", sectionWorkspace: "பணியிடம்", sectionTools: "வேளாண் கருவிகள்",
        cardWeather: "வானிலை", cardMarket: "சந்தை", cardSafety: "பாதுகாப்பு", verificationStatus: "உங்கள் கேள்விக்காக காத்திருக்கிறது", liveLabel: "நேரடி தரவு கிடைக்கும்போது",
        typing: "AgriSathi பதிலை தயார் செய்கிறது...", connecting: "இணைக்கிறது...", connected: "செயலில் உள்ளது", disconnected: "ஆஃப்லைன்", emptyQuestion: "உங்கள் கேள்வியை உள்ளிடவும்.", requestError: "AgriSathi உடன் இணைக்க முடியவில்லை.", serverError: "சர்வர் பதிலளிக்க முடியவில்லை.", approved: "பாதுகாப்பு சோதனை அனுமதிக்கப்பட்டது", unverified: "சரிபார்க்கப்படவில்லை", blocked: "அனுமதிக்கப்படவில்லை", noWeatherLocation: "முதலில் உங்கள் நகரத்தை உள்ளிடவும்.", weatherUnavailable: "வானிலை தகவல் இல்லை", mandiUnavailable: "மண்டி விலை தகவல் இல்லை", listening: "கேட்கிறது...", speechUnsupported: "குரல் உள்ளீடு ஆதரிக்கப்படவில்லை.", copied: "நகலெடுக்கப்பட்டது.", newChat: "உரையாடல் அழிக்கப்பட்டது.", darkMode: "டார்க் மோட்", lightMode: "லைட் மோட்", noSources: "ஆதாரங்கள் இல்லை.", safetyNotice: "நிபுணரிடம் சரிபார்க்கவும்.", liveDataNotice: "தரவு தகவலுக்காக மட்டுமே.",
        welcomeHead: 'சிறந்த வளர்ச்சி, <span>ஒன்றாக.</span>', welcomeDesc: 'பயிர் வழிகாட்டுதல், வானிலை, சந்தை விலைகள் மற்றும் பொறுப்பான விவசாய முடிவுகளுக்கான உங்கள் துணை.', askBtn: 'AgriSathi-யிடம் கேளுங்கள்',
        dashTitle: 'உங்கள் விவசாய டாஷ்போர்டு', dashSub: 'ஒரு பார்வையில் பண்ணை', card1Label: 'தற்போதைய நிலைமைகள்', card1Desc: 'வானிலையைப் பெற இருப்பிடத்தை உள்ளிடவும்.', card2Label: 'மாதிரி மண்டி விலை', card2Desc: 'பயிர் மற்றும் சந்தையைத் தேர்ந்தெடுக்கவும்.', card3Label: 'பொறுப்பான வழிகாட்டுதல்', card3Title: 'ஆதாரம் முதலில்', card3Desc: 'பரிந்துரைகள் நம்பகமான விவசாய ஆதாரங்களுடன் சரிபார்க்கப்பட வேண்டும்.',
        sug1: 'பயிர் வழிகாட்டுதல்', sug1D: 'வளரும் தேவைகள் மற்றும் பருவங்கள்', sug2: 'பூச்சி மேலாண்மை', sug2D: 'அடையாளம் மற்றும் பாதுகாப்பான நடைமுறைகள்', sug3: 'நீர்ப்பாசனம்', sug3D: 'நீர் மற்றும் பயிர் தேவைகள்', sug4: 'மண் மற்றும் உரம்', sug4D: 'ஊட்டச்சத்து தேவைகளைப் புரிந்து கொள்ளுங்கள்',
        disclaimer: '⚠️ <strong>முக்கியம்:</strong> இந்த AI அதிகாரப்பூர்வ தரவுத்தளங்களின் அடிப்படையில் தகவல்களை வழங்குகிறது. இது தொழில்முறை விவசாய ஆலோசனையல்ல. ரசாயனங்களைப் பயன்படுத்தும் முன் எப்போதும் உங்கள் உள்ளூர் KVK-ஐ அணுகவும்.'
    }
};'''

js = js[:start_trans] + new_trans + js[end_trans:]

# 2. Replace the applyLanguage function
start_apply = js.find('function applyLanguage() {')
end_apply = js.find('elements.languageSelect.addEventListener', start_apply)

if start_apply != -1 and end_apply != -1:
    new_apply = """function applyLanguage() {
    document.documentElement.lang = state.language;
    elements.languageSelect.value = state.language;
    elements.pageTitle.textContent = t("pageTitle");
    elements.questionInput.placeholder = t("questionPlaceholder");
    
    // Sidebar & Buttons
    if (elements.sendButton) elements.sendButton.innerHTML = `<span>${t("sendBtn")}</span><span>➤</span>`;
    if (elements.clearChat) elements.clearChat.textContent = t("newChatBtn");
    
    const navItems = document.querySelectorAll('.sidebar-section .nav-item');
    if (navItems.length >= 7) {
        navItems[0].querySelector('span:last-child').textContent = t("navAI");
        navItems[1].querySelector('span:last-child').textContent = t("navWeather");
        navItems[2].querySelector('span:last-child').textContent = t("navMandi");
        navItems[3].querySelector('span:last-child').textContent = t("cropLabel");
        navItems[4].querySelector('span:last-child').textContent = t("pestLabel");
        navItems[5].querySelector('span:last-child').textContent = t("irrigLabel");
        navItems[6].querySelector('span:last-child').textContent = t("fertLabel");
    }
    
    const labels = document.querySelectorAll('.section-label');
    if(labels.length >= 2) {
        labels[0].textContent = t("sectionWorkspace");
        labels[1].textContent = t("sectionTools");
    }
    
    // Welcome Section
    document.querySelector('.welcome-copy h1').innerHTML = t("welcomeHead");
    document.querySelector('.welcome-copy p').textContent = t("welcomeDesc");
    elements.startChatButton.innerHTML = `${t("askBtn")} <span>→</span>`;
    
    // Dashboard
    const sectionHeadings = document.querySelectorAll('.section-heading');
    if(sectionHeadings.length > 0) {
        sectionHeadings[0].querySelector('.eyebrow').textContent = t("dashSub");
        sectionHeadings[0].querySelector('h2').textContent = t("dashTitle");
    }
    
    const cardLabels = document.querySelectorAll('.card-label');
    if(cardLabels.length >= 3) {
        cardLabels[0].textContent = t("card1Label");
        cardLabels[1].textContent = t("card2Label");
        cardLabels[2].textContent = t("card3Label");
    }
    
    const mutedTexts = document.querySelectorAll('.dashboard-card .muted-text');
    if(mutedTexts.length >= 3) {
        mutedTexts[0].textContent = t("card1Desc");
        mutedTexts[1].textContent = t("card2Desc");
        mutedTexts[2].textContent = t("card3Desc");
    }
    
    document.querySelector('.safety-card h3').textContent = t("card3Title");
    
    const tags = document.querySelectorAll('.card-tag');
    if(tags.length >= 3) {
        tags[0].textContent = t("cardWeather");
        tags[1].textContent = t("cardMarket");
        tags[2].textContent = t("cardSafety");
    }
    
    // Suggestions
    const sugCards = document.querySelectorAll('.suggestion-card');
    if(sugCards.length >= 4) {
        sugCards[0].querySelector('strong').textContent = t("sug1");
        sugCards[0].querySelector('small').textContent = t("sug1D");
        sugCards[1].querySelector('strong').textContent = t("sug2");
        sugCards[1].querySelector('small').textContent = t("sug2D");
        sugCards[2].querySelector('strong').textContent = t("sug3");
        sugCards[2].querySelector('small').textContent = t("sug3D");
        sugCards[3].querySelector('strong').textContent = t("sug4");
        sugCards[3].querySelector('small').textContent = t("sug4D");
    }
    
    // Safety & Disclaimer
    elements.verificationStatus.textContent = t("verificationStatus");
    document.querySelector('.live-label').innerHTML = `<span></span> ${t("liveLabel")}`;
    document.querySelector('.chat-disclaimer').innerHTML = t("disclaimer");
    
    localStorage.setItem("agrisathi.language", state.language);
}

"""
    js = js[:start_apply] + new_apply + js[end_apply:]

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js completely rewritten with full UI translations.")
