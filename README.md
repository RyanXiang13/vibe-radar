# Vibe Radar 📡☕
**Live Demo:** [viberadar.ryanxiang.dev](https://viberadar.ryanxiang.dev)

![Vibe Radar Logo](frontend/public/logo_icon.png)

## Why I Built This
Honestly, this project started because I was stressing out during finals week. I desperately needed to lock in and study, but I couldn't focus at home, and campus libraries were absolutely packed. I wasted so much time just wandering around looking for a cafe that had:
1.  Good wifi (non-negotiable)
2.  An actual power outlet
3.  A vibe that wasn't dead silent but also not a frat party

I ended up building **Vibe Radar** to solve that problem. It's not just a map query; it uses AI to actually "read" the vibe of a place based on reviews and data so you know exactly what you're walking into. It helped me find the perfect spots to grind out my studying, and I eventually aced those finals. Hopefully, it helps you find your spot too.

---

## Capabilities
-   **Vibe Scoring**: Uses LLMs to analyze reviews and tag places (Quiet, Study-Friendly, Date Spot, etc.).
-   **Smart Search**: Filter by specific needs like "Late Night," "Group Seating," or "Fast Wifi."
-   **Dark Mode**: For those late-night coding sessions.
-   **Live Map**: Auto-detects your location to find the best spots nearby instantly.

---

## Tech Stack
### Frontend
-   **Framework**: React (Vite)
-   **Styling**: Tailwind CSS (Custom "Rainbow Wave" aesthetics)
-   **Maps**: Mapbox GL JS & Google Maps API
-   **Icons**: Lucide React

### Backend
-   **API**: FastAPI (Python)
-   **Database**: PostgreSQL (Supabase) + PostGIS for geospatial queries
-   **AI**: OpenAI API (for vibe extraction)

---

## Getting Started

If you want to run this locally, here is everything you need.

### Prerequisites
-   Node.js & npm
-   Python 3.10+
-   Docker (Optional, but recommended)
-   API Keys (Mapbox, Google Maps, OpenAI)

### 1. Environment Setup
Create a `.env` file in the root directory:
```bash
# Frontend Keys
VITE_MAPBOX_TOKEN=your_pk_token
VITE_GMAPS_KEY=your_google_maps_key

# Backend Keys
DATABASE_URL=postgresql://user:pass@host:5432/postgres
OPENAI_API_KEY=sk-...
GMAPS_KEY=your_google_maps_back_key
```

### 2. Quick Start (Docker)
The easiest way to spin everything up is with Docker Compose:
```bash
docker-compose up --build
```
This will launch:
-   Frontend: `http://localhost:5173`
-   Backend API: `http://localhost:8000`

### 3. Manual Setup (Dev Mode)

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Contributing
If you have ideas to make the vibe checks better or want to add features (like "coffee quality" vs "productivity"), feel free to open a PR!

---
*Built with caffeine and stress.*
