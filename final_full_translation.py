import re

js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add the missing translation keys to all languages
# We inject the new keys right before the closing brace of each language dict
keys_en = """
        welcomeHead: 'Growing better, <span>together.</span>',
        welcomeDesc: 'Your farming companion for crop guidance, weather updates, market prices, and responsible agricultural decisions.',
        askBtn: 'Ask AgriSathi',
        dashTitle: 'Your farming dashboard',
        dashSub: 'FARM AT A GLANCE',
        card1Label: 'Current conditions',
        card1Desc: 'Enter a location to retrieve weather.',
        card2Label: 'Modal mandi price',
        card2Desc: 'Select a crop and market.',
        card3Label: 'Responsible guidance',
        card3Title: 'Evidence first',
        card3Desc: 'Recommendations should be checked against reliable agricultural sources.',
        sug1: 'Crop guidance', sug1D: 'Growing requirements and seasons',
        sug2: 'Pest management', sug2D: 'Identification and safe practices',
        sug3: 'Irrigation', sug3D: 'Water and crop requirements',
        sug4: 'Soil and fertilizer', sug4D: 'Understand nutrient requirements',
        disclaimer: '⚠️ <strong>Important:</strong> This AI provides information based on official databases. It does not replace professional agronomic advice. Always consult your local KVK before applying chemicals.'
"""

keys_hi = """
        welcomeHead: 'बेहतर खेती, <span>साथ मिलकर।</span>',
        welcomeDesc: 'फसल मार्गदर्शन, मौसम, मंडी भाव और जिम्मेदार कृषि निर्णयों के लिए आपका साथी।',
        askBtn: 'AgriSathi से पूछें',
        dashTitle: 'आपका कृषि डैशबोर्ड',
        dashSub: 'एक नज़र में खेत',
        card1Label: 'वर्तमान स्थिति',
        card1Desc: 'मौसम देखने के लिए स्थान दर्ज करें।',
        card2Label: 'मॉडल मंडी भाव',
        card2Desc: 'फसल और मंडी चुनें।',
        card3Label: 'जिम्मेदार मार्गदर्शन',
        card3Title: 'सबसे पहले सबूत',
        card3Desc: 'सिफारिशों को विश्वसनीय कृषि स्रोतों से जांचा जाना चाहिए।',
        sug1: 'फसल मार्गदर्शन', sug1D: 'उगाने की आवश्यकताएं और मौसम',
        sug2: 'कीट प्रबंधन', sug2D: 'पहचान और सुरक्षित तरीके',
        sug3: 'सिंचाई', sug3D: 'पानी और फसल की आवश्यकताएं',
        sug4: 'मिट्टी और खाद', sug4D: 'पोषक तत्वों की आवश्यकताओं को समझें',
        disclaimer: '⚠️ <strong>महत्वपूर्ण:</strong> यह AI आधिकारिक डेटाबेस के आधार पर जानकारी प्रदान करता है। यह पेशेवर कृषि सलाह नहीं है। रसायनों का उपयोग करने से पहले हमेशा अपने स्थानीय KVK से परामर्श करें।'
"""

