"use strict";

const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : window.location.origin;
const API_URLS = { health: `${API_BASE}/health`, chat: `${API_BASE}/api/chat`, weather: `${API_BASE}/api/weather`, mandi: `${API_BASE}/api/mandi` };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const elements = {
    sidebar: $("#sidebar"), mobileMenu: $("#mobileMenu"),
    connectionDot: $("#connectionDot"), connectionText: $("#connectionText"), footerConnection: $("#footerConnection"),
    pageTitle: $("#pageTitle"), locationInput: $("#locationInput"), saveLocation: $("#saveLocation"),
    languageSelect: $("#languageSelect"), themeToggle: $("#themeToggle"), themeIcon: $("#themeIcon"), themeLabel: $("#themeLabel"),
    welcomeSection: $("#welcomeSection"), startChatButton: $("#startChatButton"),
    temperature: $("#temperature"), weatherDescription: $("#weatherDescription"), humidity: $("#humidity"), wind: $("#wind"), weatherUpdated: $("#weatherUpdated"), refreshWeather: $("#refreshWeather"),
    cropSelect: $("#cropSelect"), mandiPrice: $("#mandiPrice"), mandiMarket: $("#mandiMarket"), mandiChange: $("#mandiChange"), refreshMandi: $("#refreshMandi"),
    verificationStatus: $("#verificationStatus"),
    chatSection: $("#chatSection"), chatWelcome: $("#chatWelcome"), chatThread: $("#chatThread"), chatForm: $("#chatForm"), questionInput: $("#questionInput"), sendButton: $("#sendButton"), characterCount: $("#characterCount"), clearChat: $("#clearChat"),
    typingIndicator: $("#typingIndicator"), voiceInput: $("#voiceInput"), voiceOutput: $("#voiceOutput"), voiceStatus: $("#voiceStatus"),
    toast: $("#toast")
};

let isSending = false;
let toastTimeout = null;
let recognition = null;
let currentRequestController = null;

const state = {
    location: localStorage.getItem("agrisathi.location") || "",
    language: localStorage.getItem("agrisathi.language") || "en",
    darkMode: localStorage.getItem("agrisathi.darkMode") === "true"
};

const translations = {
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
};

function t(key) { return translations[state.language]?.[key] || translations.en[key] || key; }

function escapeHTML(value) { return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]); }
function showToast(message) { elements.toast.textContent = message; elements.toast.classList.add("show"); window.clearTimeout(toastTimeout); toastTimeout = window.setTimeout(() => elements.toast.classList.remove("show"), 3500); }
function setVoiceStatus(message) { elements.voiceStatus.textContent = message; }
function formatTime() { return new Intl.DateTimeFormat([], { hour: "2-digit", minute: "2-digit" }).format(new Date()); }
function getErrorMessage(data, fallback) { if (!data) return fallback; if (typeof data.detail === "string") return data.detail; if (data.detail && typeof data.detail === "object") return data.detail.message || fallback; return data.message || data.error || fallback; }
function safeNumber(value) { const number = Number(value); return Number.isFinite(number) ? number : null; }
function formatPrice(value) { const number = safeNumber(value); if (number === null) return "—"; return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(number); }

async function apiRequest(url, options = {}, timeoutMs = 45000) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal, headers: { "Accept": "application/json", ...(options.headers || {}) } });
        const contentType = response.headers.get("content-type") || "";
        let data;
        if (contentType.includes("application/json")) data = await response.json();
        else { const text = await response.text(); data = { message: text.slice(0, 500) }; }
        if (!response.ok) throw new Error(getErrorMessage(data, `HTTP ${response.status}`));
        return data;
    } catch (error) {
        if (error.name === "AbortError") throw new Error("The request timed out.");
        throw error;
    } finally { window.clearTimeout(timeoutId); }
}

async function checkBackend() {
    try {
        const result = await apiRequest(API_URLS.health, { method: "GET" }, 7000);
        const connected = result.initialized === true && result.status === "ok";
        elements.connectionDot.classList.toggle("online", connected);
        elements.connectionDot.classList.toggle("offline", !connected);
        elements.connectionText.textContent = connected ? "Active" : "Offline";
        elements.footerConnection.textContent = connected ? `Connected` : "Degraded";
        return connected;
    } catch (error) {
        elements.connectionDot.classList.remove("online");
        elements.connectionDot.classList.add("offline");
        elements.connectionText.textContent = "Offline";
        elements.footerConnection.textContent = "Unable to contact backend.";
        return false;
    }
}

