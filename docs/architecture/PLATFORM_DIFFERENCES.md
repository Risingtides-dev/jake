# Platform Differences: Mac vs Windows

## Quick Reference Table

| Feature | Mac | Windows |
|---------|-----|---------|
| **Python command** | `python3` | `python` or `python3` |
| **Path separator** | `/` | `\` (use `\\` in strings) |
| **Virtual env activate** | `source venv/bin/activate` | `venv\Scripts\activate` |
| **Home directory** | `/Users/username/` | `C:\Users\Username\` |
| **yt-dlp install** | `brew install yt-dlp` | `pip install yt-dlp` |
| **Line endings** | LF (`\n`) | CRLF (`\r\n`) |
| **Package manager** | Homebrew | pip / chocolatey |

---

## Critical Changes for Windows Users

### 1. File Paths

All scripts contain Mac-specific paths that MUST be updated:

**Mac path:**
```python
'/Users/risingtidesdev/Desktop/clipper_project_fixed/output.html'
```

**Windows path:**
```python
'C:\\Users\\YourUsername\\Desktop\\tracker_data\\output.html'
```

**Better (cross-platform):**
```python
import os
output_file = os.path.join(os.path.dirname(__file__), 'output.html')
```

### 2. Python Command

**Mac:**
```bash
python3 script.py
```

**Windows:**
```cmd
python script.py
```

Update subprocess calls in scripts:
```python
# Mac version
subprocess.run(['python3', 'tiktok_analyzer.py'])

# Windows version
subprocess.run(['python', 'tiktok_analyzer.py'])
```

### 3. Virtual Environment

**Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

---

## Scripts That Need Path Updates

### Files with hardcoded Mac paths:

1. **aggregate_sound_analysis.py**
   - Line 184: `base_dir = '/Users/risingtidesdev/Desktop/clipper_project_fixed'`

2. **generate_complete_html.py**
   - Line 601: `base_dir = '/Users/risingtidesdev/Desktop/clipper_project_fixed'`
   - Line 626: `output_file = f'{base_dir}/sound_usage_complete_report.html'`

3. **generate_glass_html.py**
   - Line 553: `base_dir = '/Users/risingtidesdev/Desktop/clipper_project_fixed'`
   - Line 568: `output_file = f'{base_dir}/sound_usage_complete_report.html'`

4. **generate_song_excel.py**
   - Line 315: `output_file = '/Users/risingtidesdev/Desktop/clipper_project_fixed/shared_songs_tiktok_links_oct_nov2025.xlsx'`

5. **inhouse_network_scraper.py**
   - Line 1082: `output_file = '/Users/risingtidesdev/Desktop/clipper_project_fixed/inhouse_network_tracker_oct_nov2025.html'`

### How to Update for Windows

**Option 1: Hardcode Windows path**
```python
# Windows
base_dir = 'C:\\Users\\YourUsername\\Desktop\\tracker_data'
output_file = 'C:\\Users\\YourUsername\\Desktop\\tracker_data\\report.html'
```

**Option 2: Use relative paths (recommended)**
```python
import os

# Get script directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Build output path
output_file = os.path.join(base_dir, 'report.html')
```

**Option 3: Use forward slashes (Python accepts on Windows)**
```python
# Works on both Mac and Windows
base_dir = 'C:/Users/YourUsername/Desktop/tracker_data'
```

---

## Installation Differences

### Mac

```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install yt-dlp
brew install yt-dlp

# Install Python packages
pip3 install openpyxl
```

### Windows

```cmd
# Install yt-dlp
pip install yt-dlp

