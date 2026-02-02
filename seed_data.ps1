Write-Host "🚀 Starting Vibe Radar Global Mining Operation..." -ForegroundColor Green

# --- TORONTO ---
Write-Host "📍 Mining Toronto: Kensington Market..." -ForegroundColor Cyan
docker-compose exec backend python scripts/miner.py "Cafes in Kensington Market, Toronto, ON" 20

# --- MONTREAL ---
Write-Host "📍 Mining Montreal: Mile End..." -ForegroundColor Magenta
docker-compose exec backend python scripts/miner.py "Cafes in Mile End, Montreal, QC" 20

Write-Host "📍 Mining Montreal: Concordia University..." -ForegroundColor Magenta
docker-compose exec backend python scripts/miner.py "Cafes near Concordia University, Montreal, QC" 20

# --- VANCOUVER ---
Write-Host "📍 Mining Vancouver: Kitsilano..." -ForegroundColor Yellow
docker-compose exec backend python scripts/miner.py "Cafes in Kitsilano, Vancouver, BC" 20

Write-Host "📍 Mining Vancouver: Gastown..." -ForegroundColor Yellow
docker-compose exec backend python scripts/miner.py "Cafes in Gastown, Vancouver, BC" 20

# --- UNIVERSITY TOWNS ---
Write-Host "📍 Mining Kingston: Queen's University..." -ForegroundColor White
docker-compose exec backend python scripts/miner.py "Cafes near Queen's University, Kingston, ON" 20

Write-Host "✅ MISSION COMPLETE! All cities mined." -ForegroundColor Green