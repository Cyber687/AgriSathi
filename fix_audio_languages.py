import re
import os

# ============================================================
# 1. BACKEND: Add TTS Endpoint (main.py)
# ============================================================
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main = f.read()

# Add import for TTS and FileResponse
if 'from voice.text_to_speech import TextToSpeech' not in main:
    main = main.replace(
        'from services.local_gguf_translator import LANGUAGES',
        'from services.local_gguf_translator import LANGUAGES\nfrom voice.text_to_speech import TextToSpeech\nfrom fastapi.responses import FileResponse'
    )

# Add the /api/tts endpoint
if '@app.post("/api/tts")' not in main:
    tts_endpoint = '''
@app.post("/api/tts")
def generate_speech(request: ChatRequest):
    """Generate natural-sounding audio using edge-tts."""
    try:
        tts = TextToSpeech()
        # Use a short filename based on timestamp
        import time
        filename = f"tts_{int(time.time())}.mp3"
        result = tts.generate_audio(text=request.query, language=request.language, output_filename=filename)
        
        if result["status"] == "success":
            return FileResponse(result["audio_path"], media_type="audio/mpeg")
        raise HTTPException(status_code=500, detail="TTS generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
    # Insert before the frontend serving section
    main = main.replace('# ============================================================\n# 12. FRONTEND SERVING', tts_endpoint + '\n# ============================================================\n# 12. FRONTEND SERVING')

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main)
print("✅ Backend: /api/tts endpoint added.")

# ============================================================
# 2. FRONTEND: Play Backend Audio (script.js)
# ============================================================
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the speakText function entirely
pattern = r'function speakText\(text\) \{.*?\n\}'
new_speak = '''async function speakText(text) {
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
        console.error(e);
        setVoiceStatus("Audio generation failed.");
    }
}'''
js = re.sub(pattern, new_speak, js, flags=re.DOTALL)

# Fix the Stop Audio button
old_stop = """elements.voiceOutput.addEventListener("click", () => { if ("speechSynthesis" in window) { window.speechSynthesis.cancel(); setVoiceStatus("Audio stopped."); } });"""
new_stop = """elements.voiceOutput.addEventListener("click", () => { 
    if (window.currentAudio) {
        window.currentAudio.pause();
        window.currentAudio.currentTime = 0;
    }
    if ("speechSynthesis" in window) { window.speechSynthesis.cancel(); }
    setVoiceStatus("Audio stopped."); 
});"""
js = js.replace(old_stop, new_stop)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ Frontend: Audio now plays via backend MP3.")

# ============================================================
# 3. LIMIT LANGUAGES (index.html & backend)
# ============================================================
# Update index.html
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

old_select = re.search(r'<select id="languageSelect".*?</select>', html, flags=re.DOTALL).group(0)
new_select = '''<select id="languageSelect" aria-label="Choose language">
                    <option value="en">English</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                    <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                    <option value="ta">தமிழ் (Tamil)</option>
                </select>'''
html = html.replace(old_select, new_select)
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ index.html: Languages reduced to top 4.")

# Update backend LANGUAGES dictionary
trans_path = 'services/local_gguf_translator.py'
with open(trans_path, 'r', encoding='utf-8') as f:
    trans = f.read()

old_dict = re.search(r'LANGUAGES = \{.*?\}', trans, flags=re.DOTALL).group(0)
new_dict = '''LANGUAGES = {
    "en": "English", 
    "hi": "Hindi", 
    "pa": "Punjabi", 
    "ta": "Tamil"
}'''
trans = trans.replace(old_dict, new_dict)
with open(trans_path, 'w', encoding='utf-8') as f:
    f.write(trans)
print("✅ Backend: Supported languages updated.")

