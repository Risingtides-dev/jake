@echo off
REM ===================================================================
REM Robust Campaign Scraper - Easy Manual Run Script
REM No coding experience needed!
REM ===================================================================

echo.
echo ========================================
echo  Robust Campaign Scraper
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Prompt for campaign CSV file
echo Enter the campaign CSV filename (e.g., raise_campaign.csv):
set /p CSV_FILE="> "

if not exist "%CSV_FILE%" (
    echo ERROR: File not found: %CSV_FILE%
    echo Please make sure the CSV file exists in this directory
    pause
    exit /b 1
)

echo [OK] Campaign file found: %CSV_FILE%
echo.

REM Prompt for start date
echo Enter start date to scrape from (format: YYYY-MM-DD):
echo (Press Enter to scrape ALL videos)
set /p START_DATE="> "

REM Prompt for platform
echo.
echo Choose platform:
echo   1 = TikTok only
echo   2 = Instagram only
echo   3 = Both TikTok and Instagram
set /p PLATFORM_CHOICE="> "

if "%PLATFORM_CHOICE%"=="1" set PLATFORM=tiktok
if "%PLATFORM_CHOICE%"=="2" set PLATFORM=instagram
if "%PLATFORM_CHOICE%"=="3" set PLATFORM=both

if "%PLATFORM%"=="" (
    echo Invalid choice, defaulting to TikTok
    set PLATFORM=tiktok
)

echo [OK] Platform: %PLATFORM%
echo.

REM Prompt for video limit
echo How many videos per account to scrape? (default: 500)
echo (Higher numbers = more videos but takes longer)
set /p LIMIT="> "

if "%LIMIT%"=="" set LIMIT=500

echo [OK] Limit: %LIMIT% videos per account
echo.

REM Build command
set CMD=python robust_campaign_scraper.py "%CSV_FILE%" --platform %PLATFORM% --limit %LIMIT%

if not "%START_DATE%"=="" (
    set CMD=%CMD% --start-date %START_DATE%
)

REM Show what we're about to do
echo.
echo ========================================
echo  Ready to start!
echo ========================================
echo.
echo Campaign: %CSV_FILE%
echo Platform: %PLATFORM%
echo Start date: %START_DATE%
echo Limit: %LIMIT% videos/account
echo.
echo This will:
echo  1. Scrape videos from all accounts in the CSV
echo  2. Extract sound IDs in parallel (fast!)
echo  3. Match videos to your campaign sounds
echo  4. Save results to output/ folder
echo.
echo Press any key to start, or Ctrl+C to cancel...
pause >nul

echo.
echo ========================================
echo  Starting scraper...
echo ========================================
echo.

REM Run the scraper
%CMD%

echo.
echo ========================================
echo  Done!
echo ========================================
echo.
echo Check the output/ folder for results
echo.
pause
