@echo off
echo Running External TikToks - All 2025 Sound Campaigns...

REM Navigate to the script directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

REM Run the Python script
python run_external_tiktoks.py

REM Deactivate virtual environment if it was activated
if exist "venv\Scripts\activate.bat" (
    deactivate
)

echo.
echo External campaigns process finished.
pause