keys_pa = """
        welcomeHead: 'ਵਧੀਆ ਖੇਤੀ, <span>ਇਕੱਠੇ ਮਿਲ ਕੇ।</span>',
        welcomeDesc: 'ਫਸਲਾਂ ਦੀ ਸਲਾਹ, ਮੌਸਮ, ਮੰਡੀ ਭਾਅ ਅਤੇ ਜ਼ਿੰਮੇਵਾਰ ਖੇਤੀਬਾੜੀ ਫੈਸਲਿਆਂ ਲਈ ਤੁਹਾਡਾ ਸਾਥੀ।',
        askBtn: 'AgriSathi ਨੂੰ ਪੁੱਛੋ',
        dashTitle: 'ਤੁਹਾਡਾ ਖੇਤੀ ਡੈਸ਼ਬੋਰਡ',
        dashSub: 'ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਖੇਤ',
        card1Label: 'ਮੌਜੂਦਾ ਹਾਲਾਤ',
        card1Desc: 'ਮੌਸਮ ਦੇਖਣ ਲਈ ਸਥਾਨ ਦਰਜ ਕਰੋ।',
        card2Label: 'ਮਾਡਲ ਮੰਡੀ ਭਾਅ',
        card2Desc: 'ਫਸਲ ਅਤੇ ਮੰਡੀ ਚੁਣੋ।',
        card3Label: 'ਜ਼ਿੰਮੇਵਾਰ ਮਾਰਗਦਰਸ਼ਨ',
        card3Title: 'ਪਹਿਲਾਂ ਸਬੂਤ',
        card3Desc: 'ਸਿਫ਼ਾਰਸ਼ਾਂ ਦੀ ਭਰੋਸੇਯੋਗ ਖੇਤੀਬਾੜੀ ਸਰੋਤਾਂ ਨਾਲ ਜਾਂਚ ਕੀਤੀ ਜਾਣੀ ਚਾਹੀਦੀ ਹੈ।',
        sug1: 'ਫਸਲ ਮਾਰਗਦਰਸ਼ਨ', sug1D: 'ਉਗਾਉਣ ਦੀਆਂ ਲੋੜਾਂ ਅਤੇ ਮੌਸਮ',
        sug2: 'ਕੀੜੇ ਪ੍ਰਬੰਧਨ', sug2D: 'ਪਛਾਣ ਅਤੇ ਸੁਰੱਖਿਅਤ ਤਰੀਕੇ',
        sug3: 'ਸਿੰਚਾਈ', sug3D: 'ਪਾਣੀ ਅਤੇ ਫਸਲ ਦੀਆਂ ਲੋੜਾਂ',
        sug4: 'ਮਿੱਟੀ ਅਤੇ ਖਾਦ', sug4D: 'ਪੋਸ਼ਕ ਤੱਤਾਂ ਦੀਆਂ ਲੋੜਾਂ ਨੂੰ ਸਮਝੋ',
        disclaimer: '⚠️ <strong>ਮਹੱਤਵਪੂਰਨ:</strong> ਇਹ AI ਅਧਿਕਾਰਤ ਡੇਟਾਬੇਸ ਦੇ ਅਧਾਰ ਤੇ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰਦਾ ਹੈ। ਇਹ ਪੇਸ਼ੇਵਰ ਖੇਤੀਬਾੜੀ ਸਲਾਹ ਨਹੀਂ ਹੈ। ਰਸਾਇਣਾਂ ਦੀ ਵਰਤੋਂ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਹਮੇਸ਼ਾ ਆਪਣੇ ਸਥਾਨਕ KVK ਨਾਲ ਸਲਾਹ ਕਰੋ।'
"""

keys_ta = """
        welcomeHead: 'சிறந்த வளர்ச்சி, <span>ஒன்றாக.</span>',
        welcomeDesc: 'பயிர் வழிகாட்டுதல், வானிலை, சந்தை விலைகள் மற்றும் பொறுப்பான விவசாய முடிவுகளுக்கான உங்கள் துணை.',
        askBtn: 'AgriSathi-யிடம் கேளுங்கள்',
        dashTitle: 'உங்கள் விவசாய டாஷ்போர்டு',
        dashSub: 'ஒரு பார்வையில் பண்ணை',
        card1Label: 'தற்போதைய நிலைமைகள்',
        card1Desc: 'வானிலையைப் பெற இருப்பிடத்தை உள்ளிடவும்.',
        card2Label: 'மாதிரி மண்டி விலை',
        card2Desc: 'பயிர் மற்றும் சந்தையைத் தேர்ந்தெடுக்கவும்.',
        card3Label: 'பொறுப்பான வழிகாட்டுதல்',
        card3Title: 'ஆதாரம் முதலில்',
        card3Desc: 'பரிந்துரைகள் நம்பகமான விவசாய ஆதாரங்களுடன் சரிபார்க்கப்பட வேண்டும்.',
        sug1: 'பயிர் வழிகாட்டுதல்', sug1D: 'வளரும் தேவைகள் மற்றும் பருவங்கள்',
        sug2: 'பூச்சி மேலாண்மை', sug2D: 'அடையாளம் மற்றும் பாதுகாப்பான நடைமுறைகள்',
        sug3: 'நீர்ப்பாசனம்', sug3D: 'நீர் மற்றும் பயிர் தேவைகள்',
        sug4: 'மண் மற்றும் உரம்', sug4D: 'ஊட்டச்சத்து தேவைகளைப் புரிந்து கொள்ளுங்கள்',
        disclaimer: '⚠️ <strong>முக்கியம்:</strong> இந்த AI அதிகாரப்பூர்வ தரவுத்தளங்களின் அடிப்படையில் தகவல்களை வழங்குகிறது. இது தொழில்முறை விவசாய ஆலோசனையல்ல. ரசாயனங்களைப் பயன்படுத்தும் முன் எப்போதும் உங்கள் உள்ளூர் KVK-ஐ அணுகவும்.'
"""

