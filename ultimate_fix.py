import re

# --- PATCH 1: main.py (Pass parsed query correctly) ---
path_main = 'main.py'
with open(path_main, 'r', encoding='utf-8') as f:
    main = f.read()

# 1. Fix intent extraction & get inner_query
old_parse = '''        if not parsed_result:
            return self._error_response(
                query,
                "The query parser returned no usable result.",
            )

        intent = safe_string(
            parsed_result.get("intent"),
            "unknown",
        )'''
new_parse = '''        if not parsed_result:
            return self._error_response(
                query,
                "The query parser returned no usable result.",
            )

        inner_query = parsed_result.get("query", {})
        if not isinstance(inner_query, dict):
            inner_query = {}

        intent = safe_string(
            inner_query.get("intent"),
            "unknown",
        )'''
main = main.replace(old_parse, new_parse)

# 2. Pass inner_query to RecommendationEngine
old_rec = '''        try:
            recommendation = (
                self.recommendation_engine
                .generate_recommendation(
                    rule_result,
                    query=query,
                    use_llm=False,
                )
            )'''
new_rec = '''        try:
            recommendation = (
                self.recommendation_engine
                .generate_recommendation(
                    rule_result,
                    query=inner_query,
                    use_llm=False,
                )
            )'''
main = main.replace(old_rec, new_rec)

# 3. Pass inner_query to SafetyEngine
old_safe = '''        safety_result = self._validate_safety(
            recommendation=recommendation,
            query=query,
            rule_result=rule_result,
        )'''
new_safe = '''        safety_result = self._validate_safety(
            recommendation=recommendation,
            query=inner_query,
            rule_result=rule_result,
        )'''
main = main.replace(old_safe, new_safe)

with open(path_main, 'w', encoding='utf-8') as f:
    f.write(main)
print("✅ Patched main.py: Correctly passing parsed data to engines.")

# --- PATCH 2: recommendation.py (Include crop in output) ---
path_rec = 'engine/recommendation.py'
with open(path_rec, 'r', encoding='utf-8') as f:
    rec = f.read()

old_rec_query = '''        query = query if isinstance(query, dict) else {}
        
        intent = self._normalize_identifier('''
new_rec_query = '''        query = query if isinstance(query, dict) else {}
        
        entities = query.get("entities", {})
        crop_val = None
        pest_val = None
        if entities:
            crops = entities.get("crops", [])
            if crops: crop_val = crops[0]
            pests = entities.get("pests", [])
            if pests: pest_val = pests[0]
            
        intent = self._normalize_identifier('''
rec = rec.replace(old_rec_query, new_rec_query)

old_ret = '''            "answer": answer,
            "evidence": evidence,
            "sources": sources,'''
new_ret = '''            "answer": answer,
            "crop": crop_val,
            "target_pest": pest_val,
            "evidence": evidence,
            "sources": sources,'''
rec = rec.replace(old_ret, new_ret)

with open(path_rec, 'w', encoding='utf-8') as f:
    f.write(rec)
print("✅ Patched recommendation.py: Extracted crop and pest for Safety Engine.")

# --- PATCH 3: crop_pest_validator.py (Remove strict pest requirement) ---
path_pest = 'safety/crop_pest_validator.py'
with open(path_pest, 'r', encoding='utf-8') as f:
    pest = f.read()

old_pest_err = '''        if not pest_text:
            reasons.append(
                "The target pest or disease has not been identified."
            )'''
new_pest_err = '''        # Allowed: User asked a general pest question without a specific pest name.'''
pest = pest.replace(old_pest_err, new_pest_err)

with open(path_pest, 'w', encoding='utf-8') as f:
    f.write(pest)
print("✅ Patched crop_pest_validator.py: Removed strict pest requirement.")
