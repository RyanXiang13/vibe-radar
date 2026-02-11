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
AI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

if not MAPS_KEY or not AI_KEY:
    print("❌ ERROR: Missing Keys in .env")
    exit(1)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

def get_all_reviews_text(reviews_list):
    """
    Combines ALL reviews into a single block of text.
    No filtering. No keywords. Pure raw data for the AI.
    """
    if not reviews_list: return None
    
    all_text = ""
    for r in reviews_list:
        text = r.get('text', {}).get('text', '')
        if text:
            all_text += f"- {text}\n"
            
    # Hard limit to ~30k characters to avoid hitting the absolute max token limit (approx 7-8k tokens)
    # Gemini 2.0 Flash has a huge window, but let's be safe.
    return all_text[:30000]

def get_vibe_from_ai(reviews_list):
    """
    Sends FULL review context to Gemini for aggressive inference.
    """
    review_context = get_all_reviews_text(reviews_list)
    if not review_context: return None

    # Analysis Prompt
    prompt_text = f"""
    Analyze these user reviews for a Study Spot App.
    
    YOUR GOAL: Extract attributes for students/remote workers.
    CRITICAL INSTRUCTION: DO NOT RETURN "Unknown".
    
    You must INFER values based on context. 
    Examples:
    - "People working on laptops" -> Implies 'Outlets: Many' and 'Wifi: Fast'.
    - "Great place to write my essay" -> Implies 'Noise: Moderate' or 'Quiet'.
    - "Expensive latte" -> Implies 'Price: Pricey'.
    - "Stayed for 4 hours" -> Implies 'Comfort: Cozy'.
    
    Review Data:
    {review_context}
    
    Return strictly VALID JSON.
    Return a SINGLE JSON object (not a list).
    Output format:
    {{
        "noise_level": "Quiet" | "Moderate" | "Loud",  <-- Make a guess!
        "wifi": "Fast" | "Spotty" | "None",            <-- Infer this!
        "outlets_level": "Many" | "Scarce" | "None",   <-- Look for 'laptops'!
        "price_perception": "Cheap" | "Fair" | "Overpriced",
        "comfort_level": "Cozy" | "Spacious" | "Hard Seats",
        "food_type": "Full Meals" | "Pastries" | "Coffee Only",
        
        "best_for": ["Study", "Social", "Group Work", "Date", "Lunch"],
        "group_suitability": "Good for Groups" | "Best for Pairs" | "Solo Only",
        
        "is_late_night": true/false (True if reviews mention being open late or good for evenings),
        "bathroom_status": "Public" | "Code Required" | "None" | "Unknown",
        "seating_tip": "Specific tip (e.g. 'Back booth has power'). Max 8 words.",
        
        "vibes": ["tag1", "tag2"],
        "summary": "1 short sentence summary focusing on study suitability."
    }}
    """
    
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    # Retry logic
    for attempt in range(3):
        try:
            response = requests.post(f"{AI_MODEL_URL}?key={AI_KEY}", headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
                    
                    # Handle case where AI returns a list [ {...} ]
                    if isinstance(parsed, list):
                        if len(parsed) > 0 and isinstance(parsed[0], dict):
                            return parsed[0]
                        else:
                            return None # Invalid list structure
                            
                    return parsed
            elif response.status_code == 429:
                 print(f"     ⚠️ AI Rate Limit. Sleeping 5s... (Attempt {attempt+1})")
                 time.sleep(5)
        except Exception as e:
            print(f"AI Exception: {e}")
            
    return None

def search_places_batch(query_text, max_count=20):
    """
    Uses Google Places API (New) v1 to get details + reviews.
    Handles pagination to fetch up to 'max_count' results.
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.reviews,nextPageToken"
    }
    
    all_places = []
    page_token = None
    
    print(f"📡 Sending Batch Maps Request for: '{query_text}' (Target: {max_count})...")
    
    while len(all_places) < max_count:
        # Request up to 20 at a time (API Limit)
        current_page_size = min(20, max_count - len(all_places))
        
        body = {"textQuery": query_text, "pageSize": current_page_size}
        if page_token:
            body["pageToken"] = page_token
            
        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 200:
                print(f"❌ Maps API Error: {response.text}")
                break
                
            data = response.json()
            places = data.get('places', [])
            all_places.extend(places)
            
            page_token = data.get('nextPageToken')
            if not page_token or len(all_places) >= max_count:
                break
                
            # Short sleep to be nice to the API (sometimes needed for token availability)
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Network Error: {e}")
            break
            
    return all_places

def mine_places(location_query, limit=20):
    # 1. Get Batch Data
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

        # 3. SQL Insert Vibes
        cursor.execute("""
            INSERT INTO place_vibes 
            (place_id, vibe_tags, best_for, noise_level, wifi_quality, outlets_level, comfort_level, 
             food_type, seating_tip, busyness_info, group_suitability,
             summary, is_late_night, time_limit_status, bathroom_status, has_natural_light, price_perception)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
            None,
            vibe_data.get('group_suitability'),
            vibe_data.get('summary'),
            vibe_data.get('is_late_night'),
            None, # time_limit_status
            vibe_data.get('bathroom_status'),
            False,
            vibe_data.get('price_perception')
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