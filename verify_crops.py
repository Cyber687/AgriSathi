import json
import os

# Path to your crops.json
KB_DIR = 'knowledge_base'
CROPS_FILE = os.path.join(KB_DIR, 'crops.json')

if not os.path.exists(CROPS_FILE):
    print(f"File not found: {CROPS_FILE}")
    exit()

with open(CROPS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Change the first 15 records to "verified"
count = 0
for record in data.get('records', []):
    if count < 15:
        record['verification_status'] = "verified"
        count += 1
    else:
        break

with open(CROPS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Successfully marked {count} crops as 'verified' in crops.json!")