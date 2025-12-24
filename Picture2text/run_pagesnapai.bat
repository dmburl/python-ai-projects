@echo off
REM PageSnapAI - Windows launcher
REM Double-click this file to run the PageSnapAI app
REM
REM This script:
REM 1. Checks if Python is installed
REM 2. Verifies google-generativeai is installed
REM 3. Launches the GUI app

setlocal enabledelayedexpansion

echo.
echo ========================================
echo PageSnapAI - Windows Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Solution:
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. During installation, CHECK the box "Add Python to PATH"
    echo 3. Restart your computer
    echo 4. Try this launcher again
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Python found:
python --version
echo.

REM Install dependencies
echo Installing/updating required packages...
echo.

python -m pip install --upgrade pip
python -m pip install google-generativeai python-docx

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install required packages.
    echo.
    echo Solution:
    echo 1. Open Command Prompt (Windows key + R, type 'cmd', press Enter)
    echo 2. Run this command:
    echo    pip install google-generativeai python-docx
    echo 3. After installation, try this launcher again
    echo.
    pause
    exit /b 1
)
echo Required packages ready!
echo.

REM Everything is ready - launch the app
echo Launching PageSnapAI...
echo.

python pagesnapai.py

REM If the app exits with an error, keep the window open so user can see the error
if errorlevel 1 (
    echo.
    echo ERROR: The app encountered an error (exit code: %errorlevel%)
    echo.
    pause
    exit /b %errorlevel%
)

exit /b 0
