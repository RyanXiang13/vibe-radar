from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import time
import json
import psycopg2
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# --- CONFIGURATION for AI & Maps ---
MAPS_KEY = os.getenv("GMAPS_KEY")
AI_KEY = os.getenv("GEMINI_API_KEY")
AI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DATABASE_URL = os.getenv("DATABASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAPS_KEY = os.getenv("GMAPS_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_coordinates_from_address(address: str):
    if not MAPS_KEY: return None
    try:
        resp = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params={"address": address, "key": MAPS_KEY})
        data = resp.json()
        if data['status'] != 'OK': return None
        loc = data['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    except: return None

# --- AI Miner Helpers ---
def get_all_reviews_text(reviews_list):
    if not reviews_list: return None
    all_text = ""
    for r in reviews_list:
        text = r.get('text', {}).get('text', '')
        if text:
            all_text += f"- {text}\n"
    return all_text[:30000]

def get_vibe_from_ai(reviews_list):
    review_context = get_all_reviews_text(reviews_list)
    if not review_context: return None

    prompt_text = f"""
    Analyze these user reviews for a Study Spot App.
    YOUR GOAL: Extract attributes for students/remote workers.
    CRITICAL INSTRUCTION: DO NOT RETURN "Unknown".
    You must INFER values based on context. 
    Review Data:
    {review_context}
    
    Return strictly VALID JSON. Return a SINGLE JSON object.
    Output format:
    {{
        "noise_level": "Quiet" | "Moderate" | "Loud",
        "wifi": "Fast" | "Spotty" | "None",
        "outlets_level": "Many" | "Scarce" | "None",
        "price_perception": "Cheap" | "Fair" | "Overpriced",
        "comfort_level": "Cozy" | "Spacious" | "Hard Seats",
        "food_type": "Full Meals" | "Pastries" | "Coffee Only",
        "best_for": ["Study", "Social", "Group Work", "Date", "Lunch"],
        "group_suitability": "Good for Groups" | "Best for Pairs" | "Solo Only",
        "is_late_night": true/false,
        "bathroom_status": "Public" | "Code Required" | "None" | "Unknown",
        "seating_tip": "Specific tip (e.g. 'Back booth has power'). Max 8 words.",
        "vibes": ["tag1", "tag2"],
        "summary": "1 short sentence summary focusing on study suitability."
    }}
    """
    
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    for attempt in range(3):
        try:
            response = requests.post(f"{AI_MODEL_URL}?key={AI_KEY}", headers=headers, json=data, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed[0]
                    elif isinstance(parsed, dict):
                        return parsed
            elif response.status_code == 429:
                 time.sleep(3)
        except Exception as e:
            print(f"AI Exception: {e}")
    return None

def search_google_places(lat: float, lng: float, radius_km: float, max_count=20):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.reviews"
    }
    body = {
        "includedTypes": ["cafe", "coffee_shop"],
        "maxResultCount": max_count,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_km * 1000.0
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Sort places by distance to center
            places = data.get('places', [])
            return places
    except Exception as e:
        print(f"❌ Google Places API Error: {e}")
    return []


# --- The Schema ---
class Vibe(BaseModel):
    summary: Optional[str]
    vibe_tags: Optional[List[str]]
    best_for: Optional[List[str]]
    
    noise_level: Optional[str]
    wifi_quality: Optional[str]
    outlets_level: Optional[str]
    comfort_level: Optional[str]
    food_type: Optional[str]
    
    seating_tip: Optional[str]
    busyness_info: Optional[str]
    group_suitability: Optional[str]
    is_late_night: Optional[bool]
    time_limit_status: Optional[str]
    bathroom_status: Optional[str]
    has_natural_light: Optional[bool]

class CafeResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    rating: Optional[float]
    price_level: Optional[int]
    lat: float
    lng: float
    vibes: Optional[Vibe]
    distance_km: Optional[float]

class CityRequest(BaseModel):
    city: str
    email: Optional[str] = None


# Database Connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ DB Connect Error: {e}")
        raise HTTPException(500, f"Database Connect Error: {e}")

@contextmanager
def get_db_cursor():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


async def cafe_stream_generator(request: Request, search_lat: float, search_lng: float, radius_km: float, limit: int):
    # 1. Yield Cached Initial cafes
    cached_ids = set()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
        SELECT 
            p.id, p.google_place_id, p.name, p.address, p.rating, p.price_level,
            ST_Y(p.location::geometry) as lat, ST_X(p.location::geometry) as lng,
            v.*, 
            (ST_Distance(p.location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000) as distance_km
        FROM places p
        LEFT JOIN place_vibes v ON p.id = v.place_id
        WHERE ST_DWithin(p.location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s * 1000)
        ORDER BY distance_km ASC LIMIT %s;
        """
        cursor.execute(query, (search_lng, search_lat, search_lng, search_lat, radius_km, limit))
        rows = cursor.fetchall()
        
        for row in rows:
            if row.get('google_place_id'):
                cached_ids.add(row['google_place_id'])
                
            vibes = None
            if row.get('summary'):
                vibes = {
                    k: row.get(k) for k in [
                        "summary", "vibe_tags", "best_for",
                        "noise_level", "wifi_quality", 
                        "outlets_level", "comfort_level", "food_type", 
                        "seating_tip", "busyness_info", "group_suitability", 
                        "is_late_night", "time_limit_status", "bathroom_status", 
                        "has_natural_light"
                    ]
                }
            
            cafe_obj = {
                **{k: row[k] for k in ["id", "name", "address", "rating", "price_level", "lat", "lng"]},
                "distance_km": round(row['distance_km'], 2),
                "vibes": vibes
            }
            yield f"data: {json.dumps(cafe_obj)}\n\n"
            
    except Exception as e:
        print(f"Stream DB Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        conn.close()
        return

    # 2. Yield Dynamic Google/Gemini Cafes
    if len(cached_ids) < limit:
        remaining = limit - len(cached_ids)
        print(f"📡 Requesting Google Places Search... (Need {remaining} more)")
        
        google_places = search_google_places(search_lat, search_lng, radius_km, max_count=20)
        
        for place in google_places:
            if await request.is_disconnected():
                break

            pid = place.get('id')
            if pid in cached_ids:
                continue # Already yielded from DB
            
            name = place.get('displayName', {}).get('text')
            print(f"  -> Mining New Place Live: {name}")
            
            # Send to AI
            vibe_data = get_vibe_from_ai(place.get('reviews', []))
            
            if vibe_data:
                # Add to DB Cache
                price_int = 1
                if place.get('priceLevel') == "PRICE_LEVEL_MODERATE": price_int = 2
                elif place.get('priceLevel') == "PRICE_LEVEL_EXPENSIVE": price_int = 3

                try:
                    cursor.execute("""
                        INSERT INTO places (google_place_id, name, address, location, rating, price_level)
                        VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                        RETURNING id;
                    """, (
                        pid, name, place.get('formattedAddress'),
                        place['location']['longitude'], place['location']['latitude'], 
                        place.get('rating'), price_int
                    ))
                    res = cursor.fetchone()
                    new_place_id = res['id'] if isinstance(res, dict) else res[0]

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
                except Exception as e:
                    print(f"Failed to save {name} to DB: {e}")
                    conn.rollback()
                    new_place_id = -1 # Fake ID for stream
                
                # Format exactly like DB
                vibes = {
                     "summary": vibe_data.get('summary'),
                     "vibe_tags": vibe_data.get('vibes', []),
                     "best_for": vibe_data.get('best_for', []),
                     "noise_level": vibe_data.get('noise_level'),
                     "wifi_quality": vibe_data.get('wifi'),
                     "outlets_level": vibe_data.get('outlets_level'),
                     "comfort_level": vibe_data.get('comfort_level'),
                     "food_type": vibe_data.get('food_type'),
                     "seating_tip": vibe_data.get('seating_tip'),
                     "busyness_info": None,
                     "group_suitability": vibe_data.get('group_suitability'),
                     "is_late_night": vibe_data.get('is_late_night'),
                     "time_limit_status": None,
                     "bathroom_status": vibe_data.get('bathroom_status'),
                     "has_natural_light": False
                }
                
                # Calc rough distance from center
                from math import radians, cos, sin, asin, sqrt
                def haversine(lon1, lat1, lon2, lat2):
                    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                    dlon = lon2 - lon1 
                    dlat = lat2 - lat1 
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a)) 
                    r = 6371 # km
                    return c * r
                
                dist = haversine(search_lng, search_lat, place['location']['longitude'], place['location']['latitude'])
                
                stream_obj = {
                    "id": new_place_id,
                    "name": name,
                    "address": place.get('formattedAddress'),
                    "rating": place.get('rating'),
                    "price_level": price_int,
                    "lat": place['location']['latitude'],
                    "lng": place['location']['longitude'],
                    "distance_km": round(dist, 2),
                    "vibes": vibes
                }
                
                yield f"data: {json.dumps(stream_obj)}\n\n"
                
    cursor.close()
    conn.close()
    yield "event: done\ndata: {}\n\n"

@app.get("/cafes")
async def get_nearby_cafes_stream(request: Request, address: Optional[str] = Query(None), lat: Optional[float] = Query(None), lng: Optional[float] = Query(None), radius_km: float = 5.0, limit: int = 50):
    search_lat, search_lng = lat, lng
    if address:
        coords = get_coordinates_from_address(address)
        if coords: search_lat, search_lng = coords
    
    if search_lat is None: 
        raise HTTPException(400, "Need location")

    return StreamingResponse(
        cafe_stream_generator(request, search_lat, search_lng, radius_km, limit), 
        media_type="text/event-stream"
    )


@app.post("/requests")
def submit_request(req: CityRequest):
    try:
        with get_db_cursor() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO city_requests (city, email) VALUES (%s, %s)", 
                    (req.city, req.email)
                )
                conn.commit()
        return {"status": "success", "message": "Request received"}
    except Exception as e:
        print(f"Request Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
