import pandas as pd
import json
import os

# Change this to your actual Excel file name
EXCEL_FILE = 'crops_db.xlsx' 
SHEET_NAME = 'Top 100 Indian Crops Data'
OUTPUT_DIR = 'knowledge_base'

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
except Exception as e:
    print(f"Error loading Excel: {e}")
    print("Make sure the file name and sheet name match exactly.")
    exit()

pest_records = []
fert_records = []
irrig_records = []

for _, row in df.iterrows():
    crop_id = int(row['Crop ID'])
    crop_name = row['Crop Name']
    
    # --- PESTS JSON ---
    pest = str(row.get('Target Pest / Disease', '')) if pd.notna(row.get('Target Pest / Disease')) else None
    strategy = str(row.get('Pest Control Strategy (Cultural / Bio)', '')) if pd.notna(row.get('Pest Control Strategy (Cultural / Bio)')) else None
    chemical = str(row.get('Chemical Control & Dosage', '')) if pd.notna(row.get('Chemical Control & Dosage')) else None
    source = str(row.get('Attributed Source', '')) if pd.notna(row.get('Attributed Source')) else None

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
        "verification_status": "needs_source_verification", 
        "safety_note": "Verify against current official agricultural guidance."
    })

    # --- FERTILIZERS JSON ---
    fert = str(row.get('Fertilizer Needs (N:P:K)', '')) if pd.notna(row.get('Fertilizer Needs (N:P:K)')) else None
    
    fert_records.append({
        "record_id": f"FERT{crop_id:03d}",
        "crop_id": crop_id,
        "crop": {"en": crop_name, "hi": crop_name},
        "fertilizer_requirement_as_listed": {"en": fert, "hi": fert},
        "nutrient_basis": "N:P:K as stated in source spreadsheet",
        "application_dosage": None,
        "source_attribution": {"en": source, "hi": source},
        "source_ids": ["SRC001"],
        "verification_status": "needs_source_verification"
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
        "verification_status": "needs_source_verification"
    })

# Save all three files
def save_json(filename, records):
    output = {
        "schema_version": "1.0",
        "record_count": len(records),
        "records": records
    }
    with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated {filename} with {len(records)} records!")

save_json('pests.json', pest_records)
save_json('fertilizers.json', fert_records)
save_json('irrigation.json', irrig_records)