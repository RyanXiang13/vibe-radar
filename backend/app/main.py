from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import psycopg2

from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

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

# --- The Schema ---
class Vibe(BaseModel):
    summary: Optional[str]
    vibe_tags: Optional[List[str]]
    best_for: Optional[List[str]] # <--- This was missing in the extractor below
    
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


# Initialize Connection Pool
try:
    postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        dsn=DATABASE_URL
    )
    print("✅ Database Connection Pool Created")
except Exception as e:
    print(f"❌ Error creating pool: {e}")
    postgreSQL_pool = None

@contextmanager
def get_db_connection():
    if not postgreSQL_pool:
        raise HTTPException(500, "Database pool not initialized")
    
    conn = postgreSQL_pool.getconn()
    try:
        yield conn
    finally:
        postgreSQL_pool.putconn(conn)

@app.on_event("shutdown")
def shutdown_event():
    if postgreSQL_pool:
        postgreSQL_pool.closeall()
        print("🛑 Database Pool Closed")

@app.get("/cafes", response_model=List[CafeResponse])
def get_nearby_cafes(address: Optional[str] = Query(None), lat: Optional[float] = Query(None), lng: Optional[float] = Query(None), radius_km: float = 5.0, limit: int = 50):
    search_lat, search_lng = lat, lng
    if address:
        coords = get_coordinates_from_address(address)
        if coords: search_lat, search_lng = coords
    
    if search_lat is None: raise HTTPException(400, "Need location")

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Query selects v.* so 'best_for' is definitely retrieved from DB
                query = """
                SELECT 
                    p.id, p.name, p.address, p.rating, p.price_level,
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
                
                results = []
                for row in rows:
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
                    
                    results.append({
                        **{k: row[k] for k in ["id", "name", "address", "rating", "price_level", "lat", "lng"]},
                        "distance_km": round(row['distance_km'], 2),
                        "vibes": vibes
                    })
                
                return results
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
