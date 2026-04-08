@echo off
title Amazon A+ Tool - Setup

cd /d %~dp0

echo ========================================
echo Amazon A+ Tool - Setup
echo ========================================
echo.

REM Maak venv in app\ als die nog niet bestaat
if not exist app\venv (
    echo [INFO] Creating virtual environment in app\venv...
    py -m venv app\venv
)

REM Upgrade pip
echo [INFO] Upgrading pip...
app\venv\Scripts\python.exe -m pip install --upgrade pip

REM Installeer dependencies
if exist requirements.txt (
    echo [INFO] Installing requirements.txt...
    app\venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [INFO] No requirements.txt found, installing core packages...
    app\venv\Scripts\python.exe -m pip install fastapi uvicorn jinja2 playwright python-multipart
)

REM Installeer Playwright browsers
echo [INFO] Installing Playwright browsers...
app\venv\Scripts\python.exe -m playwright install

echo.
echo [SUCCESS] Setup klaar.
pause