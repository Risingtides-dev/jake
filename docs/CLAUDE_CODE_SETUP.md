# Claude Code Setup Guide for TikTok Tracker Scripts

This guide is designed to be read by Claude Code (AI assistant) to help walk you through setting up everything needed to run the TikTok tracker scripts.

---

## Overview for Claude Assistant

**Dear Claude Code AI:**

This folder contains TikTok tracker scripts that require:
1. Claude Code CLI installed and configured
2. Python 3.7+ installed
3. yt-dlp installed (TikTok scraper)
4. openpyxl Python package installed
5. Platform-specific path configurations

The user needs help setting up Claude Code as a command-line tool, then configuring their environment to run these Python scripts.

---

## Part 1: Installing Claude Code

### For Mac Users

#### Step 1: Install Claude Code CLI

Claude Code provides a command-line interface. Installation instructions:

```bash
# Visit the Claude Code website to download
# https://claude.com/claude-code

# After installation, verify Claude Code is installed:
claude --version
```

**If `claude` command not found:**
1. Check if Claude Code desktop app is installed
2. Claude Code typically installs CLI automatically
3. May need to restart terminal after installation
4. Check PATH: `echo $PATH | grep -i claude`

#### Step 2: Configure Claude Code for Terminal Use

```bash
# Verify Claude Code CLI works
claude --help

# Test Claude Code can run commands
claude "echo Hello from Claude Code"
```

### For Windows Users

#### Step 1: Install Claude Code

```cmd
REM Download Claude Code from:
REM https://claude.com/claude-code

REM After installation, open Command Prompt or PowerShell
REM Verify installation:
claude --version
```

**If `claude` command not found:**
1. Restart Command Prompt/PowerShell after installing Claude Code
2. Check if added to PATH: `echo %PATH%` (CMD) or `$env:PATH` (PowerShell)
3. May need to restart computer

#### Step 2: Test Claude Code CLI

```cmd
REM Test Claude Code
claude --help

REM Verify it can execute commands
claude "echo Hello from Claude Code"
```

---

## Part 2: Install Python and Dependencies

### Mac Installation

```bash
# Step 1: Check if Python 3 is installed
python3 --version

# If not installed or version < 3.7:
# Install Homebrew first (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Step 2: Install yt-dlp (CRITICAL for TikTok scraping)
brew install yt-dlp

# Verify yt-dlp works
yt-dlp --version

# Step 3: Install Python package for Excel generation
pip3 install openpyxl

# Verify installation
python3 -c "import openpyxl; print('openpyxl installed successfully')"
```

### Windows Installation

```cmd
REM Step 1: Check Python installation
python --version

REM If not installed, download from python.org
REM IMPORTANT: Check "Add Python to PATH" during installation
REM https://www.python.org/downloads/

REM Step 2: Install yt-dlp (CRITICAL for TikTok scraping)
pip install yt-dlp

REM Verify yt-dlp works
yt-dlp --version

REM Step 3: Install Python package for Excel generation
pip install openpyxl

REM Verify installation
python -c "import openpyxl; print('openpyxl installed successfully')"
```

---

## Part 3: Configure Scripts for Your Platform

### Understanding the Path Issue

The scripts were written on a Mac with hardcoded paths:
```python
'/Users/risingtidesdev/Desktop/clipper_project_fixed/'
```

These MUST be updated for your system.

### For Mac Users

If your username is different from `risingtidesdev`, update paths:

```bash
# Your paths should look like:
/Users/YOUR_USERNAME/Desktop/clipper_project_fixed/tracker_data/
```

**Files to update:**
1. `aggregate_sound_analysis.py` - Line 184
2. `generate_complete_html.py` - Lines 601, 626
3. `generate_glass_html.py` - Lines 553, 568
4. `generate_song_excel.py` - Line 315
5. `inhouse_network_scraper.py` - Line 1082

### For Windows Users

**CRITICAL:** Update ALL paths from Mac format to Windows format.

**Find and replace in each script:**

```python
# FIND:
'/Users/risingtidesdev/Desktop/clipper_project_fixed/'

# REPLACE WITH (example):
'C:\\Users\\YourUsername\\Desktop\\tracker_data\\'

# OR use forward slashes (Python accepts both):
'C:/Users/YourUsername/Desktop/tracker_data/'
```

