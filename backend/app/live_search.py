import json
import time
import requests
import queue
import threading
from dotenv import load_dotenv
import os

from utils import get_db_connection, get_vibe_from_ai # Will refactor these out

# Assuming we have these from main.py
MAPS_KEY = os.getenv("GMAPS_KEY")

def search_places_nearby(lat, lng, radius_m):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.priceLevel,places.reviews"
    }
    body = {
        "includedTypes": ["cafe", "coffee_shop"],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            return response.json().get('places', [])
    except Exception as e:
        print(f"Places API Error: {e}")
    return []
