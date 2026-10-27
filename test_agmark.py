from agmarknet import Agmarknet
from datetime import date, timedelta

print("Connecting to AGMARKNET...")
api = Agmarknet()

# Fetch data for the last 2 days (in case today's data isn't uploaded yet)
start_date = str(date.today() - timedelta(days=2))
end_date = str(date.today())

try:
    df = api.report(
        from_date=start_date,
        to_date=end_date,
        commodity="Wheat",
        state="Punjab"
    )
    
    if df is not None and not df.empty:
        print("✅ SUCCESS! Here is the real data:")
        print(df[['market_name', 'min_price', 'max_price', 'model_price']].head())
    else:
        print("⚠️ API connected, but no records found for Wheat in Punjab.")
        
except Exception as e:
    print(f"❌ Error: {e}")
