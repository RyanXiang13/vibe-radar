import sys
import os
import requests
import psycopg2
import json
import time
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
MAPS_KEY = os.getenv("GMAPS_KEY")
AI_KEY = os.getenv("GEMINI_API_KEY")
# Using the stable Flash model for consistent JSON
AI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

if not MAPS_KEY or not AI_KEY:
    print("❌ ERROR: Missing Keys in .env")
    exit(1)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

def get_vibe_from_ai(reviews_list):
    """
    Sends reviews to Gemini to extract structured 'Student Intel' data.
    """
    if not reviews_list: return None
    
    # Combine reviews into one block
    reviews_text = "\n".join([r.get('text', {}).get('text', '') for r in reviews_list])
    if len(reviews_text) < 50: return None

    # 🧠 THE MASTER PROMPT (Student Survival Guide)
    prompt_text = f"""
    Analyze these reviews for a student study spot app.
    Return strictly VALID JSON. No markdown.
    
    Reviews: {reviews_text[:4000]} 
    
    Output format:
    {{
        "noise_level": "Quiet" | "Moderate" | "Loud",
        "wifi": "Fast" | "Spotty" | "None",
        "outlets_level": "Many" | "Scarce" | "None",
        "comfort_level": "Cozy" | "Spacious" | "Hard Seats",
        "food_type": "Full Meals" | "Pastries" | "Coffee Only",
        
        "best_for": ["Study", "Social", "Group Work", "Date", "Lunch"],
        "group_suitability": "Good for Groups" | "Best for Pairs" | "Solo Only",
        "seating_tip": "Specific tip (e.g. 'Basement is quiet'). Max 8 words.",
        "busyness_info": "Crowd pattern (e.g. 'Packed Sat 2pm'). Max 8 words.",
        
        "is_late_night": true/false (True if reviews mention being open late or good for evenings),
        "time_limit_status": "None" | "Strict" | "Weekends Only" | "Unknown",
        "bathroom_status": "Public" | "Code Required" | "None" | "Unknown",
        "has_natural_light": true/false (Look for 'bright', 'sunny', 'windows'),
        
        "vibes": ["tag1", "tag2"],
        "summary": "1 short sentence summary."
    }}
    """
    
    headers = {"Content-Type": "application/json"}
    data = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    
    # Retry logic
    for attempt in range(3):
        try:
            response = requests.post(f"{AI_MODEL_URL}?key={AI_KEY}", headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_json)
            elif response.status_code == 429:
                 print(f"     ⚠️ AI Rate Limit. Sleeping 5s... (Attempt {attempt+1})")
                 time.sleep(5)
        except Exception as e:
            print(f"AI Exception: {e}")
            
    return None

def search_places_batch(query_text, max_count=20):
    """
    Uses Google Places API (New) v1 to get details + reviews in ONE single call.
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.reviews"
    }
    body = {"textQuery": query_text, "pageSize": max_count}
    
    print(f"📡 Sending Batch Maps Request for: '{query_text}'...")
    response = requests.post(url, headers=headers, json=body)
    return response.json().get('places', []) if response.status_code == 200 else []

def mine_places(location_query, limit=20):
    # 1. Get Batch Data (The "Budget King" Method)
    places = search_places_batch(location_query, max_count=limit)
    
    if not places:
        print("⚠️ No places found.")
        return

    print(f"✅ Received {len(places)} places via Batch API. Processing Vibes...")
    
    for place in places:
        pid = place.get('id')
        name = place.get('displayName', {}).get('text')
        
        # Check DB
        cursor.execute("SELECT id FROM places WHERE google_place_id = %s", (pid,))
        if cursor.fetchone():
            print(f"  -> {name} (Skipping: Already in DB)")
            continue
            
        print(f"  -> Processing: {name}")
        vibe_data = get_vibe_from_ai(place.get('reviews', []))
        
        if not vibe_data:
            print("     (Skipping: AI Failed)")
            continue

        # Extract & Normalize basic info
        price_int = 1
        if place.get('priceLevel') == "PRICE_LEVEL_MODERATE": price_int = 2
        elif place.get('priceLevel') == "PRICE_LEVEL_EXPENSIVE": price_int = 3
        
        # 2. SQL Insert Place
        cursor.execute("""
            INSERT INTO places (google_place_id, name, address, location, rating, price_level)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
            RETURNING id;
        """, (
            pid, name, place.get('formattedAddress'),
            place['location']['longitude'], place['location']['latitude'], 
            place.get('rating'), price_int
        ))
        
        new_place_id = cursor.fetchone()[0]

        # 3. SQL Insert Vibes (The "Student Intel" Columns)
        cursor.execute("""
            INSERT INTO place_vibes 
            (place_id, vibe_tags, best_for, noise_level, wifi_quality, outlets_level, comfort_level, 
             food_type, seating_tip, busyness_info, group_suitability,
             summary, is_late_night, time_limit_status, bathroom_status, has_natural_light)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            new_place_id, 
            vibe_data.get('vibes', []), 
            vibe_data.get('best_for', []),
            vibe_data.get('noise_level'), 
            vibe_data.get('wifi'),
            vibe_data.get('outlets_level'),
            vibe_data.get('comfort_level'),
            vibe_data.get('food_type'),
            vibe_data.get('seating_tip'),
            vibe_data.get('busyness_info'),
            vibe_data.get('group_suitability'),
            vibe_data.get('summary'),
            vibe_data.get('is_late_night'),
            vibe_data.get('time_limit_status'),
            vibe_data.get('bathroom_status'),
            vibe_data.get('has_natural_light')
        ))
        
        conn.commit()
        print("     ✅ Saved!")
        time.sleep(1)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Cafes in Waterloo, ON"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    # Ensure "Cafes in" is present if user just typed a city
    full_query = query if "Cafes" in query or "Study" in query else f"Cafes in {query}"
    
    mine_places(full_query, limit)
    cursor.close()
    conn.close()