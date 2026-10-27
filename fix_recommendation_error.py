path = 'engine/recommendation.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the unsafe variables with a safe fallback directly from the query dict
old_ret = '''            "answer": answer,
            "crop": crop_val,
            "target_pest": pest_val,
            "evidence": evidence,'''

new_ret = '''            "answer": answer,
            "crop": query.get("entities", {}).get("crops", [None])[0] if query.get("entities", {}).get("crops") else None,
            "target_pest": query.get("entities", {}).get("pests", [None])[0] if query.get("entities", {}).get("pests") else None,
            "evidence": evidence,'''

if old_ret in content:
    content = content.replace(old_ret, new_ret)
    print('✅ Fixed NameError in recommendation.py!')
else:
    print('⚠️ Could not find the exact return block. Trying regex...')
    import re
    content = re.sub(r'"crop": crop_val,', '"crop": query.get("entities", {}).get("crops", [None])[0] if query.get("entities", {}).get("crops") else None,', content)
    content = re.sub(r'"target_pest": pest_val,', '"target_pest": query.get("entities", {}).get("pests", [None])[0] if query.get("entities", {}).get("pests") else None,', content)
    print('✅ Regex fix applied!')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
