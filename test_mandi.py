import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DATA_GOV_IN_API_KEY")

print(f"Testing with API Key: {api_key}\n")

url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
params = {
    "api-key": api_key,
    "format": "json",
    "limit": 3,
    "filters[commodity]": "Wheat",
    "filters[state]": "Punjab"
}

print("Sending request to data.gov.in...")
try:
    response = requests.get(url, params=params, timeout=15)
    print(f"HTTP Status: {response.status_code}")
    
    data = response.json()
    print("\n--- API RESPONSE ---")
    
    if "error" in data or "status" in data and data["status"] != "success":
         print(f"Error from API: {data}")
    else:
         records = data.get("records", [])
         print(f"Records found: {len(records)}")
         if records:
             print(f"First record: {records[0]}")
         else:
             print("The API returned 0 records. The key is valid, but the query didn't match any data.")
             print(f"Total records available for this query: {data.get('total')}")
             
except Exception as e:
    print(f"Request failed: {e}")
