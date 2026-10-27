import re

# ============================================================
# 1. FIX BACKEND (main.py) - Make TTS Asynchronous & Error-Proof
# ============================================================
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main = f.read()

# Replace the old TTS endpoint with an async one
old_tts = '''@app.post("/api/tts")
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
        raise HTTPException(status_code=500, detail=str(e))'''

new_tts = '''@app.post("/api/tts")
async def generate_speech(request: ChatRequest):
    """Generate natural-sounding audio using edge-tts (Async Safe)."""
    try:
        from voice.text_to_speech import TextToSpeech
        tts = TextToSpeech()
        import time
        filename = f"tts_{int(time.time())}.mp3"
        
        # Use the async method directly to prevent blocking the server
        result = await tts.generate_audio_async(text=request.query, language=request.language, output_filename=filename)
        
        if result["status"] == "success":
            return FileResponse(result["audio_path"], media_type="audio/mpeg")
            
        logger.error(f"TTS Failed: {result.get('message')}")
        raise HTTPException(status_code=500, detail="TTS generation failed")
        
    except Exception as e:
        logger.exception("TTS Endpoint Crashed")
        raise HTTPException(status_code=500, detail=str(e))'''

main = main.replace(old_tts, new_tts)
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main)
print("✅ Backend: TTS endpoint rewritten to be Async and prevent 500 crashes.")

# ============================================================
# 2. FIX FRONTEND (script.js) - Fallback to Browser Voice if 500
# ============================================================
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the speakText function to include a fallback
pattern = r'async function speakText\(text\) \{.*?\n\}'
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
}'''
js = re.sub(pattern, new_speak, js, flags=re.DOTALL)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ Frontend: Added automatic fallback to browser TTS.")
