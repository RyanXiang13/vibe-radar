# Vibe Radar 📡☕
**Your personal scout for the perfect study spot.**

![Vibe Radar Preview](frontend/public/logo_icon.png)

## The Problem
I built **Vibe Radar** during finals week because I was tired of the "coffee shop roulette."
You walk into a cafe with your laptop, ready to work, only to find:
1.  No outlets.
2.  Spotty Wifi.
3.  It's deafeningly loud.

Google Maps tells you *where* a place is. Vibe Radar tells you **what it feels like**.

## How It Works (The "Sherlock" Engine) 🕵️‍♂️
Unlike standard directories, Vibe Radar uses an **AI-powered Mining Engine** to "read" thousands of reviews so you don't have to.

### 1. Data Mining & Aggregation
The backend aggressively scrapes Google Places data for high-density student areas (Waterloo, Toronto, etc.).

### 2. The "Sherlock" Inference Model
Most data sources just give you "Amenities: Wifi". Vibe Radar goes deeper using a custom LLM pipeline (Gemini 2.0 Flash) with **Aggressive Inference**:
-   *Review says:* "I saw a lot of students with laptops."
    -   *Vibe Radar infers:* **Outlets: Many**, **Wifi: Fast**.
-   *Review says:* "Great place to focus on my essay."
    -   *Vibe Radar infers:* **Noise: Quiet/Moderate**.
-   *Review says:* "Latte was $7."
    -   *Vibe Radar infers:* **Price: Pricey**.

### 3. Spatial Indexing
Data is stored in **PostgreSQL + PostGIS**. We use **GiST Spatial Indexing** to perform lightning-fast radius searches, instantly ranking thousands of spots based on your specific needs (e.g., "Late Night" + "Group Friendly").

---

## Tech Stack
-   **Frontend**: React, Tailwind CSS (Custom "Rainbow" UI), Mapbox GL
-   **Backend**: Python, FastAPI
-   **Database**: PostgreSQL, PostGIS (Supabase)
-   **AI**: Google Gemini 2.0 Flash (JSON Mode)
-   **Infrastructure**: Docker, Vercel

## Key Features
-   **Vibe Scoring**: 0-10 scores for Quiet, Power, Wifi, Food, Price.
-   **"Sherlock" Analysis**: No more "Unknown" data fields. The AI guesses based on context.
-   **Live Filters**: Filter by intent ("Date Spot" vs "Study Grind").
-   **Performance**: Sub-100ms spatial queries via PostGIS indexing.

---
*Built to survive engineering finals.*
