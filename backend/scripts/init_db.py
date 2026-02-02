import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

print("🔨 Building Ultimate Student Database...")

# 1. Enable PostGIS
cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

# 2. Reset Tables (Clean Slate)
cursor.execute("DROP TABLE IF EXISTS place_vibes;")
cursor.execute("DROP TABLE IF EXISTS places;")

# 3. Create Places Table
cursor.execute("""
CREATE TABLE places (
    id SERIAL PRIMARY KEY,
    google_place_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    location GEOMETRY(Point, 4326),
    rating FLOAT,
    price_level INT
);
""")

# 4. Create Vibes Table
cursor.execute("""
CREATE TABLE place_vibes (
    id SERIAL PRIMARY KEY,
    place_id INT REFERENCES places(id) ON DELETE CASCADE,
    
    -- Basic Vibe
    vibe_tags TEXT[],
    summary TEXT,
    best_for TEXT[],        -- <--- NEW: ["Study", "Social", "Date", "Lunch"]
    
    -- Work Essentials
    noise_level TEXT,       
    wifi_quality TEXT,      
    outlets_level TEXT,     
    comfort_level TEXT,     
    
    -- Food & Layout
    food_type TEXT,         
    seating_tip TEXT,       
    busyness_info TEXT,     
    group_suitability TEXT, 

    -- Student Survival
    is_late_night BOOLEAN DEFAULT FALSE,
    time_limit_status TEXT, 
    bathroom_status TEXT,   
    has_natural_light BOOLEAN DEFAULT FALSE
);
""")

conn.commit()
cursor.close()
conn.close()
print("✅ Database Reborn with Student Superpowers!")