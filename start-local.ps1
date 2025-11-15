# Local Development Setup
# Quick start script for local testing

Write-Host "🚀 Talk2Data - Local Development Setup" -ForegroundColor Green
Write-Host "=" * 50

# Check if OpenAI API key is set
if (-not $env:OPENAI_API_KEY) {
    Write-Host "⚠️  OPENAI_API_KEY not found in environment" -ForegroundColor Yellow
    $apiKey = Read-Host "Please enter your OpenAI API key"
    $env:OPENAI_API_KEY = $apiKey
}

# Check if required packages are installed
$requiredPackages = @("fastapi", "uvicorn", "streamlit", "requests")

Write-Host "📦 Checking required packages..." -ForegroundColor Cyan
foreach ($package in $requiredPackages) {
    try {
        $null = pip show $package 2>$null
        Write-Host "  ✅ $package" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ $package (installing...)" -ForegroundColor Yellow
        pip install $package --quiet
    }
}

Write-Host "`n🎯 Starting Talk2Data locally..." -ForegroundColor Cyan

Write-Host "1. API Service will start on: http://localhost:8000" -ForegroundColor White
Write-Host "2. In a new terminal, run: streamlit run streamlit_client_example.py" -ForegroundColor White
Write-Host "3. Streamlit will open: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the API service" -ForegroundColor Yellow
Write-Host ""

# Start the API service
python api_service.py