# =======================================================
# Script khoi dong he thong Web Chat Local (Backend + Frontend)
# =======================================================
$Host.UI.RawUI.WindowTitle = "Web Chat - Khoi dong he thong Local"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   KHOI DONG FULLSTACK WEB CHAT (BACKEND + FRONTEND)   " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = $PSScriptRoot
$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"

# 1. Khoi dong Backend (FastAPI - Port 8000)
Write-Host "[1/3] Dang khoi dong Backend Server (Port 8000)..." -ForegroundColor Yellow
$backendCmd = "cd '$backendDir'; py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='Web Chat - Backend API (Port 8000)'; $backendCmd"

# 2. Khoi dong Frontend (Vite - Port 5173)
Write-Host "[2/3] Dang khoi dong Frontend Dev Server (Port 5173)..." -ForegroundColor Yellow
$frontendCmd = "cd '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='Web Chat - Frontend Vite (Port 5173)'; $frontendCmd"

# 3. Cho server khoi dong va tu dong mo trinh duyet
Write-Host "[3/3] Cho server san sang va mo trinh duyet..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Green
Write-Host " HE THONG DA KHOI DONG THANH CONG!" -ForegroundColor Green
Write-Host " - Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host " - Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host " - Swagger Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host " - Tai khoan:    admin / 123456" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "De dung he thong, vui long dong cac cua so terminal tren." -ForegroundColor Gray

