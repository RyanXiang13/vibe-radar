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

# --- UNIVERSITIES ---
Write-Host "🎓 Mining Universities..." -ForegroundColor Cyan

Write-Host "📍 Mining Harvard..."
python backend/scripts/miner.py "Study cafes near Harvard Square Cambridge" 20

Write-Host "📍 Mining MIT..."
python backend/scripts/miner.py "Laptop friendly cafes near MIT Cambridge" 20

Write-Host "📍 Mining Stanford..."
python backend/scripts/miner.py "Study spots near Stanford University Palo Alto" 20

Write-Host "📍 Mining UC Berkeley..."
python backend/scripts/miner.py "Cafes near UC Berkeley campus" 20

Write-Host "📍 Mining UCLA..."
python backend/scripts/miner.py "Study spots near UCLA Westwood" 20

Write-Host "📍 Mining Columbia..."
python backend/scripts/miner.py "Cafes near Columbia University NYC" 20

Write-Host "📍 Mining NYU..."
python backend/scripts/miner.py "Study cafes near NYU Washington Square Park" 20

Write-Host "📍 Mining UT Austin..."
python backend/scripts/miner.py "Coffee shops near UT Austin campus" 20

Write-Host "📍 Mining UW Seattle..."
python backend/scripts/miner.py "Study spots near University of Washington Seattle" 20

Write-Host "[!] University Mining Complete!" -ForegroundColor Green