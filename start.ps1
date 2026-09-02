Write-Host "========================================================" -ForegroundColor Yellow
Write-Host "Starting Resume Roast (Backend :8000 + Frontend :5173)..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Yellow

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; python run.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev"

Write-Host "`nBoth servers are launching!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Yellow
