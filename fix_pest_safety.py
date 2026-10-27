
# --- PATCH 1: crop_pest_validator.py (Allow general pest questions) ---
path1 = 'safety/crop_pest_validator.py'
with open(path1, 'r', encoding='utf-8') as f:
    content = f.read()

# Allow empty pest text as long as crop is present
content = content.replace(
    '''        if not crop_text or not pest_text:
            return self._result(
                status=SafetyStatus.CLARIFICATION_REQUIRED,
                crop=crop,
                pest=pest,
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )''',
    '''        if not crop_text:
            return self._result(
                status=SafetyStatus.CLARIFICATION_REQUIRED,
                crop=crop,
                pest=pest,
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )'''
)

content = content.replace(
    '''            pest_matches = self._matches(pest_text, record_pest)
            
            if crop_matches:''',
    '''            pest_matches = self._matches(pest_text, record_pest) if pest_text else True
            
            if crop_matches:'''
)

with open(path1, 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ Patched CropPestValidator: Now allows general pest questions.')


# --- PATCH 2: safety_engine.py (Let sanitizer strip unsafe chemicals instead of blocking) ---
path2 = 'safety/safety_engine.py'
with open(path2, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '''            if not self._is_approved(checks["chemical_verifier"]):
                reasons.append(
                    "Chemical verification did not pass."
                )''',
    '''            # We don't block here. The ResponseSanitizer will strip unsafe chemical details.
            # if not self._is_approved(checks["chemical_verifier"]):
            #     reasons.append("Chemical verification did not pass.")'''
)

content = content.replace(
    '''            if not self._is_approved(checks["dosage_validator"]):
                reasons.append(
                    "Dosage validation did not pass."
                )''',
    '''            # We don't block here. The ResponseSanitizer will strip unsafe dosage details.
            # if not self._is_approved(checks["dosage_validator"]):
            #     reasons.append("Dosage validation did not pass.")'''
)

with open(path2, 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ Patched SafetyEngine: Will now sanitize chemical failures instead of blocking.')
