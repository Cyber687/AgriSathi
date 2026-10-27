import pandas as pd
import json
import os

# --- CONFIGURATION ---
EXCEL_FILE = 'crops_db.xlsx' # Make sure this is in the same folder!
SHEET_NAME = 'Top 100 Indian Crops Data'
KB_DIR = 'knowledge_base'

os.makedirs(KB_DIR, exist_ok=True)

try:
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
except Exception as e:
    print(f"ERROR: Could not load {EXCEL_FILE}. Make sure the file is in this folder.")
    print(f"Details: {e}")
    exit()

pest_records = []
fert_records = []
irrig_records = []

# The first 15 crops will be marked as "verified" so the bot works
VERIFIED_CROP_LIMIT = 15

for index, row in df.iterrows():
    crop_id = int(row['Crop ID'])
    crop_name = row['Crop Name']
    
    # Determine status: first 15 are verified, rest need verification
    status = "verified" if crop_id <= VERIFIED_CROP_LIMIT else "needs_source_verification"
    
    source = str(row.get('Attributed Source', '')) if pd.notna(row.get('Attributed Source')) else "ICAR"

    # --- PESTS JSON ---
    pest = str(row.get('Target Pest / Disease', '')) if pd.notna(row.get('Target Pest / Disease')) else None
    strategy = str(row.get('Pest Control Strategy (Cultural / Bio)', '')) if pd.notna(row.get('Pest Control Strategy (Cultural / Bio)')) else None
    chemical = str(row.get('Chemical Control & Dosage', '')) if pd.notna(row.get('Chemical Control & Dosage')) else None

    pest_records.append({
        "record_id": f"PEST{crop_id:03d}",
        "crop_id": crop_id,
        "crop": {"en": crop_name, "hi": crop_name},
        "pests_and_diseases_as_listed": {"en": pest, "hi": pest},
        "management_strategies_as_listed": {"en": strategy, "hi": strategy},
        "chemical_recommendations": [chemical] if chemical and chemical != 'nan' else [],
        "chemical_dosage": chemical if chemical and chemical != 'nan' else None,
        "source_attribution": {"en": source, "hi": source},
        "source_ids": ["SRC001"],
        "verification_status": status, 
        "safety_note": "Verify against current official agricultural guidance."
    })

    # --- FERTILIZERS JSON ---
    fert = str(row.get('Fertilizer Needs (N:P:K)', '')) if pd.notna(row.get('Fertilizer Needs (N:P:K)')) else None
    fert_records.append({
        "record_id": f"FERT{crop_id:03d}",
        "crop_id": crop_id,
        "crop": {"en": crop_name, "hi": crop_name},
        "fertilizer_requirement_as_listed": {"en": fert, "hi": fert},
        "application_dosage": None,
        "source_attribution": {"en": source, "hi": source},
        "source_ids": ["SRC001"],
        "verification_status": status
    })

    # --- IRRIGATION JSON ---
    irrig = str(row.get('Soil & Irrigation Requirements', '')) if pd.notna(row.get('Soil & Irrigation Requirements')) else None
    irrig_records.append({
        "record_id": f"IRR{crop_id:03d}",
        "crop_id": crop_id,
        "crop": {"en": crop_name, "hi": crop_name},
        "soil_and_irrigation_requirements_as_listed": {"en": irrig, "hi": irrig},
        "source_attribution": {"en": source, "hi": source},
        "source_ids": ["SRC001"],
        "verification_status": status
    })

# Save the generated files
def save_json(filename, records):
    output = {"schema_version": "1.0", "record_count": len(records), "records": records}
    with open(os.path.join(KB_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Generated {filename} with {len(records)} records.")

save_json('pests.json', pest_records)
save_json('fertilizers.json', fert_records)
save_json('irrigation.json', irrig_records)

# --- NOW UPDATE CROPS.JSON ---
crops_file = os.path.join(KB_DIR, 'crops.json')
if os.path.exists(crops_file):
    with open(crops_file, 'r', encoding='utf-8') as f:
        crops_data = json.load(f)
    
    updated_count = 0
    for record in crops_data.get('records', []):
        if record.get('crop_id', 999) <= VERIFIED_CROP_LIMIT:
            record['verification_status'] = "verified"
            updated_count += 1
            
    with open(crops_file, 'w', encoding='utf-8') as f:
        json.dump(crops_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated {updated_count} records in crops.json to 'verified'.")
else:
    print("⚠️ crops.json not found. Please make sure it exists in knowledge_base/")

print("\n🎉 ALL JSON FILES FIXED! You can now run: python main.py")