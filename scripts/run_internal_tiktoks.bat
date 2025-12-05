@echo off
echo Running the Internal TikToks Daily Report...

REM Navigate to the script directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

REM Run the Python script
python run_internal_tiktoks.py

REM Deactivate virtual environment if it was activated
if exist "venv\Scripts\activate.bat" (
    deactivate
)

echo.
echo Daily report process finished.
pause