**Also update Python command in subprocess calls:**

```python
# FIND in aggregate_sound_analysis.py and others:
['python3', 'tiktok_analyzer.py']

# REPLACE WITH:
['python', 'tiktok_analyzer.py']
```

---

## Part 4: Testing Your Setup

### Quick Test Commands

#### Mac
```bash
# 1. Navigate to tracker directory
cd ~/Desktop/clipper_project_fixed/tracker_data

# 2. Test yt-dlp can scrape TikTok
yt-dlp --flat-playlist --dump-json --playlist-end 1 "https://www.tiktok.com/@radio_kart"

# 3. Test Python imports
python3 -c "import sys, json, subprocess, openpyxl; print('All imports OK')"

# 4. Test a single account analysis (quick test)
python3 tiktok_analyzer.py --url @radio_kart --limit 3

# If all work, you're ready to run full scripts!
```

#### Windows
```cmd
REM 1. Navigate to tracker directory
cd C:\Users\YourUsername\Desktop\tracker_data

REM 2. Test yt-dlp can scrape TikTok
yt-dlp --flat-playlist --dump-json --playlist-end 1 "https://www.tiktok.com/@radio_kart"

REM 3. Test Python imports
python -c "import sys, json, subprocess, openpyxl; print('All imports OK')"

REM 4. Test a single account analysis (quick test)
python tiktok_analyzer.py --url @radio_kart --limit 3

REM If all work, you're ready to run full scripts!
```

---

## Part 5: Using Claude Code with These Scripts

### How Claude Code Can Help

Once Claude Code is set up, you can ask it to:

1. **Run scripts for you:**
   ```
   "Run tiktok_analyzer.py on account @radio_kart with limit 10"
   ```

2. **Update file paths automatically:**
   ```
   "Update all file paths in these scripts to use C:\Users\MyName\Desktop\tracker_data"
   ```

3. **Debug errors:**
   ```
   "I got this error when running the script: [paste error]"
   ```

4. **Modify account lists:**
   ```
   "Add @newaccount to the ACCOUNTS list in inhouse_network_scraper.py"
   ```

5. **Explain script output:**
   ```
   "Explain the HTML report that was generated"
   ```

### Claude Code Workflow Example

```
User: "I need to run the network scraper for all 41 accounts"

Claude Code:
1. Checks if all dependencies are installed
2. Updates paths if needed
3. Runs the script: python3 inhouse_network_scraper.py
4. Monitors progress and reports status
5. Opens the generated HTML report when done
```

---

## Part 6: Running the Scripts

### Available Scripts

#### 1. tiktok_analyzer.py
**Purpose:** Analyze a single TikTok account

**Usage:**
```bash
# Mac
python3 tiktok_analyzer.py --url @accountname --limit 10

# Windows
python tiktok_analyzer.py --url @accountname --limit 10
```

**Options:**
- `--url` (required): TikTok account (@username or full URL)
- `--limit` (optional): Number of videos to analyze (default: 10)

**Output:** Terminal output with engagement metrics and song data

---

#### 2. aggregate_sound_analysis.py
**Purpose:** Aggregate sound usage across 8 hardcoded accounts

**Usage:**
```bash
# Mac
python3 aggregate_sound_analysis.py

# Windows
python aggregate_sound_analysis.py
```

**Output:** Terminal report showing which songs are used across accounts

**Note:** Account list is hardcoded in the script (lines 12-21)

---

#### 3. find_exclusive_songs.py
**Purpose:** Find songs used exclusively by target accounts

**Usage:**
```bash
# Mac
python3 find_exclusive_songs.py

# Windows
python find_exclusive_songs.py
```

**Output:** Terminal list of songs used ONLY by @ericcromartie, @johnsamuelsmathers, @johnny.secret.account

**Runtime:** 5-10 minutes (scrapes 37 accounts)

---

#### 4. generate_song_excel.py
**Purpose:** Create Excel spreadsheet with separate sheet for each song

**Usage:**
```bash
# Mac
python3 generate_song_excel.py

# Windows
python generate_song_excel.py
```

