@echo off
title Call Copilot
cd /d "%~dp0"
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" main.py
) else (
    python main.py
)
if %errorlevel% neq 0 (
    echo.
    echo ==============================
    echo   Call Copilot exited or crashed!
    echo   Check the error above.
    echo ==============================
    pause
)
