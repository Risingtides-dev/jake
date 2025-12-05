# TikTok Tracker Scripts - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Required Dependencies](#required-dependencies)
4. [Installation Guide](#installation-guide)
5. [Script Details](#script-details)
6. [Data Flow](#data-flow)
7. [Configuration](#configuration)

---

## Overview

This project contains a suite of Python scripts designed to scrape, analyze, and generate reports on TikTok content across multiple accounts. The primary focus is tracking sound/song usage, engagement metrics, and network performance analysis.

**Main Capabilities:**
- Scrape video metadata from TikTok profiles using yt-dlp
- Analyze engagement metrics (views, likes, comments, shares, engagement rate)
- Track sound/song usage across multiple accounts
- Identify exclusive vs shared songs
- Generate HTML reports with modern UI (cyberpunk and glassmorphism themes)
- Export data to Excel spreadsheets
- Compare account performance

---

## System Requirements

### Operating System
- **macOS** (Primary - paths are hardcoded for macOS)
- Linux (should work with minor path adjustments)
- Windows (requires path modifications and WSL recommended)

### Python Version
- **Python 3.7 or higher** required
- Tested on Python 3.8+

### Disk Space
- Minimum 100MB free space for reports and cached data

### Internet Connection
- Required for scraping TikTok profiles via yt-dlp

---

## Required Dependencies

### 1. External Command-Line Tools

#### **yt-dlp** (CRITICAL)
- **Purpose:** Downloads and extracts metadata from TikTok videos
- **Used by:** All scraping scripts
- **Installation:**
  ```bash
  # macOS (via Homebrew)
  brew install yt-dlp

  # macOS/Linux (via pip)
  pip install yt-dlp

  # macOS/Linux (via curl)
  sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
  sudo chmod a+rx /usr/local/bin/yt-dlp
  ```
- **Verify installation:**
  ```bash
  yt-dlp --version
  ```

#### **Claude CLI** (OPTIONAL)
- **Purpose:** Used only in `aggregate_sound_analysis.py` for bash output retrieval
- **Used by:** `aggregate_sound_analysis.py` (line 25-26)
- **Note:** Can be removed if not using background bash processes
- **Installation:** https://claude.com/claude-code

### 2. Python Packages

#### **Standard Library** (Pre-installed with Python)
These are built into Python and require no installation:
- `sys` - System-specific parameters and functions
- `os` - Operating system interfaces
- `subprocess` - Subprocess management for running external commands
- `json` - JSON encoding and decoding
- `re` - Regular expression operations
- `collections` - Container datatypes (defaultdict)
- `datetime` - Date and time manipulation
- `argparse` - Command-line argument parsing

#### **Third-Party Packages** (Require installation)

##### **openpyxl**
- **Purpose:** Create and modify Excel (.xlsx) files
- **Used by:** `generate_song_excel.py`
- **Installation:**
  ```bash
  pip install openpyxl
  ```
- **Version:** 3.0.0 or higher recommended

---

## Installation Guide

### Step 1: Install System Dependencies

```bash
# macOS - Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install yt-dlp
brew install yt-dlp

# Verify installation
yt-dlp --version
```

### Step 2: Set Up Python Environment

```bash
# Navigate to project directory
cd /Users/risingtidesdev/Desktop/clipper_project_fixed/tracker_data

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Install openpyxl
pip install openpyxl

# Verify installation
python3 -c "import openpyxl; print('openpyxl version:', openpyxl.__version__)"
```

### Step 4: Verify All Dependencies

```bash
# Check Python version
python3 --version  # Should be 3.7+

# Check yt-dlp
yt-dlp --version

# Check openpyxl
python3 -c "import openpyxl; print('OK')"

# Test yt-dlp TikTok scraping
yt-dlp --flat-playlist --dump-json --playlist-end 1 "https://www.tiktok.com/@radio_kart" | head -1
```

---

## Script Details

### 1. tiktok_analyzer.py

**Purpose:** Core analyzer that extracts detailed engagement metrics and song information from TikTok profiles.

**Process:**
1. Accepts TikTok username or profile URL via command-line arguments
2. Uses yt-dlp to scrape video metadata in JSON format
3. Parses JSON to extract:
   - Video URLs
   - Engagement metrics (views, likes, comments, shares)
   - Upload dates
   - Song/music information (title, artist, album)
4. Calculates engagement rate: `((likes + comments + shares) / views) * 100`
5. Outputs formatted analysis to stdout

**Dependencies:**
- Python: `sys`, `argparse`, `subprocess`, `json`, `re`, `datetime`
- External: `yt-dlp`

**Usage:**
```bash
python3 tiktok_analyzer.py --url @radio_kart --limit 10
python3 tiktok_analyzer.py --url "https://www.tiktok.com/@radio_kart" --limit 50
```

**Command-line Arguments:**
- `--url` (required): TikTok username (with or without @) or full profile URL
- `--limit` (optional): Number of videos to analyze (default: 10)

---

### 2. aggregate_sound_analysis.py

**Purpose:** Aggregates sound/song usage data across multiple TikTok accounts.

**Process:**
1. Defines a hardcoded list of 8 accounts to analyze
2. For each account, calls `tiktok_analyzer.py` via subprocess
3. Parses the output using regex to extract:
   - Song title and artist
   - Engagement metrics for each video
4. Groups all videos by sound key (format: "Song Title - Artist Name")
5. Calculates aggregate statistics per sound:
   - Total uses
   - Total and average views/likes/comments/shares
   - Average engagement rate
   - List of accounts using the sound
6. Outputs formatted report showing top sounds by usage

**Dependencies:**
- Python: `re`, `collections`, `subprocess`
- External: `tiktok_analyzer.py`, `yt-dlp` (via tiktok_analyzer)
- Optional: `claude` CLI (for bash output retrieval - can be removed)

**Hardcoded Accounts:**
- @radio_kart
- @steves.dreams
- @lovelatenightdrives
- @coffeemusicsoul
- @coffee.with.her
- @Chillkyle32
- @clevis.the.cowboy
- @ericcromartie

**Usage:**
```bash
python3 aggregate_sound_analysis.py
```

**Note:** Accounts list must be modified in the script source code (lines 12-21).

---

### 3. find_exclusive_songs.py

**Purpose:** Identifies songs used exclusively by specific target accounts vs those shared with other accounts.

**Process:**
1. Defines two account lists:
   - TARGET_ACCOUNTS (3 accounts): @ericcromartie, @johnsamuelsmathers, @johnny.secret.account
   - ACCOUNTS (37 total accounts to analyze)
2. For each account, scrapes videos using yt-dlp
3. Filters videos to only November 2025 (hardcoded date filter)
4. Extracts song information from each video
5. Builds a map of sound_key → set of accounts using it
6. Identifies songs where ALL using accounts are in TARGET_ACCOUNTS
7. Outputs list of exclusive songs

**Dependencies:**
- Python: `sys`, `subprocess`, `json`, `collections`, `datetime`
- External: `yt-dlp`

**Date Filter:**
- Hardcoded to only analyze videos from November 2025 (lines 85-92)
- Uses upload_date field from yt-dlp metadata

**Usage:**
```bash
python3 find_exclusive_songs.py
```

**Output Example:**
```
SONGS USED EXCLUSIVELY BY TARGET ACCOUNTS
Found 150 songs used ONLY by @ericcromartie, @johnsamuelsmathers, or @johnny.secret.account

#1
  Song:   Heather
  Artist: Conan Gray
  Used by: @ericcromartie, @johnny.secret.account
```

---

### 4. generate_song_excel.py

**Purpose:** Creates an Excel spreadsheet with separate sheets for each shared song, containing all TikTok video links using that song.

**Process:**
1. Defines ACCOUNTS list (40 accounts)
2. Defines EXCLUSIVE_SONGS set (150+ songs to filter out)
3. Scrapes all videos from October 1, 2025 onwards for each account
4. Filters out exclusive songs
5. Groups remaining videos by sound_key
6. Creates Excel workbook using openpyxl:
   - One sheet per song
   - Sheet name limited to 31 characters (Excel limitation)
   - Columns: Account, TikTok URL, Upload Date, Views, Likes, Comments, Shares
   - Styled header row with freeze panes
7. Saves to: `/Users/risingtidesdev/Desktop/clipper_project_fixed/shared_songs_tiktok_links_oct_nov2025.xlsx`

**Dependencies:**
- Python: `sys`, `subprocess`, `json`, `datetime`, `collections`
- Packages: `openpyxl` (with `Font`, `PatternFill`, `Alignment` styles)
- External: `yt-dlp`

**Date Filter:**
- Hardcoded cutoff: October 1, 2025 (line 184)

**Usage:**
```bash
python3 generate_song_excel.py
```

**Output File:**
- Path: `/Users/risingtidesdev/Desktop/clipper_project_fixed/shared_songs_tiktok_links_oct_nov2025.xlsx`
- Format: Excel 2007+ (.xlsx)

---

### 5. generate_complete_html.py

**Purpose:** Generates a comprehensive HTML report with cyberpunk-themed design showing sound usage statistics.

**Process:**
1. Scrapes 6 accounts for the last 100 videos each
2. Parses video data from tiktok_analyzer output via regex
3. Aggregates videos by sound/song
4. Generates HTML with embedded CSS (no external dependencies)
5. Creates styled report showing:
   - Overall statistics (total videos, unique sounds, accounts, views)
   - Each sound with:
     - Rank by total uses
     - Song title and artist
     - Total uses and accounts using it
     - Average and total metrics
     - Table of all videos using the sound
6. Writes to: `/Users/risingtidesdev/Desktop/clipper_project_fixed/sound_usage_complete_report.html`

**Design Features:**
- Cyberpunk theme with purple/blue gradients
- Custom fonts (Inter, Orbitron) from Google Fonts
- Animated drift background effect
- Responsive design
- Engagement badges (high/medium/low)
- Clickable video links

**Dependencies:**
- Python: `subprocess`, `re`, `collections`
- External: `tiktok_analyzer.py`, `yt-dlp`

**Hardcoded Accounts (6):**
- @radio_kart
- @steves.dreams
- @lovelatenightdrives
- @coffeemusicsoul
- @coffee.with.her
- @Chillkyle32

**Usage:**
```bash
python3 generate_complete_html.py
```

---

### 6. generate_glass_html.py

**Purpose:** Generates an HTML report with modern glassmorphism design (cleaner aesthetic than cyberpunk version).

**Process:**
- Identical to `generate_complete_html.py` but with different CSS styling
- Uses glassmorphism design patterns:
  - Translucent backgrounds with backdrop blur
  - Subtle borders and shadows
  - Clean typography
  - Purple accent color scheme

**Dependencies:**
- Same as `generate_complete_html.py`

**Usage:**
```bash
python3 generate_glass_html.py
```

**Output File:**
- Path: `/Users/risingtidesdev/Desktop/clipper_project_fixed/sound_usage_complete_report.html`
- Note: Overwrites same file as generate_complete_html.py

---

### 7. inhouse_network_scraper.py

**Purpose:** Comprehensive network tracking tool that scrapes 41 accounts and generates dual-view HTML report (by sound and by account).

**Process:**
1. Scrapes ALL videos from 41 accounts (from October 1, 2025 onwards)
2. Filters out exclusive songs (145 songs defined in EXCLUSIVE_SONGS)
3. Aggregates data in two ways:
   - By sound (showing which accounts use each sound)
   - By account (showing performance metrics per account)
4. Generates HTML with tab navigation between views
5. Includes engagement analysis and performance indicators

**Key Features:**
- Tabbed interface (Sound view / Account view)
- Performance indicators (high/medium/low colored dots)
- Account rankings by engagement rate
- Top 10 videos shown per account
- Responsive glassmorphism design

**Dependencies:**
- Python: `subprocess`, `json`, `re`, `collections`, `datetime`
- External: `yt-dlp`

**Hardcoded Settings:**
- 41 accounts tracked
- 145 exclusive songs filtered
- Date cutoff: October 1, 2025

**Usage:**
```bash
python3 inhouse_network_scraper.py
```

**Output File:**
- Path: `/Users/risingtidesdev/Desktop/clipper_project_fixed/inhouse_network_tracker_oct_nov2025.html`
- Size: Can be large (10-20MB) depending on data volume

**Performance:**
- Scraping 41 accounts can take 30-60 minutes
- No rate limiting implemented
- Downloads all available videos per account

---

## Data Flow

### Typical Workflow

```
1. yt-dlp scrapes TikTok
   ↓
2. JSON metadata extracted
   ↓
3. Python scripts parse and aggregate
   ↓
4. Generate reports (HTML/Excel)
```

### Detailed Flow Diagram

```
TikTok Profile URL
    ↓
[yt-dlp CLI]
    ↓
JSON Lines Output
    ↓
[Python JSON Parser]
    ↓
Video Metadata Objects
    ├─→ Views, Likes, Comments, Shares
    ├─→ Song Title, Artist
    ├─→ Upload Date
    └─→ Video URL
    ↓
[Aggregation Logic]
    ├─→ Group by Sound
    ├─→ Group by Account
    └─→ Calculate Engagement Rate
    ↓
[Report Generator]
    ├─→ HTML (generate_*_html.py)
    └─→ Excel (generate_song_excel.py)
    ↓
Final Report Files
```

---

## Configuration

### Account Lists

All scripts contain hardcoded account lists. To modify accounts:

**Example (inhouse_network_scraper.py, lines 14-56):**
```python
ACCOUNTS = [
    '@backroaddriver',
    '@spaceboylonerism',
    # Add your accounts here
]
```

### Date Filters

Date filtering is hardcoded in multiple scripts:

**Example:**
```python
# Filter for October 1st, 2025 onwards
cutoff_date = datetime(2025, 10, 1)
if upload_datetime < cutoff_date:
    continue
```

To modify date ranges, search for `datetime(2025, 10, 1)` and update accordingly.

### Output Paths

Output file paths are hardcoded as absolute paths:

**Example:**
```python
output_file = '/Users/risingtidesdev/Desktop/clipper_project_fixed/inhouse_network_tracker_oct_nov2025.html'
```

**To modify:**
1. Search for `/Users/risingtidesdev/Desktop/clipper_project_fixed/`
2. Replace with your desired output directory
3. Ensure directory exists before running

### Exclusive Songs List

The `inhouse_network_scraper.py` and `generate_song_excel.py` scripts filter out songs exclusive to certain accounts.

**Location:** Lines 60-146 in `inhouse_network_scraper.py`

**Format:**
```python
EXCLUSIVE_SONGS = {
    '20201203 - Mac DeMarco',
    'A Dream - Flatsound',
    # Add more in format: 'Song Title - Artist Name'
}
```

---

## Troubleshooting

### Common Issues

#### 1. "yt-dlp: command not found"
**Solution:**
```bash
# Install yt-dlp
pip install yt-dlp
# OR
brew install yt-dlp
```

#### 2. "ModuleNotFoundError: No module named 'openpyxl'"
**Solution:**
```bash
pip install openpyxl
```

#### 3. "Permission denied" when running scripts
**Solution:**
```bash
chmod +x *.py
```

#### 4. yt-dlp rate limiting / blocked
**Solution:**
- Wait 5-10 minutes between large scrapes
- Use `--sleep-interval 5` flag with yt-dlp
- Consider using a VPN if blocked by region

#### 5. Empty or incomplete data
**Causes:**
- Account is private
- Videos were deleted
- Date filter excludes all videos

**Solution:**
- Verify account exists and is public
- Check date filters in code
- Run with `--limit 1` to test a single video first

#### 6. JSON parsing errors
**Cause:** yt-dlp output format changed

**Solution:**
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Check yt-dlp GitHub for breaking changes

---

## Performance Optimization

### Speed Improvements

1. **Reduce account list** - Test with 2-3 accounts first
2. **Use --limit flag** - Analyze fewer videos per account
3. **Parallel processing** - Run multiple scripts simultaneously (not implemented)
4. **Cache results** - Save yt-dlp JSON to files to avoid re-scraping

### Memory Management

- Large scrapes (40+ accounts, all videos) can use 500MB-1GB RAM
- Close other applications when running large analyses
- Consider processing accounts in batches

---

## Security Considerations

### API Keys
- These scripts do NOT require TikTok API keys
- yt-dlp uses public web scraping (no authentication)

### Rate Limiting
- TikTok may rate limit or block excessive scraping
- No built-in rate limiting in these scripts
- Recommended: Add delays between account scrapes

### Data Privacy
- Scripts download public TikTok data only
- Generated reports may contain user handles and video URLs
- Do not share reports without permission

---

## Advanced Usage

### Customizing HTML Themes

Both HTML generators have inline CSS. To customize:

1. Locate `<style>` section in script
2. Modify CSS variables:
   - Colors: Search for hex codes (`#8a2be2`, etc.)
   - Fonts: Modify `@import url()` and `font-family`
   - Spacing: Adjust `padding`, `margin` values

### Adding New Metrics

To track additional metrics:

1. Check yt-dlp JSON output for available fields:
   ```bash
   yt-dlp --dump-json --flat-playlist --playlist-end 1 [URL] | jq
   ```
2. Add field extraction in parsing function
3. Update aggregation logic
4. Modify HTML/Excel output templates

### Batch Processing

To process multiple account lists:

```bash
#!/bin/bash
# batch_process.sh

python3 generate_complete_html.py  # Set A accounts
# Manually change ACCOUNTS in script
python3 generate_complete_html.py  # Set B accounts
```

---

## Quick Start Checklist

- [ ] Python 3.7+ installed
- [ ] yt-dlp installed and working (`yt-dlp --version`)
- [ ] openpyxl installed (`pip install openpyxl`)
- [ ] Scripts downloaded to local directory
- [ ] Account lists configured in scripts
- [ ] Output paths updated for your system
- [ ] Test run with 1 account: `python3 tiktok_analyzer.py --url @radio_kart --limit 5`
- [ ] Full run of desired script

---

## Support and Maintenance

### Updating Dependencies

```bash
# Update yt-dlp (recommended monthly)
pip install --upgrade yt-dlp

# Update openpyxl
pip install --upgrade openpyxl
```

### Script Version Control

These scripts do not have version numbers. Track changes manually or use git:

```bash
git init
git add *.py
git commit -m "Initial commit of tracker scripts"
```

### Known Limitations

1. **No API access** - Relies on web scraping which can break
2. **Hardcoded paths** - Must be updated for different systems
3. **No error recovery** - Failed scrapes are skipped, not retried
4. **Single-threaded** - Processes accounts sequentially
5. **No database** - All data processed in-memory each run

---

## License and Attribution

These scripts use:
- **yt-dlp** - Unlicense (Public Domain)
- **openpyxl** - MIT License
- **Python** - PSF License

---

## Changelog

**Current Version:** Undated (as of November 2025)

**Known Issues:**
- aggregate_sound_analysis.py references `claude` CLI which may not be available
- All date filters hardcoded to 2025 dates
- Output paths hardcoded to specific user directory

---

## Conclusion

This documentation covers all aspects of the TikTok tracker scripts. For additional help, review the inline code comments or modify the scripts to add debug logging.

**Next Steps:**
1. Install all dependencies
2. Test with a single account
3. Customize account lists and date filters
4. Run full analysis
5. Review generated HTML/Excel reports