**Output:** `shared_songs_tiktok_links_oct_nov2025.xlsx`

**Runtime:** 10-20 minutes (scrapes 40 accounts)

**File location:** Same directory as script (or path specified in line 315)

---

#### 5. generate_complete_html.py
**Purpose:** Generate cyberpunk-themed HTML report

**Usage:**
```bash
# Mac
python3 generate_complete_html.py

# Windows
python generate_complete_html.py
```

**Output:** `sound_usage_complete_report.html` (cyberpunk design)

**Runtime:** 5-10 minutes (scrapes 6 accounts, 100 videos each)

---

#### 6. generate_glass_html.py
**Purpose:** Generate glassmorphism-themed HTML report

**Usage:**
```bash
# Mac
python3 generate_glass_html.py

# Windows
python generate_glass_html.py
```

**Output:** `sound_usage_complete_report.html` (glassmorphism design)

**Runtime:** 5-10 minutes (scrapes 6 accounts, 100 videos each)

---

#### 7. inhouse_network_scraper.py
**Purpose:** Comprehensive network tracker for 41 accounts

**Usage:**
```bash
# Mac
python3 inhouse_network_scraper.py

# Windows
python inhouse_network_scraper.py
```

**Output:** `inhouse_network_tracker_oct_nov2025.html`

**Runtime:** 30-60 minutes (scrapes 41 accounts, ALL videos from Oct 2025+)

**Features:**
- Tabbed interface (Sound view / Account view)
- Performance rankings
- Engagement metrics
- Filters out 145 exclusive songs

---

## Part 7: Common Issues and Solutions

### Issue: "claude: command not found"

**Solution:**
1. Verify Claude Code app is installed
2. Restart terminal/command prompt
3. Check if Claude Code CLI was installed during app installation
4. May need to manually add to PATH

### Issue: "python3: command not found" (Mac)

**Solution:**
```bash
brew install python@3.11
```

### Issue: "python: command not found" (Windows)

**Solution:**
1. Download Python from python.org
2. During installation, CHECK "Add Python to PATH"
3. Restart Command Prompt after installation

### Issue: "yt-dlp: command not found"

**Mac:**
```bash
brew install yt-dlp
```

**Windows:**
```cmd
pip install yt-dlp
```

### Issue: "ModuleNotFoundError: No module named 'openpyxl'"

**Solution:**
```bash
# Mac
pip3 install openpyxl

# Windows
pip install openpyxl
```

### Issue: Scripts output "Error scraping profile"

**Possible causes:**
1. TikTok account is private
2. Account doesn't exist
3. Network connection issue
4. TikTok rate limiting

**Solution:**
- Verify account exists and is public
- Wait 5-10 minutes between large scrapes
- Test with a single account first

