#!/usr/bin/env pwsh
<#
.SYNOPSIS
    One-shot deployment script for Pre-Authorization Desk (Windows PowerShell)
.DESCRIPTION
    Starts all Docker services, builds corpus index, seeds demo data,
    and opens the UI. Run once after git clone.
#>

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Health Insurance Pre-Authorization Desk - Deploy Script  " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found. Install Docker Desktop from https://docker.com" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Docker found" -ForegroundColor Green

# Check docker compose (v2 plugin or standalone)
$composeCmd = $null
if (docker compose version 2>$null) {
    $composeCmd = "docker compose"
} elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $composeCmd = "docker-compose"
} else {
    Write-Host "ERROR: docker compose not available. Update Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "OK: docker compose available" -ForegroundColor Green

# Check Docker daemon / engine
Write-Host "Checking Docker engine daemon..." -ForegroundColor DarkGray
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker daemon is not running yet. Attempting to start Docker Desktop..." -ForegroundColor Yellow
    $dockerDesktopExe = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe",
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($dockerDesktopExe) {
        Start-Process -FilePath $dockerDesktopExe
        Write-Host "Launched: $dockerDesktopExe" -ForegroundColor Cyan
    }

    Write-Host "Waiting for Docker daemon to respond (up to 45s)..." -ForegroundColor Yellow
    $daemonReady = $false
    for ($wait = 1; $wait -le 15; $wait++) {
        Start-Sleep -Seconds 3
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $daemonReady = $true
            break
        }
        Write-Host "  Waiting for Docker daemon... ($wait/15)" -ForegroundColor DarkGray
    }

    if (-not $daemonReady) {
        Write-Host ""
        Write-Host "ERROR: Docker engine is not running." -ForegroundColor Red
        Write-Host "Please start Docker Desktop manually:" -ForegroundColor Yellow
        Write-Host "  1. Open the Windows Start Menu" -ForegroundColor White
        Write-Host "  2. Search for and launch 'Docker Desktop'" -ForegroundColor White
        Write-Host "  3. Wait until the whale icon in the taskbar says 'Engine running'" -ForegroundColor White
        Write-Host "  4. Re-run: .\deploy.ps1" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
}
Write-Host "OK: Docker engine daemon is running" -ForegroundColor Green

# 2. Check .env file
Write-Host ""
Write-Host "[2/6] Checking environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Copying .env.example to .env" -ForegroundColor DarkGray
    Copy-Item ".env.example" ".env"
    Write-Host "OK: .env created (stub LLM - zero API cost)" -ForegroundColor Green
} else {
    Write-Host "OK: .env already exists" -ForegroundColor Green
}

# 3. Start core services
Write-Host ""
Write-Host "[3/6] Starting Docker services..." -ForegroundColor Yellow
Invoke-Expression "$composeCmd up -d --build redis postgres backend agent-worker jaeger prometheus grafana flower frontend"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose failed. Check Docker Desktop is running." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Services started" -ForegroundColor Green

# 4. Wait for backend health
Write-Host ""
Write-Host "[4/6] Waiting for backend to be healthy (up to 45s)..." -ForegroundColor Yellow
$healthy = $false
for ($i = 1; $i -le 15; $i++) {
    Start-Sleep -Seconds 3
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        # still starting
    }
    Write-Host "  Waiting... ($i/15)" -ForegroundColor DarkGray
}

if ($healthy) {
    Write-Host "OK: Backend is healthy" -ForegroundColor Green
} else {
    Write-Host "WARNING: Backend may still be starting. Continuing anyway..." -ForegroundColor Yellow
    Write-Host "         Check logs with: docker compose logs backend" -ForegroundColor DarkGray
}

# 5. Build corpus index
Write-Host ""
Write-Host "[5/6] Building FAISS corpus index (this takes ~30 seconds)..." -ForegroundColor Yellow
Invoke-Expression "$composeCmd run --rm corpus-ingest"
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Corpus index built" -ForegroundColor Green
} else {
    Write-Host "WARNING: Corpus ingest may have failed. The backend has an in-memory fallback." -ForegroundColor Yellow
}

# 6. Seed demo data
Write-Host ""
Write-Host "[6/6] Seeding Hyderabad and Bangalore hospital demo data..." -ForegroundColor Yellow
$seedResult = Invoke-Expression "$composeCmd exec -T backend python scripts/seed_demo_data.py" 2>&1
if ($LASTEXITCODE -ne 0) {
    # Try with explicit PYTHONPATH
    $seedResult = Invoke-Expression "$composeCmd exec -T -e PYTHONPATH=/app backend python /app/scripts/seed_demo_data.py" 2>&1
}
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: Demo data seeded (20 hospital records)" -ForegroundColor Green
} else {
    Write-Host "WARNING: Seed script failed. Run manually:" -ForegroundColor Yellow
    Write-Host "         cd backend && python ../scripts/seed_demo_data.py" -ForegroundColor DarkGray
}

# Done
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   Pre-Authorization Desk is LIVE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend UI     ->  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Live Records    ->  http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host "  Cataract Demo   ->  http://localhost:3000/demo" -ForegroundColor Cyan
Write-Host "  API Swagger     ->  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Grafana         ->  http://localhost:3001  (admin / admin123)" -ForegroundColor Cyan
Write-Host "  Jaeger Traces   ->  http://localhost:16686" -ForegroundColor Cyan
Write-Host "  Flower Workers  ->  http://localhost:5555" -ForegroundColor Cyan
Write-Host ""
Write-Host "Section 4.1 Test -> open http://localhost:3000/demo" -ForegroundColor White
Write-Host ""