function applyLanguage() {
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

elements.languageSelect.addEventListener("change", () => {
    state.language = elements.languageSelect.value;
    applyLanguage();
    if (recognition) { try { recognition.stop(); } catch {} }
    setVoiceStatus(`Language: ${state.language}`);
});

function loadSavedLocation() { elements.locationInput.value = state.location; }

elements.saveLocation.addEventListener("click", async () => {
    const location = elements.locationInput.value.trim();
    if (!location) { showToast("Enter a city or district first."); return; }
    state.location = location;
    localStorage.setItem("agrisathi.location", location);
    showToast(`Location saved: ${location}`);
    await loadWeather();
});

elements.locationInput.addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); elements.saveLocation.click(); } });

function applyTheme() {
    document.body.classList.toggle("dark-mode", state.darkMode);
    elements.themeIcon.textContent = state.darkMode ? "☀" : "☾";
    elements.themeLabel.textContent = state.darkMode ? t("lightMode") : t("darkMode");
    localStorage.setItem("agrisathi.darkMode", String(state.darkMode));
}

elements.themeToggle.addEventListener("click", () => { state.darkMode = !state.darkMode; applyTheme(); });

function scrollToChat() {
    elements.chatSection.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => elements.questionInput.focus(), 400);
}

elements.startChatButton.addEventListener("click", scrollToChat);
elements.mobileMenu.addEventListener("click", () => elements.sidebar.classList.toggle("open"));

document.addEventListener("click", event => {
    const clickedInsideSidebar = elements.sidebar.contains(event.target);
    const clickedMenu = elements.mobileMenu.contains(event.target);
    if (window.innerWidth <= 1000 && !clickedInsideSidebar && !clickedMenu) elements.sidebar.classList.remove("open");
});

$$(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        // If it's a Workspace tab (AI Assistant, Weather, Mandi)
        if (button.dataset.view) {
            $$(".nav-item").forEach(item => item.classList.remove("active"));
            button.classList.add("active");
            
            const view = button.dataset.view;
            if (view === "chat") scrollToChat();
            else if (view === "weather") { 
                $("#temperature").scrollIntoView({ behavior: "smooth", block: "center" }); 
                if (state.location) loadWeather(); 
            }
            else if (view === "mandi") {
                elements.mandiPrice.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        } 
        // If it's a Farming Tool (Crop Guidance, Pest Management, etc.)
        else if (button.dataset.question) {
            // Keep "AI Assistant" as the active tab
            $$(".nav-item").forEach(item => item.classList.remove("active"));
            const chatTab = document.querySelector('.nav-item[data-view="chat"]');
            if (chatTab) chatTab.classList.add("active");
            
            // Type the question and scroll to chat
            elements.questionInput.value = button.dataset.question;
            updateCharacterCount(); 
            scrollToChat();
        }
        elements.sidebar.classList.remove("open");
    });
});

$$(".suggestion-card").forEach(button => {
    button.addEventListener("click", () => {
        elements.questionInput.value = button.dataset.question || "";
        updateCharacterCount(); scrollToChat();
    });
});

function hideWelcome() { elements.chatWelcome.classList.add("hidden"); }
function showWelcome() { elements.chatWelcome.classList.remove("hidden"); }
function updateCharacterCount() { elements.characterCount.textContent = `${elements.questionInput.value.length} / 2000`; }

elements.questionInput.addEventListener("input", updateCharacterCount);
elements.questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); elements.chatForm.requestSubmit(); }
});

function setSending(value) {
    isSending = value;
    elements.sendButton.disabled = value;
    elements.sendButton.innerHTML = value ? "<span>Thinking...</span><span>⌛</span>" : "<span>Send question</span><span>➤</span>";
    elements.typingIndicator.classList.toggle("hidden", !value);
}

function scrollChatToBottom() { elements.chatThread.scrollTop = elements.chatThread.scrollHeight; }

