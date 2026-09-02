@echo off
echo ========================================================
echo Starting Resume Roast (Backend :8000 + Frontend :5173)...
echo ========================================================

start "Resume Roast Backend" cmd /k "cd /d %~dp0backend && python run.py"
start "Resume Roast Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are launching!
echo Frontend will be live at: http://localhost:5173
echo Backend will be live at:  http://localhost:8000
echo ========================================================
