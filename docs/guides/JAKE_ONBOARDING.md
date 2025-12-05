# Warner Tracker - Jake's Onboarding Guide

Welcome Jake! This guide will help you get set up to work on the Warner Tracker project, generate reports, and deploy them to GitHub Pages.

## Table of Contents
1. [Getting GitHub Access](#1-getting-github-access)
2. [Installing Development Tools](#2-installing-development-tools)
3. [Setting Up the Project](#3-setting-up-the-project)
4. [Generating CSVs and Reports](#4-generating-csvs-and-reports)
5. [Git Workflow & Branching](#5-git-workflow--branching)
6. [Deploying to GitHub Pages](#6-deploying-to-github-pages)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Getting GitHub Access

### Step 1.1: Get Added to the Repository
Ask your project lead to:
- Add you as a collaborator to the GitHub repository
- Grant you "Write" or "Maintain" access (needed to push code and deploy)

### Step 1.2: Set Up Git Locally
```bash
# Configure your git identity (use your work email)
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# Set up authentication with GitHub (recommended: SSH key)
# Follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

---

## 2. Installing Development Tools

### Step 2.1: Install Python
1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Verify installation:
   ```bash
   python3 --version
   ```

### Step 2.2: Install Cursor IDE
1. Go to [cursor.com](https://cursor.com)
2. Download and install Cursor for your operating system
3. Launch Cursor

### Step 2.3: Set Up Claude Code in Cursor

#### Install Claude Code Extension
1. Open Cursor
2. Click the Extensions icon (sidebar, looks like squares)
3. Search for "Claude Code"
4. Click Install on the official Claude Code extension by Anthropic

#### Configure Claude API Key
1. Get your Claude API key from [console.anthropic.com](https://console.anthropic.com)
2. In Cursor, open Command Palette (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows)
3. Type "Claude Code: Set API Key"
4. Paste your API key

#### Verify Claude Code Works
1. Open Command Palette again
2. Type "Claude Code: Open"
3. Try asking Claude: "Hello, can you help me understand this project?"
4. If Claude responds, you're all set!

---

## 3. Setting Up the Project

### Step 3.1: Clone the Repository
```bash
# Navigate to where you want the project
cd ~/Desktop  # or wherever you prefer

# Clone the repo (replace with actual repo URL)
git clone git@github.com:yourusername/warnertracker.git
cd warnertracker
```

### Step 3.2: Install Dependencies
```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 3.3: Install YT-DLP (TikTok Scraper)
```bash
# YT-DLP is used to scrape TikTok data without requiring API keys
# Install via pip (should already be in requirements.txt)
pip install yt-dlp

# Or install globally if needed
# On Mac/Linux:
pip3 install yt-dlp

# On Windows:
pip install yt-dlp

# Verify installation
yt-dlp --version
```

**Note**: This project uses YT-DLP to scrape TikTok publicly available data. No API keys or authentication tokens are required!

### Step 3.4: Open in Cursor
```bash
# From the project directory
cursor .
```

---

## 4. Generating CSVs and Reports

### Understanding the Workflow
The project tracks TikTok data across multiple campaigns and generates reports:
1. **Scrape Data** → Uses YT-DLP to fetch TikTok video metadata (views, likes, sounds, etc.)
2. **Generate CSVs** → Organized data files
3. **Create Reports** → HTML reports with visualizations
4. **Deploy** → Publish to GitHub Pages

**How YT-DLP Works**: YT-DLP scrapes publicly available TikTok data by analyzing video pages and extracting metadata. It doesn't require authentication or API keys, making it simple to use and maintain.

### Step 4.1: Run a Full Campaign Scrape
```bash
# Make sure you're in the project directory with venv activated
source venv/bin/activate  # if not already active

# Run a specific campaign scraper
./run_warner_scrape.sh    # Warner Music campaign
./run_inhouse_scrape.sh   # In-house campaign
./run_plgrnd_scrape.sh    # Playground campaign

# Or run all campaigns at once
./run_all_campaigns.sh
```

### Step 4.2: Generate CSV Reports
```bash
# Generate CSVs from scraped data
python generate_song_csvs.py

# This creates CSV files in the output directory
# Files will be named like: warner_music_YYYY-MM-DD.csv
```

### Step 4.3: Create HTML Reports
```bash
# Generate HTML report from CSV
python generate_csv_report.py

# Or use the convenience script
./generate_report.sh

# Reports are saved in the reports/ directory
```

### Step 4.4: Preview Reports Locally
```bash
# Start the web UI to preview reports
python web_ui.py

# Open your browser to: http://localhost:5000
```

### Quick Reference Commands
```bash
# Full workflow in one go:
./run_all_campaigns.sh && python generate_song_csvs.py && ./generate_report.sh
```

---

## 5. Git Workflow & Branching

### Basic Git Workflow

#### Step 5.1: Always Start with Fresh Code
```bash
# Make sure you're on main branch
git checkout main

# Pull latest changes
git pull origin main
```

#### Step 5.2: Create a Feature Branch
```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Examples:
git checkout -b report/weekly-update-2025-01-15
git checkout -b fix/csv-generation-bug
```

#### Step 5.3: Make Your Changes
```bash
# After generating reports or making changes, check status
git status

# Add files you want to commit
git add reports/
git add *.csv

# Or add everything
git add .

# Commit with a clear message
git commit -m "Add weekly Warner Music report for 2025-01-15"
```

#### Step 5.4: Push Your Branch
```bash
# Push your branch to GitHub
git push origin feature/your-feature-name
```

#### Step 5.5: Create a Pull Request
1. Go to the GitHub repository in your browser
2. You'll see a banner: "Compare & pull request" - click it
3. Add a description of your changes
4. Request review from your project lead
5. Wait for approval, then merge

### Quick Commands Cheat Sheet
```bash
# See what branch you're on
git branch

# Switch branches
git checkout branch-name

# See what changed
git diff

# Undo changes (before commit)
git checkout -- filename

# See commit history
git log --oneline
```

---

## 6. Deploying to GitHub Pages

### Option 1: Using the Deploy Script (Recommended)
```bash
# This script handles everything automatically
./deploy_github_pages.sh

# What it does:
# 1. Generates latest reports
# 2. Commits them to gh-pages branch
# 3. Pushes to GitHub
# 4. Reports are live in ~1 minute
```

### Option 2: Manual Deployment
```bash
# Generate reports first
python generate_csv_report.py

# Switch to gh-pages branch
git checkout gh-pages

# Copy reports to root (if needed)
cp -r reports/* .

# Commit and push
git add .
git commit -m "Update reports - $(date +%Y-%m-%d)"
git push origin gh-pages

# Switch back to main
git checkout main
```

### Viewing Your Deployed Reports
After deployment, your reports will be available at:
```
https://yourusername.github.io/warnertracker/
```

(Replace `yourusername` with the actual GitHub username/org)

---

## 7. Troubleshooting

### Python Environment Issues
```bash
# If packages aren't found
pip install -r requirements.txt

# If wrong Python version
python3 --version  # should be 3.8+

# If venv issues, recreate it
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Git Issues
```bash
# If you can't push (permission denied)
# You need to be added as a collaborator

# If merge conflicts
git status  # see what's conflicted
# Edit files to resolve conflicts
git add .
git commit -m "Resolve merge conflicts"

# If you're lost
git checkout main  # go back to main
git pull  # get latest
# Start over with a new branch
```

### Claude Code Issues
- **Claude not responding**: Check API key in Cursor settings
- **Rate limits**: Wait a few minutes, then try again
- **Extension not found**: Reinstall from Cursor marketplace

### Report Generation Issues
```bash
# If CSV generation fails
# Check that scrapers ran successfully
ls -la data/  # should see JSON files

# If reports look wrong
# Check the CSV files first
head -20 output/latest_report.csv

# Clear cache and regenerate
rm -rf output/*.csv
python generate_song_csvs.py
```

### YT-DLP Issues
```bash
# If YT-DLP fails to scrape
# Update to latest version (TikTok changes frequently)
pip install --upgrade yt-dlp

# If you get rate-limited
# Wait 10-15 minutes before retrying
# TikTok may temporarily block excessive requests

# Test YT-DLP directly on a single video
yt-dlp --dump-json "https://www.tiktok.com/@username/video/123456789"

# If videos fail to load
# Check your internet connection
# Try using a different network or VPN if blocked
```

---

## Common Tasks Quick Reference

### Daily Report Generation
```bash
# 1. Pull latest code
git checkout main && git pull

# 2. Create dated branch
git checkout -b report/$(date +%Y-%m-%d)

# 3. Run scraper and generate
./run_all_campaigns.sh
python generate_song_csvs.py
./generate_report.sh

# 4. Commit and push
git add .
git commit -m "Daily report $(date +%Y-%m-%d)"
git push origin report/$(date +%Y-%m-%d)

# 5. Deploy to GitHub Pages
./deploy_github_pages.sh
```

### Working with Claude Code
```bash
# Open Claude Code panel
Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
Type: "Claude Code: Open"

# Useful Claude prompts:
"Help me understand how the CSV generation works"
"Debug this error in generate_song_csvs.py"
"Create a new report template based on the existing one"
"Explain the difference between these two functions"
```

---

## Getting Help

1. **Ask Claude Code**: Open Claude in Cursor and ask questions about the code
2. **Check existing docs**: Look in `README.md`, `DEPLOY.md`, etc.
3. **Ask your project lead**: They know the project best
4. **GitHub Issues**: Check if someone else had the same problem

---

## Next Steps

1. ✅ Complete all installation steps above
2. ✅ Run your first scraper and generate a test report
3. ✅ Create a test branch and practice the git workflow
4. ✅ Deploy a test report to GitHub Pages
5. ✅ Try using Claude Code to explore the codebase
6. ✅ Schedule a sync with your project lead to review

Welcome to the team, Jake! 🚀
