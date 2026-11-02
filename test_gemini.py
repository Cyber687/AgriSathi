from services.gemini_service import GeminiService
import logging
logging.basicConfig(level=logging.INFO)

print("Testing Gemini API connection...")
gemini = GeminiService()
response = gemini.generate("Who is the prime minister of India?")
if response:
    print("\n✅ SUCCESS! Gemini says:\n", response)
else:
    print("\n❌ FAILED. Your API key might be invalid or you have no internet connection.")
