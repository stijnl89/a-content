@echo off
title Amazon A+ Tool - Dev Server

cd /d %~dp0

echo ========================================
echo Amazon A+ Tool - Starting...
echo ========================================
echo.

if not exist venv\Scripts\python.exe (
    echo [ERROR] venv\Scripts\python.exe niet gevonden.
    pause
    exit /b 1
)

echo [INFO] Using Python:
venv\Scripts\python.exe -c "import sys; print(sys.executable)"
echo.

echo [INFO] Starting server on http://127.0.0.1:8000
echo.

venv\Scripts\python.exe -m uvicorn main:app --reload --app-dir "%~dp0"

pause