### Issue: Path errors on Windows

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/Users/risingtidesdev/...'
```

**Solution:**
Update all paths in scripts from Mac format to Windows format (see Part 3)

### Issue: Empty or no data returned

**Causes:**
- Date filters exclude all videos (scripts filter for Oct-Nov 2025)
- Account has no recent videos
- Account was deleted

**Solution:**
Check date filters in scripts and adjust if needed

---

## Part 8: Checklist for Setup

### Initial Setup Checklist

- [ ] Claude Code desktop app installed
- [ ] Claude Code CLI working (`claude --version`)
- [ ] Python 3.7+ installed (`python3 --version` or `python --version`)
- [ ] yt-dlp installed (`yt-dlp --version`)
- [ ] openpyxl installed (`pip list | grep openpyxl`)
- [ ] Scripts downloaded to local folder
- [ ] File paths updated for your system (Windows users)
- [ ] Python command updated in scripts (Windows users)
- [ ] Output directory exists and is writable

### Pre-Run Checklist

- [ ] Navigate to tracker_data directory
- [ ] Test yt-dlp can access TikTok
- [ ] Test Python imports work
- [ ] Run quick test with tiktok_analyzer.py
- [ ] Verify output location is correct

### Post-Run Checklist

- [ ] Check output files were created
- [ ] Open HTML reports in browser
- [ ] Open Excel files to verify data
- [ ] Check terminal for any errors
- [ ] Save/backup generated reports

---

## Part 9: Directory Structure

Expected folder structure:

```
tracker_data/
├── CLAUDE_CODE_SETUP.md           ← This file
├── TRACKER_DOCUMENTATION.md       ← Detailed technical docs
├── SETUP_MAC.md                   ← Mac-specific setup
├── SETUP_WINDOWS.md               ← Windows-specific setup
├── PLATFORM_DIFFERENCES.md        ← Mac vs Windows guide
├── requirements.txt               ← Python dependencies
├── README.md                      ← Project overview
│
├── tiktok_analyzer.py             ← Core analyzer script
├── aggregate_sound_analysis.py    ← Sound aggregation
├── find_exclusive_songs.py        ← Exclusive song finder
├── generate_song_excel.py         ← Excel generator
├── generate_complete_html.py      ← Cyberpunk HTML
├── generate_glass_html.py         ← Glassmorphism HTML
└── inhouse_network_scraper.py     ← Full network tracker
```

Generated output files (after running scripts):
```
tracker_data/
├── shared_songs_tiktok_links_oct_nov2025.xlsx
├── sound_usage_complete_report.html
└── inhouse_network_tracker_oct_nov2025.html
```

---

## Part 10: Getting Help from Claude Code

### How to Ask Claude Code for Help

Once you have Claude Code set up and you're in the tracker_data directory, you can ask:

**Setup Questions:**
- "Can you verify all my dependencies are installed?"
- "I'm on Windows, can you update the paths in all scripts?"
- "Walk me through testing that yt-dlp works"

**Running Scripts:**
- "Run tiktok_analyzer on @radio_kart with 10 videos"
- "Generate the Excel report for me"
- "Run the full network scraper and let me know when it's done"

**Troubleshooting:**
- "I got this error: [paste error message]"
- "The script isn't finding any videos, why?"
- "How do I change the date filter in the scripts?"

**Customization:**
- "Add @newaccount to the accounts list"
- "Change the output path to save files in my Documents folder"
- "Update the exclusive songs list to include [song name]"

---

## Part 11: Next Steps After Setup

Once everything is installed and working:

1. **Start with a small test:**
   ```bash
   python3 tiktok_analyzer.py --url @radio_kart --limit 5
   ```

2. **Review the output** to understand the data format

3. **Try a larger script:**
   ```bash
   python3 generate_glass_html.py
   ```

4. **Open the generated HTML** to see the report

5. **Customize account lists** in scripts for your needs

6. **Run the full network tracker** when ready (30-60 min)

7. **Use Claude Code** to help modify and enhance scripts

---

## Part 12: Important Notes

### Rate Limiting
- TikTok may rate limit or block excessive scraping
- Recommended: Wait 5-10 minutes between large runs
- No built-in rate limiting in these scripts

### Data Privacy
- Scripts only access public TikTok data
- Generated reports contain usernames and video URLs
- Do not share reports without permission

### Performance
- Scripts are single-threaded (process accounts one at a time)
- Can take 30-60 minutes for 41 accounts
- Close other applications for better performance

### Updates
- Keep yt-dlp updated: `pip install --upgrade yt-dlp`
- TikTok changes may break scraping (update yt-dlp if this happens)
- Check GitHub for yt-dlp updates regularly

---

## Summary

**For Claude Code AI reading this:**

The user needs your help to:
1. Verify Claude Code CLI is installed and working
2. Install Python 3.7+, yt-dlp, and openpyxl
3. Update file paths in scripts for their platform (especially Windows)
4. Test the setup with a quick script run
5. Guide them through running the full scripts
6. Help troubleshoot any errors that occur

**Key things to check:**
- Platform (Mac vs Windows)
- Python command (`python3` vs `python`)
- Path format (forward vs backslash)
- yt-dlp installation
- openpyxl installation

**Quick test sequence:**
1. `yt-dlp --version`
2. `python3 --version` (or `python --version`)
3. `python3 -c "import openpyxl; print('OK')"`
4. `python3 tiktok_analyzer.py --url @radio_kart --limit 3`

If all succeed, the user is ready to run the full scripts!

For detailed documentation, refer to `TRACKER_DOCUMENTATION.md`.
