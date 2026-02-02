import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We try BOTH keys to see which one works
keys_to_test = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "GMAPS_KEY": os.getenv("GMAPS_KEY"),
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY")
}

print("🔍 STARTING DIAGNOSTIC...\n")

for name, key in keys_to_test.items():
    if not key:
        print(f"⚠️  {name} is MISSING or Empty.")
        continue
        
    masked_key = f"{key[:5]}...{key[-5:]}"
    print(f"🔑 Testing {name}: {masked_key}")
    
    # 1. The URL that lists models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! This key is valid for AI.")
            print("   Available Models:")
            # Filter for the Flash model we want
            flash_models = [m['name'] for m in data.get('models', []) if 'flash' in m['name']]
            for m in flash_models:
                print(f"      - {m}")
            if not flash_models:
                print("      (No 'flash' models found, but key works. List is too long to print all.)")
        else:
            # Print the RAW error from Google
            error_msg = data.get('error', {}).get('message', 'Unknown Error')
            print(f"   ❌ FAILED. Status: {response.status_code}")
            print(f"   Reason: {error_msg}")
            
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR: {e}")
    
    print("-" * 40)