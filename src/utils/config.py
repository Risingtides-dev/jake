#!/usr/bin/env python3
"""
Configuration file for Warner Tracker
Centralizes all configurable values including account lists, dates, paths, and exclusive songs.

TODO: Replace placeholder accounts with your actual TikTok accounts
TODO: Update date filters to match your analysis timeframe
TODO: Update output paths to your desired locations
"""

import os
from datetime import datetime
from pathlib import Path

# Get project root directory (directory containing this config file)
PROJECT_ROOT = Path(__file__).parent.absolute()

# ============================================================================
# ACCOUNT CONFIGURATION
# ============================================================================

# List of TikTok accounts to analyze
# Format: List of strings with '@' prefix (e.g., '@username')
# Extracted from CSV files on 2025-11-10 (removed email addresses)
ACCOUNTS = [
    '@beaujenkins',
    '@codyjames6.7',
    '@coffeesentiments',
    '@gavin.wilder1',
    '@smoked.999',
]

# Target accounts for exclusive song analysis
# Songs used ONLY by these accounts will be filtered out
# All Warner TikTok accounts are target accounts
TARGET_ACCOUNTS = {
    '@beaujenkins',
    '@codyjames6.7',
    '@coffeesentiments',
    '@gavin.wilder1',
    '@smoked.999',
}

# Account mapping for aggregate_sound_analysis.py
# Maps bash process IDs to account names (if using background processes)
# TODO: Replace with your account mappings or remove if not needed
ACCOUNTS_DICT = {
    # 'process_id_1': '@example_account_1',
    # 'process_id_2': '@example_account_2',
}

# ============================================================================
# DATE FILTERS
# ============================================================================

# Cutoff date for video analysis (videos before this date will be excluded)
# Format: datetime(year, month, day)
CUTOFF_DATE = datetime(2025, 10, 1)  # TODO: Update to your desired cutoff date

# Date filter for exclusive songs analysis
# Only analyze videos from this month/year
EXCLUSIVE_SONGS_YEAR = 2025  # TODO: Update if needed
EXCLUSIVE_SONGS_MONTH = 11   # TODO: Update if needed

# ============================================================================
# EXCLUSIVE SONGS
# ============================================================================

# Songs that are ONLY used by target accounts
# These will be filtered out from shared song analysis
# Format: Set of strings in format "Song Title - Artist Name"
# TODO: Populate with your exclusive songs list or leave empty
EXCLUSIVE_SONGS = {
    # 'Song Title - Artist Name',
    # 'Another Song - Another Artist',
}

# ============================================================================
# FILTERED ARTISTS/SONGS
# ============================================================================

# Artists to exclude from reports
FILTERED_ARTISTS = {
    'Mon Rovîa',
    'GoldFord',
    'Gregory Alan Isakov',
}

# Specific songs to exclude (format: "Song Title - Artist Name" or just "Song Title")
FILTERED_SONGS = {
    'original sound - beau jenkins 🛠️',
    'original sound - beau jenkins',
    'original sound - Cody James',
    'Ostentatious - Montell Fish, dj gummy bear, John Glacier',
    'Ostentatious',
}

# Whitelist of songs to include (if set, only these songs will be shown)
# Leave empty to show all songs (except filtered ones)
# Format: Set of tuples (song_title, artist_name) or None
SONG_WHITELIST = None  # Set to None to disable whitelist, or provide a set of (song, artist) tuples

# ============================================================================
# PATHS AND DIRECTORIES
# ============================================================================

# Project directories
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
CONFIG_DIR = PROJECT_ROOT / 'config'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Output file paths
EXCEL_OUTPUT_FILE = OUTPUT_DIR / 'shared_songs_tiktok_links.xlsx'
HTML_OUTPUT_FILE = OUTPUT_DIR / 'sound_usage_complete_report.html'
NETWORK_TRACKER_OUTPUT_FILE = OUTPUT_DIR / 'inhouse_network_tracker.html'

# Data file paths
CSV_DATA_DIR = DATA_DIR / 'Private & Shared 4'  # TODO: Update if CSV files are moved

# Path to CSV file containing the official song list
SONG_TRACKER_CSV = CSV_DATA_DIR / 'WARNER Sound Use Tracker - October 28d1465bb82981929dabde2da2622466_all.csv'

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

# Default limit for video scraping
DEFAULT_VIDEO_LIMIT = 100

# yt-dlp command (can be 'yt-dlp' or full path)
YT_DLP_CMD = 'yt-dlp'

# Python command (can be 'python', 'python3', or full path)
PYTHON_CMD = 'python3'

# ============================================================================
# ANALYSIS CONFIGURATION
# ============================================================================

# Number of top videos to show in reports
TOP_VIDEOS_COUNT = 3

# Engagement rate calculation
# Formula: ((likes + comments + shares) / views) * 100
ENGAGEMENT_RATE_FORMULA = lambda likes, comments, shares, views: (
    ((likes + comments + shares) / views) * 100 if views > 0 else 0
)

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration and warn about missing values"""
    warnings = []
    
    if not ACCOUNTS:
        warnings.append("WARNING: ACCOUNTS list is empty. Add accounts to analyze.")
    
    if not TARGET_ACCOUNTS:
        warnings.append("WARNING: TARGET_ACCOUNTS is empty. Exclusive song filtering may not work as expected.")
    
    if CUTOFF_DATE > datetime.now():
        warnings.append("WARNING: CUTOFF_DATE is in the future. This may exclude all videos.")
    
    for warning in warnings:
        print(warning)
    
    return len(warnings) == 0

if __name__ == '__main__':
    # Test configuration
    print("Warner Tracker Configuration")
    print("=" * 50)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Accounts: {len(ACCOUNTS)} accounts configured")
    print(f"Target Accounts: {len(TARGET_ACCOUNTS)} accounts configured")
    print(f"Exclusive Songs: {len(EXCLUSIVE_SONGS)} songs configured")
    print(f"Cutoff Date: {CUTOFF_DATE.strftime('%Y-%m-%d')}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()
    validate_config()

