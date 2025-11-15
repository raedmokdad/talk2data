#!/usr/bin/env powershell
# Talk2Data API Starter - Mit Ihrem OpenAI Key

Write-Host "🚀 Talk2Data API Service Starter" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor White
Write-Host ""

# Check Virtual Environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✅ Virtual Environment gefunden" -ForegroundColor Green
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Virtual Environment nicht gefunden!" -ForegroundColor Red
    Write-Host "Führen Sie aus: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Check .env file
if (Test-Path ".env") {
    Write-Host "✅ .env Datei mit OpenAI Key gefunden" -ForegroundColor Green
} else {
    Write-Host "❌ .env Datei nicht gefunden!" -ForegroundColor Red
    Write-Host "Erstellen Sie eine .env Datei mit: OPENAI_API_KEY=sk-your-key" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🎯 Starte Talk2Data API Service..." -ForegroundColor Yellow
Write-Host "📍 URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Drücken Sie Ctrl+C zum Beenden" -ForegroundColor Gray
Write-Host ""

# Start API Service
python api_service.py