function normalizeSources(sources) {
    if (!Array.isArray(sources)) return [];
    return sources.map(source => {
        if (typeof source === "string") return { label: source, url: null };
        if (!source || typeof source !== "object") return null;
        const label = source.title || source.document_title || source.name || source.source_id || source.id || "Source";
        const rawUrl = source.url || source.link || null;
        let safeUrl = null;
        if (rawUrl) { try { const parsedUrl = new URL(rawUrl); if (parsedUrl.protocol === "https:") safeUrl = parsedUrl.href; } catch { safeUrl = null; } }
        return { label: String(label), url: safeUrl };
    }).filter(Boolean);
}

function determineSafetyStatus(data) {
    const safety = data.safety || {};
    const approved = data.approved === true && safety.approved === true;
    const status = String(safety.status || data.status || "").toLowerCase();
    if (approved) return { type: "approved", label: t("approved") };
    if (status.includes("block") || status.includes("reject") || status.includes("error")) return { type: "blocked", label: t("blocked") };
    return { type: "unverified", label: t("unverified") };
}

function addMessage(role, text, options = {}) {
    hideWelcome();
    const isUser = role === "user";
    const row = document.createElement("div");
    row.className = `message-row ${isUser ? "user-message" : "assistant-message"}`;
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = isUser ? "👤" : "🌱";
    const content = document.createElement("div");
    content.className = "message-content";
    const meta = document.createElement("div");
    meta.className = "message-meta";
    const name = document.createElement("strong");
    name.textContent = isUser ? "You" : "AgriSathi";
    const time = document.createElement("time");
    time.textContent = formatTime();
    meta.append(name, time);
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = String(text ?? "");
    content.append(meta, bubble);
    
    if (!isUser) {
        if (options.status) {
            const badge = document.createElement("div");
            badge.className = `message-status status-${options.status.type}`;
            badge.textContent = options.status.label;
            content.appendChild(badge);
        }
        const sources = normalizeSources(options.sources);
        if (sources.length > 0) {
            const sourceContainer = document.createElement("div");
            sourceContainer.className = "message-sources";
            const title = document.createElement("strong");
            title.textContent = "Sources";
            const list = document.createElement("ul");
            sources.forEach(source => {
                const item = document.createElement("li");
                if (source.url) { const link = document.createElement("a"); link.href = source.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = source.label; item.appendChild(link); }
                else item.textContent = source.label;
                list.appendChild(item);
            });
            sourceContainer.append(title, list);
            content.appendChild(sourceContainer);
        }
        const warnings = Array.isArray(options.warnings) ? options.warnings.filter(Boolean) : [];
        if (warnings.length > 0) {
            const warningContainer = document.createElement("div");
            warningContainer.className = "message-warnings";
            warningContainer.textContent = warnings.join(" ");
            content.appendChild(warningContainer);
        }
        const actions = document.createElement("div");
        actions.className = "message-actions";
        const copyButton = document.createElement("button");
        copyButton.type = "button"; copyButton.textContent = "Copy answer";
        copyButton.addEventListener("click", async () => { try { await navigator.clipboard.writeText(String(text ?? "")); showToast("✅ Answer copied to clipboard!"); } catch { showToast("Clipboard unavailable."); } });
        const speakButton = document.createElement("button");
        speakButton.type = "button"; speakButton.textContent = "Read aloud";
        speakButton.addEventListener("click", () => speakText(String(text ?? "")));
        const waButton = document.createElement("button");
        waButton.type = "button"; waButton.textContent = "Share 📲";
        waButton.style.color = "#25D366"; 
        waButton.addEventListener("click", () => {
            const shareText = encodeURIComponent(`AgriSathi Advisory:\n\n${String(text ?? "")}\n\n(Courtesy of AgriSathi AI)`);
            window.open(`https://wa.me/?text=${shareText}`, '_blank');
        });
        actions.append(copyButton, speakButton, waButton);
        content.appendChild(actions);
    }
    row.append(avatar, content);
    elements.chatThread.appendChild(row);
    scrollChatToBottom();
    localStorage.setItem("agrisathi.chatHistory", elements.chatThread.innerHTML);
}

