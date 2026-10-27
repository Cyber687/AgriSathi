import re

# --- PATCH 1: main.py (Ensure LLM is actually turned on) ---
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main = f.read()

# Force use_llm=True in the main call
main = main.replace('use_llm=False,', 'use_llm=True,')

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main)
print("✅ main.py patched: LLM is now ON for all queries.")

# --- PATCH 2: recommendation.py (The Expert Agronomist Prompt) ---
rec_path = 'engine/recommendation.py'
with open(rec_path, 'r', encoding='utf-8') as f:
    rec = f.read()

# Find the system prompt in _rephrase_with_llm
old_prompt = '''        system_prompt = (
            "You are the language rephrasing component of AgriSathi, "
            "an agricultural advisory assistant. Rewrite the supplied "
            "answer clearly in the requested language. Use only facts "
            "already present in the supplied answer and evidence. "
            "Do not add crop facts, pest diagnoses, chemical products, "
            "dosages, fertilizer quantities, weather measurements, "
            "market prices, citations, or source IDs. If information is "
            "missing, keep it missing. Return only the rewritten answer."
        )'''

new_prompt = '''        system_prompt = (
            "You are AgriSathi, a highly experienced and friendly agricultural expert speaking to a farmer. "
            "You have been provided with verified agricultural data from a government database.\\n"
            "YOUR JOB:\\n"
            "1. Read the verified data provided in the context.\\n"
            "2. Explain it to the farmer in a warm, conversational, and easy-to-understand way.\\n"
            "3. If there are technical terms (like 'CRI stage' or 'N:P:K'), briefly explain what they mean in simple terms.\\n"
            "4. Use bullet points or short paragraphs to make it readable.\\n"
            "5. End with a helpful, encouraging note.\\n\\n"
            "STRICT RULES:\\n"
            "- You MUST NOT invent any facts, chemicals, dosages, or prices that are not in the provided context.\\n"
            "- If the context does not contain the answer, say: 'I don't have verified information on this specific detail.'\\n"
            "- Return ONLY the final response to the farmer. Do not include 'Here is the rewritten text:'."
        )'''

if old_prompt in rec:
    rec = rec.replace(old_prompt, new_prompt)
    print("✅ recommendation.py patched: Expert Agronomist Prompt activated.")
else:
    # If exact match fails, try regex
    rec = re.sub(r'system_prompt = \(.*?\)', f'system_prompt = {repr(new_prompt)}', rec, flags=re.DOTALL)
    print("✅ recommendation.py patched via Regex.")

with open(rec_path, 'w', encoding='utf-8') as f:
    f.write(rec)

# --- PATCH 3: llm_service.py (Increase max tokens for richer answers) ---
llm_path = 'services/llm_service.py'
with open(llm_path, 'r', encoding='utf-8') as f:
    llm = f.read()

# Increase from 512 to 1024 so the LLM doesn't cut off mid-sentence
llm = llm.replace('max_tokens: int = 512', 'max_tokens: int = 1024')

with open(llm_path, 'w', encoding='utf-8') as f:
    f.write(llm)
print("✅ llm_service.py patched: Max tokens increased to 1024.")
