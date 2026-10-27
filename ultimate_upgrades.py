import re

# ============================================================
# UPGRADE 1: Response Caching & Conversational Memory (main.py)
# ============================================================
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main = f.read()

# Add cache and memory to __init__
old_init = """        # Recommendation engine
        self.recommendation_engine = RecommendationEngine(
            llm_service=self.llm_service
        )"""
new_init = """        # Recommendation engine
        self.recommendation_engine = RecommendationEngine(
            llm_service=self.llm_service
        )
        
        # UPGRADE: Response Cache & Conversational Memory
        self.response_cache = {}
        self.last_crop_context = None"""
main = main.replace(old_init, new_init)

# Add Cache check at the start of answer()
old_start = """        query = safe_string(query)

        if not query:
            raise ValueError(
                "Please enter a question."
            )"""
new_start = """        query = safe_string(query)

        if not query:
            raise ValueError(
                "Please enter a question."
            )

        # UPGRADE: Check Response Cache
        cache_key = f"{query.lower().strip()}_{language}"
        if cache_key in self.response_cache:
            logger.info(f"⚡ Cache Hit: Returning instant response for '{query}'")
            return self.response_cache[cache_key]"""
main = main.replace(old_start, new_start)

# Add Memory injection after parsing
old_parse = """        intent = safe_string(
            inner_query.get("intent"),
            "unknown",
        )"""
new_parse = """        intent = safe_string(
            inner_query.get("intent"),
            "unknown",
        )

        # UPGRADE: Conversational Memory Injection
        entities = inner_query.get("entities", {})
        crops = entities.get("crops", [])
        
        if not crops and self.last_crop_context:
            # Inject the last crop if the user forgot to mention it
            entities["crops"] = [self.last_crop_context]
            inner_query["entities"] = entities
            query = f"{query} for {self.last_crop_context}" # Update query for LLM context
            logger.info(f"🧠 Memory used: Injecting previous crop '{self.last_crop_context}'")
        elif crops:
            # Save the current crop for future questions
            self.last_crop_context = crops[0]"""
main = main.replace(old_parse, new_parse)

# Save to cache before returning final result
old_return = """        return {
            "approved": approved,
            "status": status,
            "language": requested_language,"""
new_return = """        final_response = {
            "approved": approved,
            "status": status,
            "language": requested_language,"""
main = main.replace(old_return, new_return)

old_end_return = """            "safety": safety_result,
            "timestamp": utc_timestamp(),
        }"""
new_end_return = """            "safety": safety_result,
            "timestamp": utc_timestamp(),
        }
        
        # UPGRADE: Save to Cache
        self.response_cache[cache_key] = final_response
        return final_response"""
main = main.replace(old_end_return, new_end_return)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main)
print("✅ main.py patched: Caching & Conversational Memory added!")

# ============================================================
# UPGRADE 2: Robust Intent Parsing (engine/query_parser.py)
# ============================================================
parser_path = 'engine/query_parser.py'
with open(parser_path, 'r', encoding='utf-8') as f:
    parser = f.read()

# Add natural farmer dialect to Pest Management
old_pests = '''        "pest_management": [
            "pest", "pests", "insect", "insects", "bug", "bugs", "infestation",
            "pest control", "control pest", "control pests", "manage pest", "manage pests",
            "disease", "diseases", "fungus", "fungal", "infection", "infected",
            "yellow leaves", "yellowing leaves", "leaf spots", "wilting", "spots on leaves",
            "crop damage", "plant damage",'''
new_pests = '''        "pest_management": [
            "pest", "pests", "insect", "insects", "bug", "bugs", "infestation",
            "pest control", "control pest", "control pests", "manage pest", "manage pests",
            "disease", "diseases", "fungus", "fungal", "infection", "infected",
            "yellow leaves", "yellowing leaves", "leaf spots", "wilting", "spots on leaves",
            "crop damage", "plant damage", "dying", "sick", "holes", "holes in leaves", "brown spots",'''
parser = parser.replace(old_pests, new_pests)

with open(parser_path, 'w', encoding='utf-8') as f:
    f.write(parser)
print("✅ query_parser.py patched: Added farmer dialect keywords!")

# ============================================================
# UPGRADE 3: UI Polish - Fade-in Messages (frontend/style.css)
# ============================================================
css_path = 'frontend/style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Add fade-in animation for messages
css += """

/* UPGRADE: Smooth fade-in for chat messages */
@keyframes messageFadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-row {
    animation: messageFadeIn 0.4s ease-out forwards;
}
"""

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)
print("✅ style.css patched: Added smooth fade-in animations!")
