import re

js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# --- FIX 1: Add EVERYTHING to the Translation Dictionary ---
old_dict = """const translations = {
    en: { pageTitle: "Agricultural Assistant","""
new_dict = """const translations = {
    en: { 
        pageTitle: "Agricultural Assistant",
        navAI: "AI Assistant", navWeather: "Weather", navMandi: "Mandi Prices",
        sectionWorkspace: "WORKSPACE", sectionTools: "FARMING TOOLS",
        cardWeather: "WEATHER", cardMarket: "MARKET", cardSafety: "SAFETY",
        verificationStatus: "Waiting for your question",
        liveLabel: "LIVE DATA WHEN AVAILABLE","""
js = js.replace(old_dict, new_dict)

old_hi_dict = """    hi: { pageTitle: "कृषि सहायक","""
new_hi_dict = """    hi: { 
        pageTitle: "कृषि सहायक",
        navAI: "एआई सहायक", navWeather: "मौसम", navMandi: "मंडी भाव",
        sectionWorkspace: "कार्यक्षेत्र", sectionTools: "कृषि उपकरण",
        cardWeather: "मौसम", cardMarket: "बाज़ार", cardSafety: "सुरक्षा",
        verificationStatus: "आपके प्रश्न की प्रतीक्षा है",
        liveLabel: "लाइव डेटा उपलब्ध होने पर","""
js = js.replace(old_hi_dict, new_hi_dict)

# --- FIX 2: Update applyLanguage to translate the Sidebar ---
old_apply = """    // Translate sidebar tool buttons
    const navItems = document.querySelectorAll('.sidebar-section .nav-item');
    if (navItems.length >= 6) {
        navItems[3].querySelector('span:last-child').textContent = t("cropLabel");
        navItems[4].querySelector('span:last-child').textContent = t("pestLabel");
        navItems[5].querySelector('span:last-child').textContent = t("irrigLabel");
        navItems[6].querySelector('span:last-child').textContent = t("fertLabel");
    }"""
    
new_apply = """    // Translate Workspace Nav
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
    document.querySelector('.live-label').innerHTML = `<span></span> ${t("liveLabel")}`;"""
js = js.replace(old_apply, new_apply)

# --- FIX 3: Force WhatsApp Button & Fix Audio ---
# Ensure the WhatsApp button is actually in the DOM
old_actions = """        actions.append(copyButton, speakButton);"""
new_actions = """        const waButton = document.createElement("button");
        waButton.type = "button"; waButton.textContent = "Share 📲";
        waButton.style.color = "#25D366"; 
        waButton.addEventListener("click", () => {
            const shareText = encodeURIComponent(`AgriSathi Advisory:\\n\\n${String(text ?? "")}\\n\\n(Courtesy of AgriSathi AI)`);
            window.open(`https://wa.me/?text=${shareText}`, '_blank');
        });
        actions.append(copyButton, speakButton, waButton);"""
js = js.replace(old_actions, new_actions)

# Improve Audio Fallback for Brave (Force highest available voice)
old_audio = """    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.includes(state.language) && v.name.includes("Google")) || voices.find(v => v.lang.includes(state.language));
    if (preferredVoice) utterance.voice = preferredVoice;"""
new_audio = """    const voices = window.speechSynthesis.getVoices();
    // Brave blocks Google voices, so we try to find ANY natural sounding voice
    let preferredVoice = voices.find(v => v.lang.includes(state.language) && v.name.includes("Google"));
    if (!preferredVoice) preferredVoice = voices.find(v => v.lang.includes(state.language) && !v.name.includes("eSpeak"));
    if (!preferredVoice) preferredVoice = voices.find(v => v.lang.includes(state.language));
    if (preferredVoice) utterance.voice = preferredVoice;"""
js = js.replace(old_audio, new_audio)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js Master Patched: Full Translations, WhatsApp Fixed, Audio Improved.")
