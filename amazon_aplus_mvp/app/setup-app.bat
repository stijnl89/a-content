@echo off
title Amazon A+ Tool - Setup

cd /d %~dp0

echo ========================================
echo Amazon A+ Tool - Setup
echo ========================================
echo.

if not exist venv (
    echo [INFO] Creating virtual environment...
    py -m venv venv
)

echo [INFO] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo [INFO] Installing dependencies...
venv\Scripts\python.exe -m pip install fastapi uvicorn jinja2 playwright

echo [INFO] Installing Playwright browsers...
venv\Scripts\python.exe -m playwright install

echo.
echo [SUCCESS] Setup klaar.
pause