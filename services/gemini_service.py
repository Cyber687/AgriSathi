import os
import time
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agrisathi")

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                # We will use a primary and a fallback model to handle high demand
                self.primary_model = 'gemini-3.8-flash'
                self.fallback_model = 'gemini-3.5-flash' 
                logger.info("✨ Gemini Fallback Service Initialized.")
            except Exception as e:
                self.client = None
                logger.error(f"Failed to initialize Gemini: {e}")
        else:
            self.client = None
            logger.warning("⚠️ GEMINI_API_KEY not found. Fallback disabled.")

    def generate(self, prompt, system_prompt=None):
        if not self.client:
            return None
            
        full_prompt = f"System Instructions: {system_prompt}\\n\\nUser Query: {prompt}" if system_prompt else prompt
        
        # Try the primary model with exponential backoff (3 attempts)
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=full_prompt,
                    request_options={'timeout': 10.0}
                )
                return response.text.strip()
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    wait_time = 2 ** attempt
                    logger.warning(f"Model {self.primary_model} is busy. Retrying in {wait_time}s... (Attempt {attempt+1}/3)")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini API Error: {e}")
                    break # Break on non-503 errors (e.g., invalid key)

        # If the primary model failed after retries, try the fallback model
        logger.info(f"Switching to fallback model: {self.fallback_model}")
        try:
            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=full_prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Fallback model also failed: {e}")
            return None
