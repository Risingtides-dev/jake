# Windows Setup Guide for TikTok Tracker Scripts

## Prerequisites

- **Windows 10 or Windows 11**
- **Administrator access** (for installing software)
- **Internet connection**

---

## Step-by-Step Installation

### Step 1: Install Python

1. Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT:** During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```
   OR
   ```cmd
   python3 --version
   ```

### Step 2: Install yt-dlp

**Option A: Using pip (Recommended)**
```cmd
pip install yt-dlp
```

**Option B: Using Windows executable**
1. Download from: https://github.com/yt-dlp/yt-dlp/releases/latest
2. Download `yt-dlp.exe`
3. Place in `C:\Windows\System32\` OR add to PATH

**Verify installation:**
```cmd
yt-dlp --version
```

### Step 3: Install Python Packages

```cmd
# Navigate to project directory
cd C:\Users\YourUsername\Desktop\tracker_data

# Install openpyxl
pip install openpyxl

# Verify
python -c "import openpyxl; print('OK')"
```

---

## Configuration Changes Required

### 1. Update File Paths in Scripts

All scripts have hardcoded Mac paths that MUST be changed:

**Find and Replace:**
- **OLD:** `/Users/risingtidesdev/Desktop/clipper_project_fixed/`
- **NEW:** `C:\\Users\\YourUsername\\Desktop\\tracker_data\\`

**Files to update:**
- `aggregate_sound_analysis.py` (line 184)
- `generate_complete_html.py` (line 601, 626)
- `generate_glass_html.py` (line 553, 568)
- `generate_song_excel.py` (line 315)
- `inhouse_network_scraper.py` (line 1082)

**Example change:**
```python
# BEFORE (Mac)
output_file = '/Users/risingtidesdev/Desktop/clipper_project_fixed/report.html'

# AFTER (Windows)
output_file = 'C:\\Users\\YourUsername\\Desktop\\tracker_data\\report.html'
```

**Or use relative paths (recommended):**
```python
import os
output_file = os.path.join(os.path.dirname(__file__), 'report.html')
```

### 2. Python Command

Windows might use `python` instead of `python3`:

**In scripts, update subprocess calls:**
```python
# BEFORE
cmd = ['python3', 'tiktok_analyzer.py', '--url', account]

# AFTER (try both)
cmd = ['python', 'tiktok_analyzer.py', '--url', account]
# OR
cmd = ['python3', 'tiktok_analyzer.py', '--url', account]
```

### 3. Test Your Python Command

```cmd
python --version
python3 --version
```

Use whichever one works.

---

## Running the Scripts

### Basic Usage

```cmd
# Single account analysis
python tiktok_analyzer.py --url @radio_kart --limit 10

# Generate Excel report
python generate_song_excel.py

# Generate HTML report
python inhouse_network_scraper.py
```

### Using Command Prompt

1. Press `Win + R`
2. Type `cmd` and press Enter
3. Navigate to script directory:
   ```cmd
   cd C:\Users\YourUsername\Desktop\tracker_data
   ```
4. Run scripts as shown above

### Using PowerShell (Alternative)

1. Press `Win + X` → Select "Windows PowerShell"
2. Navigate to directory:
   ```powershell
   cd C:\Users\YourUsername\Desktop\tracker_data
   ```
3. Run scripts using `python` or `python3`

---

## Virtual Environment (Recommended)

### Create Virtual Environment

```cmd
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Install dependencies
pip install openpyxl yt-dlp

# When done, deactivate
deactivate
```

---

## Troubleshooting Windows-Specific Issues

### Issue: "python is not recognized"

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. OR manually add Python to PATH:
   - Search "Environment Variables" in Start Menu
   - Edit System Environment Variables
   - Add `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3X\` to PATH
   - Add `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3X\Scripts\` to PATH

### Issue: "yt-dlp is not recognized"

**Solution:**
```cmd
pip install --upgrade yt-dlp
# OR download yt-dlp.exe and place in C:\Windows\System32\
```

### Issue: Permission denied when writing files

**Solution:**
- Run Command Prompt as Administrator
- OR save output files to your Documents folder instead:
  ```python
  output_file = 'C:\\Users\\YourUsername\\Documents\\report.html'
  ```

### Issue: Backslash path errors

Windows uses backslashes `\` in paths. In Python strings, use:
- Double backslashes: `"C:\\Users\\Name\\file.txt"`
- OR forward slashes (Python accepts both): `"C:/Users/Name/file.txt"`
- OR raw strings: `r"C:\Users\Name\file.txt"`

### Issue: Scripts taking too long

**Same as Mac** - TikTok rate limiting. Wait 5-10 minutes between runs.

---

## File Output Locations

After running scripts, find outputs at:
```
C:\Users\YourUsername\Desktop\tracker_data\
├── shared_songs_tiktok_links_oct_nov2025.xlsx
├── sound_usage_complete_report.html
└── inhouse_network_tracker_oct_nov2025.html
```

---

## Windows-Specific Performance Tips

1. **Disable Windows Defender scanning** on the tracker_data folder temporarily (speeds up file operations)
2. **Close browser and heavy apps** before running large scrapes
3. **Use SSD location** for output files (faster than HDD)
4. **Run overnight** for 41-account scrapes (30-60 minutes)

---

## Quick Test

```cmd
# Test yt-dlp
yt-dlp --flat-playlist --dump-json --playlist-end 1 "https://www.tiktok.com/@radio_kart"

# Test Python imports
python -c "import sys, json, openpyxl; print('All imports OK')"

# Test single account
python tiktok_analyzer.py --url @radio_kart --limit 3
```

---

## Summary Checklist

- [ ] Python 3.8+ installed (with "Add to PATH")
- [ ] yt-dlp installed (`yt-dlp --version` works)
- [ ] openpyxl installed (`pip install openpyxl`)
- [ ] All file paths updated in scripts (Mac → Windows paths)
- [ ] Python command verified (`python` vs `python3`)
- [ ] Output directory exists
- [ ] Test run successful

---

## Need Help?

Common Windows errors:
- **"Access is denied"** → Run as Administrator OR change output folder
- **"No module named X"** → `pip install X`
- **"python not found"** → Add Python to PATH or reinstall
- **Paths not working** → Use double backslashes `\\` or forward slashes `/`

For detailed script documentation, see `TRACKER_DOCUMENTATION.md`
