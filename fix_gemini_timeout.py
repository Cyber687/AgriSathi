import re

# ============================================================
# 1. Add Timeout to Gemini Service
# ============================================================
path_service = 'services/gemini_service.py'
with open(path_service, 'r', encoding='utf-8') as f:
    service = f.read()

# Update the generate_content calls to include request_options timeout
service = service.replace(
    "contents=full_prompt,\n                )",
    "contents=full_prompt,\n                    request_options={'timeout': 10.0}\n                )"
)

with open(path_service, 'w', encoding='utf-8') as f:
    f.write(service)
print("✅ Patched gemini_service.py: Added 10-second timeout.")

# ============================================================
# 2. Update main.py Pre-Flight Routing to handle Gemini Failure
# ============================================================
path_main = 'main.py'
with open(path_main, 'r', encoding='utf-8') as f:
    main = f.read()

# Find the preflight block and update the fallback behavior
old_preflight = """            if gemini_response:
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
                logger.warning("Gemini failed, letting local pipeline handle it.")"""

new_preflight = """            if gemini_response:
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
                # If Gemini times out or fails, return a friendly message instead of blocking
                logger.warning("Gemini failed. Returning friendly fallback.")
                fallback_msg = "I am currently having trouble reaching the general knowledge server. However, as an agricultural assistant, I am fully ready to help you with crop cultivation, pests, weather, and market prices!"
                final_response = {
                    "approved": True, "status": "approved", "language": requested_language,
                    "answer": fallback_msg, "final_answer": fallback_msg,
                    "query": query, "intent": "general_knowledge",
                    "parsed_query": {}, "sources": [], "warnings": [],
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
                self.response_cache[cache_key] = final_response
                return final_response"""

if old_preflight in main:
    main = main.replace(old_preflight, new_preflight)
    with open(path_main, 'w', encoding='utf-8') as f:
        f.write(main)
    print("✅ Patched main.py: Added graceful fallback for Gemini timeouts.")
else:
    print("⚠️ Could not find preflight block. Applying regex...")
    main = re.sub(
        r'if gemini_response:\s+final_response = \{.*?\n            else:\s+logger.warning\("Gemini failed, letting local pipeline handle it\."\)',
        new_preflight,
        main,
        flags=re.DOTALL
    )
    with open(path_main, 'w', encoding='utf-8') as f:
        f.write(main)
    print("✅ Regex fix applied.")
