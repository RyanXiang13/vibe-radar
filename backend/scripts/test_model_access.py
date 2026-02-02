import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
AI_KEY = os.getenv("GEMINI_API_KEY")

print(f"🔑 Testing Key: {AI_KEY[:5]}...{AI_KEY[-5:]}")

# The 3 candidates for 2026:
MODELS_TO_TEST = [
    "gemini-2.5-flash-lite",      # The new budget standard (Most likely to work)
    "gemini-2.5-flash",           # The standard 2026 model
    "gemini-1.5-flash",           # The old reliable (if still active)
    "gemini-1.5-flash-latest"     # Alias sometimes used
]

prompt_text = "Just say 'Hello'."

headers = {"Content-Type": "application/json"}
data = { "contents": [{ "parts": [{"text": prompt_text}] }] }

print("\n--- BEGIN MODEL AUDIT ---")

for model in MODELS_TO_TEST:
    print(f"\n📡 Pinging: {model} ...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={AI_KEY}"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! This is your model.")
            print(f"   Response: {response.json()['candidates'][0]['content']['parts'][0]['text'].strip()}")
            print(f"   >>> USE THIS MODEL NAME IN MINER.PY <<<")
            break # Stop at the first working one
            
        elif response.status_code == 404:
            print("   ❌ 404 Not Found (Model does not exist or key has no access)")
            
        elif response.status_code == 429:
            print("   ⚠️  429 Quota Exceeded (Model exists, but you have 0 free limit)")
            
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"   Connection Failed: {e}")

print("\n--- END AUDIT ---")