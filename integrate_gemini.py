import re

# ============================================================
# 1. Create the Gemini Service
# ============================================================
service_code = '''import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agrisathi")

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Using the fast and free flash model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✨ Gemini Fallback Service Initialized.")
        else:
            self.model = None
            logger.warning("⚠️ GEMINI_API_KEY not found. Fallback disabled.")

    def generate(self, prompt, system_prompt=None):
        if not self.model:
            return None
        try:
            # Combine system prompt and user prompt
            full_prompt = f"System Instructions: {system_prompt}\\n\\nUser Query: {prompt}" if system_prompt else prompt
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return None
'''

with open('services/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(service_code)
print("✅ Created services/gemini_service.py")

# ============================================================
# 2. Patch main.py to use the Fallback Silently
# ============================================================
path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'from services.gemini_service import GeminiService' not in content:
    content = content.replace(
        'from services.local_gguf_translator import LANGUAGES',
        'from services.local_gguf_translator import LANGUAGES\nfrom services.gemini_service import GeminiService'
    )

# Initialize in app class
if 'self.gemini_service = GeminiService()' not in content:
    content = content.replace(
        'self.local_translator = LocalGGUFTranslator(PROJECT_ROOT)',
        'self.local_translator = LocalGGUFTranslator(PROJECT_ROOT)\n        self.gemini_service = GeminiService()'
    )

# Find the General Knowledge Fallback block we added earlier and replace it with Gemini
old_fallback = '''        # UPGRADE: GENERAL KNOWLEDGE FALLBACK
        # If the Rule Engine fails to find agricultural data, but it's NOT a dangerous query,
        # let Sarvam answer it as a general assistant.
        rule_status = rule_result.get("status")
        is_dangerous = bool(re.search(r"\\b(pesticide|insecticide|fungicide|herbicide|dosage|dose)\\b", query, flags=re.IGNORECASE))
        
        if rule_status in {"no_verified_information", "needs_clarification"} and not is_dangerous:
            logger.info(f"🧠 General Knowledge Fallback triggered for: {query}")
            system_prompt = (
                "You are AgriSathi, a helpful Indian AI assistant. "
                "The user asked a general question that is not in your agricultural database. "
                "Answer the question accurately and conversationally in 1-2 sentences. "
                "If the question is completely unrelated to farming, gently remind them you are an agricultural assistant."
            )
            try:
                llm_response = self.llm_service.generate(prompt=query, system_prompt=system_prompt, temperature=0.5)
                return {
                    "approved": True,
                    "status": "approved",
                    "language": requested_language,
                    "answer": llm_response,
                    "final_answer": llm_response,
                    "query": query,
                    "intent": "general_knowledge",
                    "parsed_query": {},
                    "sources": [],
                    "warnings": ["This is general AI knowledge, not verified agricultural data."],
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
            except Exception as e:
                logger.error(f"LLM General Knowledge failed: {e}")
                # Let it fall through to the normal error handling if LLM fails'''

new_fallback = '''        # UPGRADE: SILENT GEMINI FALLBACK
        # If the Rule Engine fails, we try Gemini before giving up.
        rule_status = rule_result.get("status")
        is_dangerous = bool(re.search(r"\\b(pesticide|insecticide|fungicide|herbicide|dosage|dose)\\b", query, flags=re.IGNORECASE))
        
        if rule_status in {"no_verified_information", "needs_clarification"} and not is_dangerous:
            logger.info(f"✨ Local RAG failed. Routing to Gemini Fallback for: {query}")
            
            system_prompt = (
                "You are AgriSathi, a friendly and knowledgeable Indian AI assistant. "
                "Answer the user's question accurately and conversationally. "
                "If they ask about farming, provide practical advice. "
                "Keep the response under 3 sentences."
            )
            
            # Try Gemini first
            gemini_response = self.gemini_service.generate(prompt=query, system_prompt=system_prompt)
            
            if gemini_response:
                return {
                    "approved": True,
                    "status": "approved",
                    "language": requested_language,
                    "answer": gemini_response,
                    "final_answer": gemini_response,
                    "query": query,
                    "intent": "general_knowledge",
                    "parsed_query": {},
                    "sources": [],
                    "warnings": [], # Hidden: We removed the visible warning so it looks seamless
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
            else:
                logger.error("Gemini fallback failed. Falling back to local Sarvam.")
                # If Gemini fails (e.g. no internet), fall back to local Sarvam as a last resort
                try:
                    llm_response = self.llm_service.generate(prompt=query, system_prompt=system_prompt, temperature=0.5)
                    return {
                        "approved": True, "status": "approved", "language": requested_language,
                        "answer": llm_response, "sources": [], "warnings": [], 
                        "safety": {"approved": True, "status": "approved"}, "timestamp": utc_timestamp(),
                    }
                except Exception:
                    pass'''

if old_fallback in content:
    content = content.replace(old_fallback, new_fallback)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ main.py patched: Silent Gemini Fallback activated.")
else:
    print("⚠️ Could not find the fallback block. Patching via regex...")
    content = re.sub(r'# UPGRADE: GENERAL KNOWLEDGE FALLBACK.*?(?=# ----------------------------------------------------\n        # E\.)', new_fallback + '\n\n        ', content, flags=re.DOTALL)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Regex fix applied.")
