import re

js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# --- FIX 1: Translate UI Elements (Buttons/Headers) ---
old_translations = """const translations = {
    en: { pageTitle: "Agricultural Assistant", questionPlaceholder: "Ask about your crop, soil, irrigation, pests...","""
new_translations = """const translations = {
    en: { pageTitle: "Agricultural Assistant", questionPlaceholder: "Ask about your crop, soil, irrigation, pests...", sendBtn: "Send question", newChatBtn: "＋ New conversation", cropLabel: "CROP GUIDANCE", pestLabel: "PEST MANAGEMENT", irrigLabel: "IRRIGATION", fertLabel: "FERTILIZER ADVICE","""
js = js.replace(old_translations, new_translations)

old_hi_trans = """    hi: { pageTitle: "कृषि सहायक", questionPlaceholder: "अपनी फसल, मिट्टी, सिंचाई या कीटों के बारे में पूछें...","""
new_hi_trans = """    hi: { pageTitle: "कृषि सहायक", questionPlaceholder: "अपनी फसल, मिट्टी, सिंचाई या कीटों के बारे में पूछें...", sendBtn: "प्रश्न भेजें", newChatBtn: "＋ नई बातचीत", cropLabel: "फसल मार्गदर्शन", pestLabel: "कीट प्रबंधन", irrigLabel: "सिंचाई", fertLabel: "उर्वरक सलाह","""
js = js.replace(old_hi_trans, new_hi_trans)

# Update applyLanguage to actually translate the UI
old_apply = """function applyLanguage() {
    document.documentElement.lang = state.language;
    elements.languageSelect.value = state.language;
    elements.pageTitle.textContent = t("pageTitle");
    elements.questionInput.placeholder = t("questionPlaceholder");
    localStorage.setItem("agrisathi.language", state.language);
}"""
new_apply = """function applyLanguage() {
    document.documentElement.lang = state.language;
    elements.languageSelect.value = state.language;
    elements.pageTitle.textContent = t("pageTitle");
    elements.questionInput.placeholder = t("questionPlaceholder");
    
    // Translate buttons and headers
    if (elements.sendButton) elements.sendButton.innerHTML = `<span>${t("sendBtn")}</span><span>➤</span>`;
    if (elements.clearChat) elements.clearChat.textContent = t("newChatBtn");
    
    // Translate sidebar tool buttons
    const navItems = document.querySelectorAll('.sidebar-section .nav-item');
    if (navItems.length >= 6) {
        navItems[3].querySelector('span:last-child').textContent = t("cropLabel");
        navItems[4].querySelector('span:last-child').textContent = t("pestLabel");
        navItems[5].querySelector('span:last-child').textContent = t("irrigLabel");
        navItems[6].querySelector('span:last-child').textContent = t("fertLabel");
    }
    
    localStorage.setItem("agrisathi.language", state.language);
}"""
js = js.replace(old_apply, new_apply)


# --- FIX 2: Stop Audio Overlap ---
old_audio = """function speakText(text) {
    if (!("speechSynthesis" in window)) { setVoiceStatus("Text-to-speech unsupported."); return; }
    window.speechSynthesis.cancel();"""
new_audio = """function speakText(text) {
    if (!("speechSynthesis" in window)) { setVoiceStatus("Text-to-speech unsupported."); return; }
    // Cancel any currently playing audio immediately to prevent overlap
    window.speechSynthesis.cancel();
    setTimeout(() => {"""
js = js.replace(old_audio, new_audio)
# Close the setTimeout
js = js.replace("""    window.speechSynthesis.speak(utterance);
}""", """    window.speechSynthesis.speak(utterance);
    }, 100);
}""")


# --- FIX 3: Show "Estimated Price" for Fallback Mandi Data ---
old_mandi_ui = """            elements.mandiPrice.textContent = `₹${formatPrice(modalPrice)}`;
            elements.mandiMarket.textContent = `${record.commodity} · ${record.market}, ${record.state}`;
            elements.mandiChange.textContent = `Date: ${record.arrival_date} · ${record.source || 'Govt API'}`;"""
            
new_mandi_ui = """            elements.mandiPrice.textContent = `₹${formatPrice(modalPrice)}`;
            elements.mandiMarket.textContent = `${record.commodity} · ${record.market}, ${record.state}`;
            
            const isFallback = record.source && record.source.includes("Fallback");
            if (isFallback) {
                elements.mandiPrice.style.color = "orange";
                elements.mandiChange.textContent = "⚠️ Estimated Price (API Offline)";
            } else {
                elements.mandiPrice.style.color = "var(--text)";
                elements.mandiChange.textContent = `Date: ${record.arrival_date} · Live API`;
            }"""
js = js.replace(old_mandi_ui, new_mandi_ui)


# --- FIX 4: Chat Persistence (Save to Local Storage) ---
# Save chat on new message
old_add_msg = """    row.append(avatar, content);
    elements.chatThread.appendChild(row);
    scrollChatToBottom();"""
new_add_msg = """    row.append(avatar, content);
    elements.chatThread.appendChild(row);
    scrollChatToBottom();
    localStorage.setItem("agrisathi.chatHistory", elements.chatThread.innerHTML);"""
js = js.replace(old_add_msg, new_add_msg)

# Restore chat on load
old_init = """    elements.verificationStatus.textContent = "Waiting for your question";
    await checkBackend();
    if (state.location) await loadWeather();
}"""
new_init = """    elements.verificationStatus.textContent = "Waiting for your question";
    
    // Restore chat history if exists
    const savedChat = localStorage.getItem("agrisathi.chatHistory");
    if (savedChat) {
        elements.chatThread.innerHTML = savedChat;
        hideWelcome();
        scrollChatToBottom();
    }
    
    await checkBackend();
    if (state.location) await loadWeather();
}"""
js = js.replace(old_init, new_init)

# Clear chat history on "New Conversation"
old_clear = """    elements.chatThread.replaceChildren();
    showWelcome();"""
new_clear = """    elements.chatThread.replaceChildren();
    localStorage.removeItem("agrisathi.chatHistory");
    showWelcome();"""
js = js.replace(old_clear, new_clear)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ All 4 UI flaws fixed! (Translations, Audio, Fallback UI, Persistence)")