async function submitQuestion(question) {
    const query = String(question || "").trim();
    if (!query) { showToast(t("emptyQuestion")); return; }
    if (isSending) return;
    if (query.length > 2000) { showToast("Keep your question under 2,000 characters."); return; }
    addMessage("user", query);
    elements.questionInput.value = "";
    updateCharacterCount();
    setSending(true);
    setVoiceStatus("");
    try {
        const payload = { query, language: state.language, location: state.location || null };
        const data = await apiRequest(API_URLS.chat, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }, 60000);
        const answer = data.answer || data.final_answer || "No answer returned.";
        const safetyStatus = determineSafetyStatus(data);
        const warnings = Array.isArray(data.warnings) ? data.warnings : [];
        addMessage("assistant", answer, { status: safetyStatus, sources: data.sources || [], warnings });
        elements.verificationStatus.textContent = safetyStatus.label;
        elements.verificationStatus.style.color = safetyStatus.type === "approved" ? "var(--green-700)" : "var(--text-secondary)";
    } catch (error) {
        addMessage("assistant", `${t("requestError")} Details: ${error.message}`, { status: { type: "blocked", label: "Connection error" } });
        elements.verificationStatus.textContent = "Unable to verify response.";
    } finally {
        setSending(false);
        elements.questionInput.focus();
    }
}

elements.chatForm.addEventListener("submit", event => { event.preventDefault(); submitQuestion(elements.questionInput.value); });
elements.clearChat.addEventListener("click", () => {
    if (isSending && currentRequestController) currentRequestController.abort();
    elements.chatThread.replaceChildren();
    localStorage.removeItem("agrisathi.chatHistory");
    showWelcome();
    elements.questionInput.value = "";
    updateCharacterCount();
    elements.verificationStatus.textContent = "Waiting for your question";
    showToast(t("newChat"));
});

async function loadWeather() {
    const location = state.location.trim();
    if (!location) { elements.weatherDescription.textContent = t("noWeatherLocation"); showToast(t("noWeatherLocation")); return; }
    elements.weatherDescription.textContent = "Loading weather...";
    elements.temperature.textContent = "--°C"; elements.humidity.textContent = "--%"; elements.wind.textContent = "-- km/h";
    try {
        const params = new URLSearchParams({ location });
        const data = await apiRequest(`${API_URLS.weather}?${params}`, { method: "GET" });
        if (data.status !== "live_data") throw new Error(data.message || t("weatherUnavailable"));
        elements.temperature.textContent = data.temperature_c == null ? "--°C" : `${data.temperature_c}°C`;
        elements.humidity.textContent = data.humidity == null ? "--%" : `${data.humidity}%`;
        let windKmh = safeNumber(data.wind_kmh);
        if (windKmh === null) { const windMps = safeNumber(data.wind_mps); if (windMps !== null) windKmh = windMps * 3.6; }
        elements.wind.textContent = windKmh === null ? "-- km/h" : `${windKmh.toFixed(1)} km/h`;
        elements.weatherDescription.textContent = data.description || "Current weather conditions";
        elements.weatherUpdated.textContent = data.updated_at ? `Updated: ${data.updated_at}` : `Updated: ${formatTime()}`;
    } catch (error) {
        elements.weatherDescription.textContent = t("weatherUnavailable");
        elements.weatherUpdated.textContent = "No live data";
        showToast(error.message);
    }
}
elements.refreshWeather.addEventListener("click", loadWeather);

