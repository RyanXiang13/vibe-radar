Write-Host "🚀 Starting Vibe Radar US Tech Hub Mining..." -ForegroundColor Green

# --- SAN FRANCISCO ---
Write-Host "📍 Mining SF: SoMa..." -ForegroundColor Cyan
python backend/scripts/miner.py "Laptop friendly cafes SoMa San Francisco" 20

Write-Host "📍 Mining SF: Mission District..." -ForegroundColor Cyan
python backend/scripts/miner.py "Study spots Mission District San Francisco" 20

# --- NEW YORK CITY ---
Write-Host "📍 Mining NYC: Williamsburg..." -ForegroundColor Magenta
python backend/scripts/miner.py "Cafes with wifi Williamsburg Brooklyn" 20

Write-Host "📍 Mining NYC: West Village..." -ForegroundColor Magenta
python backend/scripts/miner.py "Study cafes West Village NYC" 20

Write-Host "📍 Mining NYC: Lower East Side..." -ForegroundColor Magenta
python backend/scripts/miner.py "Coffee shops Lower East Side NYC" 20

Write-Host "📍 Mining NYC: Bushwick..." -ForegroundColor Magenta
python backend/scripts/miner.py "Laptop friendly cafes Bushwick" 15

# --- SEATTLE ---
Write-Host "📍 Mining Seattle: Capitol Hill..." -ForegroundColor Yellow
python backend/scripts/miner.py "Best study cafes Capitol Hill Seattle" 20

# --- AUSTIN ---
Write-Host "📍 Mining Austin: South Congress..." -ForegroundColor White
python backend/scripts/miner.py "Coffee shops South Congress Austin" 20

Write-Host "✅ MISSION COMPLETE! US Tech Hubs Mined." -ForegroundColor Green