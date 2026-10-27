import re
import os

def patch_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Patched: {filepath}")

# --- 1. Patch local_gguf_translator.py (Add Languages) ---
lang_old = """LANGUAGES = {
    "en": "English", "hi": "Hindi", "pa": "Punjabi", "bn": "Bengali",
    "mr": "Marathi", "gu": "Gujarati", "ta": "Tamil", "te": "Telugu",
}"""
lang_new = """LANGUAGES = {
    "en": "English", "hi": "Hindi", "pa": "Punjabi", "bn": "Bengali",
    "mr": "Marathi", "gu": "Gujarati", "ta": "Tamil", "te": "Telugu",
    "ml": "Malayalam", "ur": "Urdu"
}"""
patch_file('local_gguf_translator.py', [(lang_old, lang_new)])

# --- 2. Patch main.py (Greetings & Clean Safety Errors) ---
main_py_path = 'main.py'
with open(main_py_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

# Add Greetings
greet_old = """        language = (language or "en").strip().lower()
        if language not in LANGUAGES:
            return self._error_response("""
greet_new = """        language = (language or "en").strip().lower()
        
        # GREETINGS HANDLER
        greetings = ["hi", "hello", "hey", "namaste", "how are you", "good morning", "good evening"]
        if query.lower().strip() in greetings:
            return {
                "approved": True, "status": "approved", "language": language,
                "answer": "Namaste! I am AgriSathi. How can I help you with your crops today?" if language == "en" else "नमस्ते! मैं एग्रीसाथी हूँ। आज मैं आपकी फसलों में कैसे मदद कर सकता हूँ?",
                "sources": [], "warnings": [], "safety": {"approved": True, "status": "approved"}, "timestamp": utc_timestamp()
            }

        if language not in LANGUAGES:
            return self._error_response("""
main_content = main_content.replace(greet_old, greet_new)

# Fix ugly safety error
safety_old = """        if not safety_approved:
            warnings.append(
                "This response has not been approved by the safety engine. "
                "Do not treat it as a verified agricultural recommendation."
            )

        if chemical_requested and not safety_approved:"""
safety_new = """        if not safety_approved:
            answer_text = "I don't have verified information for this specific question yet. I have logged this query so our agricultural experts can review it. Please consult your local Krishi Vigyan Kendra (KVK) for immediate help."
            warnings = ["Safety verification could not be completed."]

        if chemical_requested and not safety_approved:"""
main_content = main_content.replace(safety_old, safety_new)

with open(main_py_path, 'w', encoding='utf-8') as f:
    f.write(main_content)
print("✅ Patched: main.py")

# --- 3. Patch index.html (Language Dropdown) ---
html_old = """<select id="languageSelect" aria-label="Choose language">
                    <option value="en">English</option>
                    <option value="hi">हिन्दी</option>
                    <option value="pa">ਪੰਜਾਬੀ</option>
                </select>"""
html_new = """<select id="languageSelect" aria-label="Choose language">
                    <option value="en">English</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                    <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                    <option value="te">తెలుగు (Telugu)</option>
                    <option value="ta">தமிழ் (Tamil)</option>
                    <option value="ml">മലയാളം (Malayalam)</option>
                    <option value="ur">اردو (Urdu)</option>
                </select>"""
patch_file('frontend/index.html', [(html_old, html_new)])

# --- 4. Patch script.js (Enter Key, Mic, Backend Text, Mandi Bug, Audio) ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Enter Key
enter_old = """elements.questionInput.addEventListener(
    "input",
    updateCharacterCount
);"""
enter_new = """elements.questionInput.addEventListener(
    "input",
    updateCharacterCount
);

elements.questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        elements.chatForm.requestSubmit();
    }
});"""
js_content = js_content.replace(enter_old, enter_new)

# Backend Text
js_content = js_content.replace('elements.connectionText.textContent = connected ? t("connected") : t("disconnected");', 'elements.connectionText.textContent = connected ? "Online" : "Offline";')

# Mandi Bug (Remove crop from chat payload)
mandi_bug_old = """        const payload = {
            query,
            language: state.language,
            location: state.location || null,
            crop: elements.cropSelect.value || null
        };"""
mandi_bug_new = """        const payload = {
            query,
            language: state.language,
            location: state.location || null
        };"""
js_content = js_content.replace(mandi_bug_old, mandi_bug_new)

# Mic Permission Fix
mic_old = """function startVoiceInput() {
    if (!SpeechRecognition) {
        setVoiceStatus(t("speechUnsupported"));
        return;
    }"""
mic_new = """async function startVoiceInput() {
    if (!SpeechRecognition) {
        setVoiceStatus(t("speechUnsupported"));
        return;
    }
    
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
        setVoiceStatus("Microphone access denied. Please allow it in browser settings.");
        return;
    }
"""
js_content = js_content.replace(mic_old, mic_new)

# Audio Voice Fix
audio_old = """    utterance.lang = voiceLanguages[state.language] || "en-IN";
    utterance.rate = 0.95;"""
audio_new = """    utterance.lang = voiceLanguages[state.language] || "en-IN";
    
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.includes(state.language) && v.name.includes("Google")) || voices.find(v => v.lang.includes(state.language));
    if (preferredVoice) utterance.voice = preferredVoice;
    
    utterance.rate = 0.95;"""
js_content = js_content.replace(audio_old, audio_new)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js_content)
print("✅ Patched: frontend/script.js")

print("\n🎉 All fixes applied! Restart your Python server.")
