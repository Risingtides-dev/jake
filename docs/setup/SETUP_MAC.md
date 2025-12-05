# Mac Setup Guide for TikTok Tracker Scripts

## Prerequisites

- **macOS 10.14 (Mojave) or later**
- **Administrator access**
- **Internet connection**

---

## Step-by-Step Installation

### Step 1: Install Homebrew (if not already installed)

Homebrew is a package manager for macOS that makes installing yt-dlp easier.

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Verify installation
brew --version
```

### Step 2: Install Python

macOS comes with Python, but we recommend installing the latest version:

```bash
# Check current version
python3 --version

# If older than 3.7, install latest
brew install python@3.11

# Verify
python3 --version
```

### Step 3: Install yt-dlp

```bash
# Install via Homebrew (recommended)
brew install yt-dlp

# Verify installation
yt-dlp --version
```

**Alternative installation methods:**
```bash
# Via pip
pip3 install yt-dlp

# Via curl
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

### Step 4: Install Python Packages

```bash
# Navigate to project directory
cd ~/Desktop/clipper_project_fixed/tracker_data

# Install openpyxl
pip3 install openpyxl

# Verify
python3 -c "import openpyxl; print('OK')"
```

---

## Configuration Changes Required

### 1. Update File Paths (If Needed)

The scripts have hardcoded paths for a specific Mac user. Update if your username is different:

**Find and Replace:**
- **OLD:** `/Users/risingtidesdev/Desktop/clipper_project_fixed/`
- **NEW:** `/Users/YourUsername/Desktop/clipper_project_fixed/`

**Or use your home directory shortcut:**
```python
import os
output_file = os.path.expanduser('~/Desktop/clipper_project_fixed/report.html')
```

**Files to check:**
- `aggregate_sound_analysis.py` (line 184)
- `generate_complete_html.py` (line 601, 626)
- `generate_glass_html.py` (line 553, 568)
- `generate_song_excel.py` (line 315)
- `inhouse_network_scraper.py` (line 1082)

### 2. Make Scripts Executable (Optional)

```bash
chmod +x *.py
```

Then run with:
```bash
./tiktok_analyzer.py --url @radio_kart --limit 10
```

---

## Running the Scripts

### Terminal Usage

```bash
# Single account analysis
python3 tiktok_analyzer.py --url @radio_kart --limit 10

# Generate Excel report
python3 generate_song_excel.py

# Generate HTML report
python3 inhouse_network_scraper.py

# Generate cyberpunk HTML
python3 generate_complete_html.py

# Generate glassmorphism HTML
python3 generate_glass_html.py
```

### Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install openpyxl yt-dlp

# Run scripts
python tiktok_analyzer.py --url @radio_kart --limit 10

# Deactivate when done
deactivate
```

---

## Troubleshooting Mac-Specific Issues

### Issue: "python3: command not found"

**Solution:**
```bash
# Install Python via Homebrew
brew install python@3.11

# Add to PATH if needed
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "yt-dlp: command not found"

**Solution:**
```bash
# Reinstall via Homebrew
brew install yt-dlp

# OR via pip
pip3 install yt-dlp

# Check installation location
which yt-dlp
```

### Issue: "Permission denied"

**Solution:**
```bash
# Make script executable
chmod +x script_name.py

# OR run with sudo (not recommended)
sudo python3 script_name.py
```

### Issue: SSL Certificate errors

**Solution:**
```bash
# Update certificates
/Applications/Python\ 3.*/Install\ Certificates.command

# OR reinstall Python
brew reinstall python@3.11
```

### Issue: "xcrun: error: invalid active developer path"

This happens after macOS updates.

**Solution:**
```bash
xcode-select --install
```

### Issue: M1/M2 Mac (Apple Silicon) compatibility

All dependencies work natively on Apple Silicon. If you encounter issues:

```bash
# Check architecture
uname -m  # Should show "arm64" for M1/M2

# Install Rosetta if needed (for older software)
softwareupdate --install-rosetta
```

---

## File Output Locations

After running scripts, find outputs at:
```
/Users/YourUsername/Desktop/clipper_project_fixed/
├── shared_songs_tiktok_links_oct_nov2025.xlsx
├── sound_usage_complete_report.html
└── inhouse_network_tracker_oct_nov2025.html
```

**Open HTML reports:**
```bash
# Open in default browser
open inhouse_network_tracker_oct_nov2025.html

# Open in specific browser
open -a "Google Chrome" report.html
```

**Open Excel files:**
```bash
open shared_songs_tiktok_links_oct_nov2025.xlsx
```

---

## Mac-Specific Performance Tips

1. **Close browser tabs** before large scrapes (saves RAM)
2. **Use Activity Monitor** to check script progress (CPU usage)
3. **Prevent Mac from sleeping:**
   ```bash
   caffeinate -i python3 inhouse_network_scraper.py
   ```
4. **Run in background:**
   ```bash
   nohup python3 inhouse_network_scraper.py > scrape.log 2>&1 &
   ```

---

## Quick Test

```bash
# Test yt-dlp
yt-dlp --flat-playlist --dump-json --playlist-end 1 "https://www.tiktok.com/@radio_kart"

# Test Python imports
python3 -c "import sys, json, openpyxl; print('All imports OK')"

# Test single account scrape
python3 tiktok_analyzer.py --url @radio_kart --limit 3

# Check output
ls -lh *.html *.xlsx
```

---

## Using Terminal Shortcuts

### Create an alias for quick access

Add to `~/.zshrc` (or `~/.bash_profile` for older macOS):

```bash
# Add these lines
alias tracker='cd ~/Desktop/clipper_project_fixed/tracker_data'
alias scrape='python3 inhouse_network_scraper.py'
alias analyze='python3 tiktok_analyzer.py'

# Reload shell
source ~/.zshrc
```

Now you can:
```bash
tracker  # Jump to directory
scrape   # Run network scraper
analyze --url @radio_kart --limit 10  # Quick analysis
```

---

## Summary Checklist

- [ ] Homebrew installed
- [ ] Python 3.7+ installed (`python3 --version`)
- [ ] yt-dlp installed (`yt-dlp --version`)
- [ ] openpyxl installed (`pip3 install openpyxl`)
- [ ] File paths updated (if username different)
- [ ] Scripts executable (`chmod +x *.py`)
- [ ] Test run successful
- [ ] Output directory accessible

---

## Updating Dependencies

Keep dependencies current for best compatibility:

```bash
# Update Homebrew
brew update

# Update yt-dlp
brew upgrade yt-dlp

# Update Python packages
pip3 install --upgrade openpyxl yt-dlp

# Check versions
yt-dlp --version
python3 --version
pip3 list | grep openpyxl
```

---

## Need Help?

Common Mac errors:
- **"Operation not permitted"** → Check System Preferences > Security & Privacy
- **"Command not found"** → Check PATH or reinstall via Homebrew
- **"No module named X"** → `pip3 install X`
- **Slow performance** → Close other apps, use `caffeinate` to prevent sleep

For detailed script documentation, see `TRACKER_DOCUMENTATION.md`
