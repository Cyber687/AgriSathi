import re

# --- PATCH 1: script.js (Mic, Audio, Enter Key, Backend Text) ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Mic Permission
old_mic = """function startVoiceInput() {
    if (!SpeechRecognition) {
        setVoiceStatus(t("speechUnsupported"));
        return;
    }"""
new_mic = """async function startVoiceInput() {
    if (!SpeechRecognition) {
        setVoiceStatus(t("speechUnsupported"));
        return;
    }
    
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
        setVoiceStatus("Microphone access denied. Please allow it in browser settings.");
        return;
    }"""
js = js.replace(old_mic, new_mic)

# 2. Crackly Audio Fix (Force High Quality Google Voice)
old_audio = """    utterance.lang = voiceLanguages[state.language] || "en-IN";
    utterance.rate = 0.95;"""
new_audio = """    utterance.lang = voiceLanguages[state.language] || "en-IN";
    
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.includes(state.language) && v.name.includes("Google")) || voices.find(v => v.lang.includes(state.language));
    if (preferredVoice) utterance.voice = preferredVoice;
    
    utterance.rate = 0.95;"""
js = js.replace(old_audio, new_audio)

# 3. Enter Key
old_enter = """elements.questionInput.addEventListener(
    "input",
    updateCharacterCount
);"""
new_enter = """elements.questionInput.addEventListener(
    "input",
    updateCharacterCount
);

elements.questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        elements.chatForm.requestSubmit();
    }
});"""
js = js.replace(old_enter, new_enter)

# 4. Backend Text
js = js.replace('elements.connectionText.textContent = connected ? t("connected") : t("disconnected");', 'elements.connectionText.textContent = connected ? "Online" : "Offline";')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js patched (Mic, Audio, Enter Key, UI Text)")

# --- PATCH 2: index.html (Side Menu Questions) ---
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace(
    'data-question="Tell me about crop cultivation and growing requirements."',
    'data-question="Tell me about wheat cultivation."'
)
html = html.replace(
    'data-question="How can I identify and manage crop pests safely?"',
    'data-question="How can I manage pests in rice?"'
)
html = html.replace(
    'data-question="Explain irrigation methods suitable for my crop."',
    'data-question="What is the irrigation requirement for wheat?"'
)
html = html.replace(
    'data-question="Explain fertilizer requirements and why soil testing matters."',
    'data-question="What is the fertilizer requirement for rice?"'
)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ index.html patched (Side Menus now ask valid questions)")
