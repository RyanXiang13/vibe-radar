import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    print("🚀 Adding 'city_requests' table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_requests (
            id SERIAL PRIMARY KEY,
            city TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    conn.commit()
    print("✅ Table created successfully.")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if cursor: cursor.close()
    if conn: conn.close()