# Find the closing braces of the dictionaries and inject
js = js.replace('        liveDataNotice: "Retrieved data is informational."\n    }\n};', f'        liveDataNotice: "Retrieved data is informational.",{keys_en}\n    }},\n    hi: {{', 1)
# Remove old hi dict to replace it properly
js = re.sub(r'    hi: \{.*?\n    \},\n    pa:', f'    hi: {{{keys_hi}\n    }},\n    pa:', js, flags=re.DOTALL)
js = re.sub(r'    pa: \{.*?\n    \},\n    ta:', f'    pa: {{{keys_pa}\n    }},\n    ta:', js, flags=re.DOTALL)
js = re.sub(r'    ta: \{.*?\n    \}\n\};', f'    ta: {{{keys_ta}\n    }}\n}};', js, flags=re.DOTALL)

# 2. Update applyLanguage() to replace all static UI text
old_apply = """function applyLanguage() {
    document.documentElement.lang = state.language;
    elements.languageSelect.value = state.language;
    elements.pageTitle.textContent = t("pageTitle");
    elements.questionInput.placeholder = t("questionPlaceholder");
    
    // Translate buttons and headers
    if (elements.sendButton) elements.sendButton.innerHTML = `<span>${t("sendBtn")}</span><span>➤</span>`;
    if (elements.clearChat) elements.clearChat.textContent = t("newChatBtn");
    
    // Translate Workspace Nav
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
    
    // Translate Section Labels
    const labels = document.querySelectorAll('.section-label');
    if(labels.length >= 2) {
        labels[0].textContent = t("sectionWorkspace");
        labels[1].textContent = t("sectionTools");
    }
    
    // Translate Cards
    const tags = document.querySelectorAll('.card-tag');
    if(tags.length >= 3) {
        tags[0].textContent = t("cardWeather");
        tags[1].textContent = t("cardMarket");
        tags[2].textContent = t("cardSafety");
    }
    
    elements.verificationStatus.textContent = t("verificationStatus");
    document.querySelector('.live-label').innerHTML = `<span></span> ${t("liveLabel")}`;
    
    localStorage.setItem("agrisathi.language", state.language);
}"""

new_apply = """function applyLanguage() {
    document.documentElement.lang = state.language;
    elements.languageSelect.value = state.language;
    elements.pageTitle.textContent = t("pageTitle");
    elements.questionInput.placeholder = t("questionPlaceholder");
    
    // 1. Sidebar & Buttons
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
    
    // 2. Welcome Section
    document.querySelector('.welcome-copy h1').innerHTML = t("welcomeHead");
    document.querySelector('.welcome-copy p').textContent = t("welcomeDesc");
    elements.startChatButton.innerHTML = `${t("askBtn")} <span>→</span>`;
    
    // 3. Dashboard
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
    
    // 4. Suggestions
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
    
    // 5. Safety & Disclaimer
    elements.verificationStatus.textContent = t("verificationStatus");
    document.querySelector('.live-label').innerHTML = `<span></span> ${t("liveLabel")}`;
    document.querySelector('.chat-disclaimer').innerHTML = t("disclaimer");
    
    localStorage.setItem("agrisathi.language", state.language);
}"""

js = js.replace(old_apply, new_apply)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js patched: FULL UI translation added for all 4 languages!")
