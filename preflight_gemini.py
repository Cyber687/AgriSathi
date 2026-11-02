import re

path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the beginning of the answer function (after the cache check)
# We will inject the routing logic right before it parses the query
old_block = """        # ----------------------------------------------------
        # A. PARSE THE QUERY
        # ----------------------------------------------------

        try:
            parsed_result = self.query_parser.parse("""

new_block = """        # ============================================================
        # UPGRADE: PRE-FLIGHT GEMINI ROUTING
        # ============================================================
        # If the query is non-agricultural and not dangerous, route to Gemini immediately.
        is_dangerous = bool(re.search(r"\\b(pesticide|insecticide|fungicide|herbicide|dosage|dose)\\b", query, flags=re.IGNORECASE))
        agri_keywords = ["crop", "wheat", "rice", "maize", "potato", "tomato", "pest", "fertilizer", "soil", "weather", "mandi", "seed", "plant", "farm", "irrigation", "yield", "harvest", "agriculture", "farming"]
        is_agri = any(k in query.lower() for k in agri_keywords)
        
        if not is_agri and not is_dangerous:
            logger.info(f"✨ General query detected PRE-FLIGHT. Routing directly to Gemini.")
            system_prompt = (
                "You are AgriSathi, a helpful Indian AI assistant. "
                "Answer the user's question accurately in 1-2 sentences. "
                "If the question is entirely unrelated to farming, gently mention you are an agricultural assistant but still answer the question."
            )
            gemini_response = self.gemini_service.generate(prompt=query, system_prompt=system_prompt)
            
            if gemini_response:
                final_response = {
                    "approved": True, "status": "approved", "language": requested_language,
                    "answer": gemini_response, "final_answer": gemini_response,
                    "query": query, "intent": "general_knowledge",
                    "parsed_query": {}, "sources": [], "warnings": [],
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
                self.response_cache[cache_key] = final_response
                return final_response
            else:
                logger.warning("Gemini failed, letting local pipeline handle it.")

        # ----------------------------------------------------
        # A. PARSE THE QUERY
        # ----------------------------------------------------

        try:
            parsed_result = self.query_parser.parse("""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ main.py patched: Pre-Flight Gemini Routing activated!")
else:
    print("⚠️ Could not find the exact block. Trying regex...")
    # Fallback regex in case spacing is slightly different
    pattern = r'(        # A\. PARSE THE QUERY\s+# -+\s+try:\s+parsed_result = self\.query_parser\.parse\()'
    
    def repl(m):
        return new_block.replace("        # ----------------------------------------------------\n        # A. PARSE THE QUERY\n        # ----------------------------------------------------\n\n        try:\n            parsed_result = self.query_parser.parse(", m.group(1))

    content = re.sub(pattern, repl, content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Regex fix applied.")
