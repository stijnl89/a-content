@echo off
title Amazon A+ Tool - Dev Server

cd /d %~dp0

echo ========================================
echo Amazon A+ Tool - Starting...
echo ========================================
echo.

REM Gebruik python uit app\venv
if not exist app\venv\Scripts\python.exe (
    echo [ERROR] venv niet gevonden in app\venv
    pause
    exit /b 1
)

echo [INFO] Starting server...
echo [INFO] http://127.0.0.1:8000
echo.

app\venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir "%~dp0"

pause