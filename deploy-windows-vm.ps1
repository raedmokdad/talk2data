# Talk2Data Agent - Windows VM Deployment Script
# PowerShell Script for automated deployment

param(
    [string]$VMPath = "C:\Apps\Talk2Data",
    [string]$OpenAIKey = "",
    [switch]$SkipDocker = $false
)

Write-Host "🚀 Talk2Data Agent - Windows VM Deployment" -ForegroundColor Green
Write-Host "=" * 50

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator!"
    exit 1
}

# Function to check if Docker is installed
function Test-DockerInstalled {
    try {
        $version = docker --version
        Write-Host "✅ Docker found: $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Docker not found" -ForegroundColor Red
        return $false
    }
}

# Function to install Docker (if needed)
function Install-DockerDesktop {
    Write-Host "📦 Installing Docker Desktop..." -ForegroundColor Yellow
    
    # Download Docker Desktop
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Host "Downloading Docker Desktop..."
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
    
    Write-Host "Starting Docker Desktop installation..."
    Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet" -Wait
    
    Write-Host "⚠️  Please restart your VM and run this script again!" -ForegroundColor Yellow
    exit 0
}

# Function to create project directory
function Initialize-ProjectDirectory {
    param([string]$Path)
    
    Write-Host "📁 Creating project directory: $Path" -ForegroundColor Cyan
    
    if (Test-Path $Path) {
        Write-Host "Directory already exists, backing up..."
        $backupPath = "$Path.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item $Path $backupPath
        Write-Host "Backup created: $backupPath"
    }
    
    New-Item -ItemType Directory -Path $Path -Force
    return $Path
}

# Function to copy project files
function Copy-ProjectFiles {
    param([string]$SourcePath, [string]$DestPath)
    
    Write-Host "📋 Copying project files..." -ForegroundColor Cyan
    
    $filesToCopy = @(
        "src\*",
        "prompts\*", 
        "requirements.txt",
        "api_service.py",
        "Dockerfile.windows",
        "docker-compose.windows.yml",
        ".env.example"
    )
    
    foreach ($filePattern in $filesToCopy) {
        $sourcePath = Join-Path $SourcePath $filePattern
        if (Test-Path $sourcePath) {
            $destDir = Split-Path (Join-Path $DestPath $filePattern) -Parent
            if (!(Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force
            }
            Copy-Item $sourcePath $destDir -Recurse -Force
            Write-Host "  ✅ Copied: $filePattern"
        } else {
            Write-Host "  ⚠️  Not found: $filePattern" -ForegroundColor Yellow
        }
    }
}

# Function to setup environment variables
function Setup-Environment {
    param([string]$ProjectPath, [string]$ApiKey)
    
    Write-Host "🔑 Setting up environment variables..." -ForegroundColor Cyan
    
    $envFile = Join-Path $ProjectPath ".env"
    
    if ($ApiKey) {
        "OPENAI_API_KEY=$ApiKey" | Out-File $envFile -Encoding UTF8
        Write-Host "✅ OpenAI API key configured"
    } else {
        Write-Host "⚠️  OpenAI API key not provided. Please add it manually to .env file" -ForegroundColor Yellow
        "OPENAI_API_KEY=your-openai-api-key-here" | Out-File $envFile -Encoding UTF8
    }
}

# Function to build and start Docker containers
function Start-DockerContainers {
    param([string]$ProjectPath)
    
    Write-Host "🐳 Building and starting Docker containers..." -ForegroundColor Cyan
    
    Set-Location $ProjectPath
    
    # Build the container
    Write-Host "Building Docker image..."
    docker-compose -f docker-compose.windows.yml build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker image built successfully"
    } else {
        Write-Host "❌ Docker build failed" -ForegroundColor Red
        return $false
    }
    
    # Start containers
    Write-Host "Starting containers..."
    docker-compose -f docker-compose.windows.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Containers started successfully"
        return $true
    } else {
        Write-Host "❌ Failed to start containers" -ForegroundColor Red
        return $false
    }
}

# Function to configure Windows Firewall
function Configure-Firewall {
    Write-Host "🔥 Configuring Windows Firewall..." -ForegroundColor Cyan
    
    try {
        # Allow port 8000 for Talk2Data API
        New-NetFirewallRule -DisplayName "Talk2Data API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -ErrorAction SilentlyContinue
        Write-Host "✅ Firewall rule added for port 8000"
    }
    catch {
        Write-Host "⚠️  Could not configure firewall. Please manually allow port 8000" -ForegroundColor Yellow
    }
}

# Function to test the deployment
function Test-Deployment {
    Write-Host "🧪 Testing deployment..." -ForegroundColor Cyan
    
    Start-Sleep -Seconds 10  # Wait for services to start
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
        if ($response.status -eq "healthy") {
            Write-Host "✅ Deployment test PASSED!" -ForegroundColor Green
            Write-Host "API is running at: http://localhost:8000"
            Write-Host "API Documentation: http://localhost:8000/docs"
            return $true
        }
    }
    catch {
        Write-Host "❌ Deployment test FAILED!" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)"
        return $false
    }
}

# Function to show final instructions
function Show-FinalInstructions {
    Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "=" * 50
    Write-Host "Talk2Data Agent is now running on your Windows VM!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📍 API Endpoints:"
    Write-Host "  • Health Check: http://localhost:8000/health"
    Write-Host "  • Generate SQL: http://localhost:8000/generate-sql"
    Write-Host "  • API Docs: http://localhost:8000/docs"
    Write-Host ""
    Write-Host "🔧 Management Commands:"
    Write-Host "  • View logs: docker-compose -f docker-compose.windows.yml logs -f"
    Write-Host "  • Stop service: docker-compose -f docker-compose.windows.yml down"
    Write-Host "  • Restart: docker-compose -f docker-compose.windows.yml restart"
    Write-Host ""
    Write-Host "🌐 External Access:"
    Write-Host "  Replace 'localhost' with your VM's IP address for external access"
    Write-Host "  Example: http://your-vm-ip:8000/health"
    Write-Host ""
}

# MAIN DEPLOYMENT FLOW
try {
    # Step 1: Check Docker
    if (-not $SkipDocker) {
        if (-not (Test-DockerInstalled)) {
            Install-DockerDesktop
        }
    }
    
    # Step 2: Initialize project directory
    $projectPath = Initialize-ProjectDirectory -Path $VMPath
    
    # Step 3: Copy files
    $currentPath = Get-Location
    Copy-ProjectFiles -SourcePath $currentPath -DestPath $projectPath
    
    # Step 4: Setup environment
    Setup-Environment -ProjectPath $projectPath -ApiKey $OpenAIKey
    
    # Step 5: Configure firewall
    Configure-Firewall
    
    # Step 6: Start containers
    if (-not $SkipDocker) {
        $deploySuccess = Start-DockerContainers -ProjectPath $projectPath
        
        if ($deploySuccess) {
            # Step 7: Test deployment
            if (Test-Deployment) {
                Show-FinalInstructions
            }
        }
    } else {
        Write-Host "✅ Project files prepared. Run Docker manually with:" -ForegroundColor Green
        Write-Host "cd $projectPath"
        Write-Host "docker-compose -f docker-compose.windows.yml up -d"
    }
    
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n🚀 Windows VM deployment completed!" -ForegroundColor Green