# Install Python packages
pip install openpyxl
```

---

## Running Scripts

### Mac Terminal

```bash
cd ~/Desktop/clipper_project_fixed/tracker_data
python3 tiktok_analyzer.py --url @radio_kart --limit 10
```

### Windows Command Prompt

```cmd
cd C:\Users\YourUsername\Desktop\tracker_data
python tiktok_analyzer.py --url @radio_kart --limit 10
```

### Windows PowerShell

```powershell
cd C:\Users\YourUsername\Desktop\tracker_data
python tiktok_analyzer.py --url @radio_kart --limit 10
```

---

## Common Cross-Platform Issues

### Issue: Paths not working

**Mac:** Uses `/` for paths
```python
path = '/Users/username/file.txt'
```

**Windows:** Uses `\` for paths (must escape in strings)
```python
path = 'C:\\Users\\username\\file.txt'
```

**Solution:** Use `os.path.join()` for cross-platform compatibility
```python
import os
path = os.path.join('C:', 'Users', 'username', 'file.txt')
```

### Issue: Python command not found

**Mac:** Use `python3`
**Windows:** Use `python` (sometimes `python3` also works)

**Check which one works:**
```bash
python --version
python3 --version
```

### Issue: Line ending conflicts

If editing scripts on Windows then running on Mac (or vice versa):

**Mac:** Convert to Unix line endings
```bash
dos2unix script.py
```

**Windows:** Use editor that handles both (VS Code, Notepad++)

---

## Cross-Platform Script Template

For maximum compatibility, use this pattern:

```python
#!/usr/bin/env python3
"""Cross-platform script template"""

import os
import sys
import platform

# Detect platform
IS_WINDOWS = platform.system() == 'Windows'
IS_MAC = platform.system() == 'Darwin'

# Python executable
PYTHON_CMD = 'python' if IS_WINDOWS else 'python3'

# Path handling
if IS_WINDOWS:
    BASE_DIR = 'C:\\Users\\YourUsername\\Desktop\\tracker_data'
else:
    BASE_DIR = os.path.expanduser('~/Desktop/clipper_project_fixed/tracker_data')

# Or better - use relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build output path (works on both)
output_file = os.path.join(BASE_DIR, 'report.html')

# Run subprocess
import subprocess
cmd = [PYTHON_CMD, 'other_script.py', '--arg', 'value']
subprocess.run(cmd)
```

---

## Testing Compatibility

### Mac

```bash
# Test Python
python3 --version

# Test yt-dlp
yt-dlp --version

# Test imports
python3 -c "import os, sys, subprocess, json, openpyxl; print('OK')"

# Test path handling
python3 -c "import os; print(os.path.join('a', 'b', 'c'))"
```

### Windows

```cmd
# Test Python
python --version

# Test yt-dlp
yt-dlp --version

# Test imports
python -c "import os, sys, subprocess, json, openpyxl; print('OK')"

# Test path handling
python -c "import os; print(os.path.join('a', 'b', 'c'))"
```

---

## Recommended Workflow

### For Mac Users Sharing with Windows Users

1. Use relative paths instead of absolute paths
2. Use `os.path.join()` for all path operations
3. Use `python3` in shebangs but detect platform in code
4. Test scripts on Windows VM or with Windows user before sharing
5. Document any Mac-specific commands

### For Windows Users Receiving Mac Scripts

1. Search for `/Users/` and replace with `C:\\Users\\`
2. Replace `python3` with `python` in subprocess calls
3. Convert line endings if needed
4. Test with small dataset first
5. Update `README.md` with your changes

---

## Quick Migration Guide

### Converting Mac Script to Windows

```bash
# 1. Clone or copy scripts to Windows
# 2. Edit each script:

# Find:
'/Users/risingtidesdev/Desktop/clipper_project_fixed/'
'python3'

# Replace with:
'C:\\Users\\YourUsername\\Desktop\\tracker_data\\'
'python'

# 3. Test
python script_name.py
```

### Making Scripts Cross-Platform

```python
# Add at top of each script:
import os
import platform

# Replace hardcoded paths with:
if platform.system() == 'Windows':
    BASE_DIR = 'C:\\Users\\YourUsername\\Desktop\\tracker_data'
else:
    BASE_DIR = os.path.expanduser('~/Desktop/clipper_project_fixed/tracker_data')

# Or use relative paths:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
```

---

## Summary

**Must Change for Windows:**
- ✅ File paths (`/Users/...` → `C:\\Users\\...`)
- ✅ Python command (`python3` → `python`)
- ✅ Virtual environment activation

**Should Work on Both:**
- ✅ yt-dlp functionality
- ✅ Python standard library
- ✅ openpyxl package
- ✅ JSON parsing
- ✅ Regular expressions

**Platform-Specific:**
- ❌ Homebrew (Mac only)
- ❌ `chmod +x` (Mac/Linux only)
- ❌ Forward slash paths work on both, backslash only on Windows

For detailed setup instructions, see:
- `SETUP_MAC.md` - Mac-specific setup
- `SETUP_WINDOWS.md` - Windows-specific setup