async function loadMandiPrices() {
    const crop = elements.cropSelect.value;
    const market = state.location.trim();
    elements.mandiPrice.textContent = "—";
    elements.mandiMarket.textContent = `${crop}${market ? " · " + market : ""}`;
    elements.mandiChange.textContent = "Retrieving market records...";
    if (!market) { elements.mandiChange.textContent = "Enter a location."; showToast("Enter a city first."); return; }
    try {
        const params = new URLSearchParams({ crop, state: market, limit: "10" });
        const data = await apiRequest(`${API_URLS.mandi}?${params}`, { method: "GET" }, 20000);
        if (data.status !== "live_data" || !Array.isArray(data.records) || data.records.length === 0) throw new Error(data.message || t("mandiUnavailable"));
        const record = data.records[0];
        const modalPrice = record.modal_price || record.price;
        if (modalPrice) {
            elements.mandiPrice.textContent = `₹${formatPrice(modalPrice)}`;
            elements.mandiMarket.textContent = `${record.commodity} · ${record.market}, ${record.state}`;
            
            const isFallback = record.source && record.source.includes("Fallback");
            if (isFallback) {
                elements.mandiPrice.style.color = "orange";
                elements.mandiChange.textContent = "⚠️ Estimated Price (API Offline)";
            } else {
                elements.mandiPrice.style.color = "var(--text)";
                elements.mandiChange.textContent = `Date: ${record.arrival_date} · Live API`;
            }
        } else {
            elements.mandiPrice.textContent = "—";
            elements.mandiChange.textContent = "Records received; no recognized price field.";
        }
    } catch (error) {
        elements.mandiPrice.textContent = "—";
        elements.mandiChange.textContent = t("mandiUnavailable");
        showToast(error.message);
    }
}
elements.refreshMandi.addEventListener("click", loadMandiPrices);

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

async function startVoiceInput() {
    if (!SpeechRecognition) { setVoiceStatus(t("speechUnsupported")); return; }
    try { await navigator.mediaDevices.getUserMedia({ audio: true }); } catch (err) { setVoiceStatus("Microphone access denied."); return; }
    if (recognition) { try { recognition.stop(); } catch {} }
    recognition = new SpeechRecognition();
    const voiceLanguages = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", ta: "ta-IN" };
    recognition.lang = voiceLanguages[state.language] || "en-IN";
    recognition.interimResults = true;
    recognition.continuous = false;
    setVoiceStatus(t("listening"));
    elements.voiceInput.disabled = true;
    recognition.onresult = event => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) transcript += event.results[i][0].transcript;
        elements.questionInput.value = transcript.trim();
        updateCharacterCount();
    };
    recognition.onerror = event => setVoiceStatus(`Voice input error: ${event.error}`);
    recognition.onend = () => elements.voiceInput.disabled = false;
    try { recognition.start(); } catch (error) { elements.voiceInput.disabled = false; setVoiceStatus("Could not start voice input."); }
}
elements.voiceInput.addEventListener("click", startVoiceInput);

async function speakText(text) {
    setVoiceStatus("Generating audio...");
    
    try {
        const res = await fetch(API_BASE + '/api/tts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: text, language: state.language })
        });
        
        if (!res.ok) throw new Error("Backend TTS failed");
        
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        
        window.currentAudio = new Audio(url);
        window.currentAudio.play();
        setVoiceStatus("Speaking...");
        
        window.currentAudio.onended = () => setVoiceStatus("");
    } catch (e) {
        console.warn("Backend TTS failed, falling back to browser voice.", e);
        
        // FALLBACK: Use the browser's built-in voice if the backend fails
        if (!("speechSynthesis" in window)) { 
            setVoiceStatus("Text-to-speech unsupported."); 
            return; 
        }
        
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const voiceLanguages = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", ta: "ta-IN" };
        utterance.lang = voiceLanguages[state.language] || "en-IN";
        
        utterance.onstart = () => setVoiceStatus("Speaking...");
        utterance.onend = () => setVoiceStatus("");
        utterance.onerror = () => setVoiceStatus("Speech output unavailable.");
        
        window.speechSynthesis.speak(utterance);
    }
}

elements.voiceOutput.addEventListener("click", () => { 
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio.currentTime = 0;
    }
    if ("speechSynthesis" in window) { window.speechSynthesis.cancel(); }
    setVoiceStatus("Audio stopped."); 
});

async function initializeAgriSathi() {
    applyLanguage();
    applyTheme();
    loadSavedLocation();
    updateCharacterCount();
    elements.verificationStatus.textContent = "Waiting for your question";
    
    // Restore chat history if exists
    const savedChat = localStorage.getItem("agrisathi.chatHistory");
    if (savedChat) {
        elements.chatThread.innerHTML = savedChat;
        hideWelcome();
        scrollChatToBottom();
    }
    
    await checkBackend();
    if (state.location) await loadWeather();
}

initializeAgriSathi();
