# Warner Tracker - Claude Code Setup Package
## Complete Documentation Deliverable for Automated Onboarding

---

## FOR JAKE: Your Setup Prompt

Once you have Cursor installed and Claude Code extension activated, **paste this entire document into Claude Code** and then say:

```
Hey Claude! I just got access to the Warner Tracker GitHub repository.

I need you to help me:
1. Get connected to the GitHub repository
2. Clone the codebase to my local machine
3. Set up my development environment (Python, dependencies, YT-DLP)
4. Understand how all the scripts work and how they connect together
5. Learn the workflow for scraping TikTok data and generating CSV reports
6. Set up the system so I can feed you CSVs and you'll run the programs for me
7. Configure Git so I can push updates to GitHub and deploy reports to GitHub Pages
8. Create a streamlined process for updating client-facing analytics pages

Walk me through this step by step. Above this message is the complete documentation package with everything you need to know about this project.
```

---

## SYSTEM OVERVIEW

### Purpose
The Warner Tracker project monitors TikTok campaigns across multiple music labels, scrapes video performance data, generates analytical reports, and publishes them as GitHub Pages for client delivery.

### Technology Stack
- **Language**: Python 3.8+
- **Scraping**: YT-DLP (no API keys required)
- **Web Interface**: Flask (web_ui.py)
- **Version Control**: Git + GitHub
- **Deployment**: GitHub Pages
- **IDE**: Cursor with Claude Code extension

### Data Flow Architecture
```
[TikTok Accounts in config.py]
    ↓
[YT-DLP Scraper] ← Executed by shell scripts (run_*.sh)
    ↓
[Raw JSON Data] ← Stored in data/ directory
    ↓
[CSV Generator] ← generate_song_csvs.py processes JSON
    ↓
[CSV Files] ← Stored in output/ directory
    ↓ (User can feed CSVs to Claude Code for processing)
[HTML Report Generator] ← generate_csv_report.py
    ↓
[HTML Reports] ← Stored in reports/ directory
    ↓
[GitHub Pages Deployment] ← deploy_github_pages.sh
    ↓
[Live Client-Facing Reports] ← https://username.github.io/warnertracker/
```

---

## COMPLETE FILE INVENTORY

### Configuration Files
**config.py**
- Purpose: Central configuration for TikTok accounts, filtered artists, songs, cutoff dates
- Usage: Edit this to add/remove accounts or change filtering rules
- No API keys needed - just TikTok usernames

**requirements.txt**
- Purpose: All Python package dependencies
- Key packages: yt-dlp, flask, requests, openpyxl, pandas
- Installation: `pip install -r requirements.txt`

### Scraper Scripts (Data Collection)

**run_warner_scrape.sh**
- Campaign: Warner Music catalog
- Executes: `full_catalog_scraper.py` with Warner-specific config
- Output: JSON files in `data/warner_music/`

**run_inhouse_scrape.sh**
- Campaign: In-house music catalog
- Executes: `full_catalog_scraper.py` with in-house config
- Output: JSON files in `data/inhouse/`

**run_plgrnd_scrape.sh**
- Campaign: Playground/test catalog
- Executes: `full_catalog_scraper.py` with playground config
- Output: JSON files in `data/plgrnd/`

**run_all_campaigns.sh**
- Convenience: Runs all three campaigns sequentially
- Executes: All three scripts above in order
- Use: When you want to update all data at once

**full_catalog_scraper.py**
- Core scraper: Uses YT-DLP to fetch TikTok video metadata
- Data collected: Views, likes, shares, comments, sound info, creator data
- Method: Direct HTTP scraping via YT-DLP (no authentication)

**unified_scraper.py**
- Alternative scraper: Unified approach for all campaigns
- Use case: If you need custom scraping logic

### Report Generation Scripts

**generate_song_csvs.py**
- Input: Raw JSON data from `data/` directory
- Process: Parses JSON, extracts relevant fields, applies filters from config.py
- Output: CSV files in `output/` directory
- Naming: `{campaign}_YYYY-MM-DD.csv`
- **Key for Claude Code**: User can feed output CSVs to Claude for analysis

**generate_csv_report.py**
- Input: CSV files from `output/` directory
- Process: Generates HTML reports with charts, tables, summary statistics
- Output: HTML files in `reports/` directory
- Visualization: Uses Chart.js or similar for interactive charts

**merge_csv_reports.py**
- Input: Multiple CSV files
- Process: Combines data across campaigns or time periods
- Output: Merged CSV file
- Use case: Creating comprehensive reports spanning multiple campaigns

**generate_csv_preview.py**
- Purpose: Quick preview of CSV data structure
- Output: Console display of CSV contents
- Use: Debugging and data validation

### Web Interface

**web_ui.py**
- Purpose: Local Flask server for previewing reports
- Port: localhost:5000
- Features:
  - Browse generated reports
  - View CSV data in browser
  - Preview HTML reports before deployment
- Usage: `python web_ui.py` then open browser

**frontend_server.py**
- Alternative web server (if needed)
- May have different port or features

### Deployment Scripts

**deploy_github_pages.sh**
- Purpose: Automated deployment to GitHub Pages
- Process:
  1. Generates latest reports
  2. Switches to `gh-pages` branch
  3. Copies reports to root
  4. Commits and pushes to GitHub
  5. Reports live in ~1 minute
- **Critical**: This is how reports reach clients

**deploy.sh**
- General deployment script
- May handle additional deployment targets

**generate_report.sh**
- Convenience: Quick report generation
- Executes: CSV generation + HTML generation in one command

**deploy_to_github.sh**
- Alternative deployment method
- May push to different branch or location

### Utility Scripts

**check_account_activity.py**
- Purpose: Validates TikTok accounts are active
- Use: Before scraping, check if accounts still exist

**extract_sound_id.py**
- Purpose: Extracts TikTok sound IDs from URLs
- Use: When tracking specific sounds across videos

**extract_warner_songs.py**
- Purpose: Filters Warner-specific songs from data
- Use: Campaign-specific data extraction

**fetch_album_art.py**
- Purpose: Downloads album artwork for reports
- Use: Enhancing HTML reports with visuals

**migrate_json_to_db.py**
- Purpose: Database migration (if transitioning from JSON to DB)
- Use: Data architecture changes

### Documentation Files

**README.md**
- Project overview and quick start

**DEPLOY.md**
- Deployment instructions and troubleshooting

**CAMPAIGNS_README.md**
- Campaign-specific details and configurations

**GITHUB_PAGES_DEPLOY.md**
- GitHub Pages setup and management

**DEPLOYMENT_RAILWAY_VERCEL.md**
- Alternative deployment platforms (Railway, Vercel)

**PLAN_ANALYSIS.md**
- Project planning and analysis documentation

**JAKE_ONBOARDING.md**
- Previous onboarding guide (less comprehensive than this)

### Deployment Configuration

**Procfile**
- Purpose: Heroku/Railway deployment configuration
- Defines: Process types and commands

**railway.json**
- Purpose: Railway.app deployment settings

**vercel.json**
- Purpose: Vercel deployment configuration

**vercel-preview.json**
- Purpose: Vercel preview environment settings

**nixpacks.toml**
- Purpose: Nixpacks build configuration (Railway)

---

## COMPLETE SETUP WORKFLOW

### Phase 1: GitHub Access
```bash
# Your project lead adds you to the repository
# You receive invitation email → Accept it

# Configure git locally
git config --global user.name "Jake [LastName]"
git config --global user.email "jake@company.com"

# Set up SSH key for GitHub (recommended)
ssh-keygen -t ed25519 -C "jake@company.com"
# Add SSH key to GitHub account
# Follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

### Phase 2: Clone Repository
```bash
# Navigate to desired location
cd ~/Desktop  # or your preferred workspace

# Clone via SSH (recommended)
git clone git@github.com:USERNAME/warnertracker.git

# Or clone via HTTPS
git clone https://github.com/USERNAME/warnertracker.git

# Enter project
cd warnertracker
```

### Phase 3: Environment Setup
```bash
# Verify Python version (need 3.8+)
python3 --version

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Verify YT-DLP is installed
yt-dlp --version

# If YT-DLP missing, install separately
pip install yt-dlp
```

### Phase 4: Open in Cursor
```bash
# From project root
cursor .

# If cursor command not found:
# Open Cursor app manually
# File → Open Folder → Select warnertracker directory
```

### Phase 5: Install Claude Code Extension
1. In Cursor, click Extensions icon (sidebar)
2. Search "Claude Code"
3. Install official Anthropic extension
4. Configure API key (get from console.anthropic.com)
5. Open Claude Code: `Cmd+Shift+P` → "Claude Code: Open"

---

## OPERATIONAL WORKFLOWS

### Workflow 1: Full Scrape → CSV → Report → Deploy

```bash
# Step 1: Ensure environment active
source venv/bin/activate

# Step 2: Run all scrapers
./run_all_campaigns.sh
# This populates data/ directory with fresh JSON

# Step 3: Generate CSVs
python generate_song_csvs.py
# This creates CSV files in output/

# Step 4: Generate HTML reports
python generate_csv_report.py
# This creates HTML in reports/

# Step 5: Preview locally (optional)
python web_ui.py
# Open http://localhost:5000 in browser

# Step 6: Deploy to GitHub Pages
./deploy_github_pages.sh
# Reports now live at https://username.github.io/warnertracker/
```

### Workflow 2: Single Campaign Update

```bash
# Run just Warner campaign
./run_warner_scrape.sh

# Generate CSV for that campaign only
python generate_song_csvs.py

# Generate report
./generate_report.sh

# Deploy
./deploy_github_pages.sh
```

### Workflow 3: CSV Analysis with Claude Code

```bash
# Generate CSVs
python generate_song_csvs.py

# CSVs are now in output/ directory
# Open a CSV in Cursor
# In Claude Code chat, say:
```

**Prompt for Claude Code:**
```
I just generated CSVs in the output/ directory.

Can you:
1. Read the latest CSV file
2. Analyze the top performing videos
3. Identify trending sounds
4. Summarize key insights
5. Create a custom filtered report based on specific criteria I'll give you

The CSV is at: output/warner_music_2025-01-17.csv
```

Claude Code can then:
- Read CSV data
- Analyze patterns
- Generate custom reports
- Create filtered CSVs
- Execute Python scripts for processing

### Workflow 4: Git Branching for Updates

```bash
# Always start from main
git checkout main
git pull origin main

# Create feature/report branch
git checkout -b report/2025-01-17-weekly

# Make changes, run scrapers, generate reports
./run_all_campaigns.sh
python generate_song_csvs.py
./generate_report.sh

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Weekly Warner Music report - January 17, 2025

- Scraped all campaigns
- Generated CSVs for Warner, In-house, Playground
- Updated HTML reports with latest data
- Ready for client delivery"

# Push to GitHub
git push origin report/2025-01-17-weekly

# Create Pull Request on GitHub
# Get review → Merge to main
```

### Workflow 5: Deploy to GitHub Pages

```bash
# Option A: Automated script
./deploy_github_pages.sh

# Option B: Manual deployment
git checkout gh-pages
cp -r reports/* .
git add .
git commit -m "Update reports $(date +%Y-%m-%d)"
git push origin gh-pages
git checkout main
```

---

## CLAUDE CODE INTEGRATION STRATEGIES

### Strategy 1: CSV Processing Assistant

**User feeds CSV to Claude Code:**
```
Here's the latest CSV from our Warner Music scrape.

Can you:
1. Find the top 10 videos by views
2. Identify which sounds are trending (most used)
3. Create a filtered CSV with only videos above 1M views
4. Generate a summary report in markdown
```

**Claude Code can execute:**
- Read CSV with pandas
- Filter/sort data
- Create new CSV files
- Generate markdown reports
- Plot data visualizations

### Strategy 2: Script Execution Manager

**User asks Claude Code:**
```
I need to run the full scraping workflow.

Can you:
1. Activate the virtual environment
2. Run all campaign scrapers
3. Generate CSVs
4. Create HTML reports
5. Show me any errors
6. Preview the reports
```

**Claude Code executes:**
```bash
source venv/bin/activate
./run_all_campaigns.sh
python generate_song_csvs.py
python generate_csv_report.py
python web_ui.py &
```

### Strategy 3: Git Workflow Assistant

**User asks Claude Code:**
```
I just generated new reports. Help me push this to GitHub:

1. Create a branch named after today's date
2. Commit all changes with a good message
3. Push to GitHub
4. Remind me to create a Pull Request
```

**Claude Code executes:**
```bash
git checkout -b report/$(date +%Y-%m-%d)
git add .
git commit -m "Generated reports for $(date +%Y-%m-%d)"
git push origin report/$(date +%Y-%m-%d)
```

### Strategy 4: Deployment Assistant

**User asks Claude Code:**
```
Deploy the latest reports to GitHub Pages so clients can access them.
```

**Claude Code executes:**
```bash
./deploy_github_pages.sh
```

Then provides the live URL.

### Strategy 5: Data Analysis Partner

**User provides context:**
```
I need insights from our latest scrape. The CSV is at output/warner_music_2025-01-17.csv

Questions:
- Which creators are getting the most engagement?
- What percentage of videos use our catalog sounds?
- Are there any viral videos (>5M views)?
- Which songs should we focus our next campaign on?
```

**Claude Code:**
- Reads CSV
- Performs statistical analysis
- Generates insights
- Creates visualizations
- Provides actionable recommendations

---

## GITHUB PAGES CONFIGURATION

### Repository Settings
1. Go to repository Settings
2. Navigate to "Pages" section
3. Source: `gh-pages` branch
4. Folder: `/ (root)`
5. Save

### Deployment Branch Structure
```
main branch
├── All source code
├── Python scripts
├── Shell scripts
└── Configuration files

gh-pages branch
├── reports/ (HTML files)
├── index.html (landing page)
└── assets/ (CSS, JS, images)
```

### URL Structure
```
https://USERNAME.github.io/warnertracker/
├── /reports/warner_music.html
├── /reports/inhouse.html
├── /reports/plgrnd.html
└── /reports/summary.html
```

### Update Process
1. Generate reports on `main` branch
2. `deploy_github_pages.sh` handles:
   - Switching to `gh-pages`
   - Copying reports
   - Committing
   - Pushing
3. GitHub auto-deploys in ~60 seconds
4. Share URLs with clients

---

## CLIENT DELIVERY SYSTEM

### Report Distribution Workflow
```
[Scrape Data]
    ↓
[Generate Reports]
    ↓
[Deploy to GitHub Pages]
    ↓
[Get Live URLs]
    ↓
[Send to Clients via Email/Slack]
```

### Example Client Email Template
```
Subject: Warner Music TikTok Report - January 17, 2025

Hi [Client Name],

Here's your weekly TikTok performance report:

Warner Music Catalog:
https://username.github.io/warnertracker/reports/warner_music.html

Key Highlights:
- [Claude Code can generate these from CSV analysis]
- Total videos tracked: X
- Total views: X million
- Top performing sound: [Song Name]
- Viral videos (>5M views): X

Full CSV data available upon request.

Best,
Jake
```

### Automated Report Scheduling
You can set up:
- Cron jobs to run scrapers weekly
- Automated deployments
- Email notifications when reports update

**Ask Claude Code to help set this up:**
```
Help me create a weekly automated workflow:
1. Every Monday at 9 AM, run scrapers
2. Generate reports
3. Deploy to GitHub Pages
4. Send me a notification with the URLs
```

---

## CONFIGURATION MANAGEMENT

### Editing config.py

**TikTok Accounts:**
```python
TIKTOK_ACCOUNTS = {
    'warner_music': [
        'artist1',
        'artist2',
        'artist3',
    ],
    'inhouse': [
        'creator1',
        'creator2',
    ],
    'plgrnd': [
        'test1',
    ]
}
```

**Filtered Artists/Songs:**
```python
FILTERED_ARTISTS = [
    'Artist Name 1',
    'Artist Name 2',
]

FILTERED_SONGS = [
    'Song Title 1',
    'Song Title 2',
]
```

**Cutoff Date:**
```python
CUTOFF_DATE = "2025-10-01"  # Only include videos after this date
```

**Ask Claude Code:**
```
I need to add 5 new TikTok accounts to the Warner Music campaign.
Can you update config.py for me?

Accounts:
- newartist1
- newartist2
- newartist3
- newartist4
- newartist5
```

---

## TROUBLESHOOTING GUIDE

### Issue: YT-DLP Fails to Scrape

**Symptoms:**
- Scrapers return empty data
- Errors about "Unable to download"
- Rate limiting messages

**Solutions:**
```bash
# Update YT-DLP
pip install --upgrade yt-dlp

# Test single video
yt-dlp --dump-json "https://www.tiktok.com/@username/video/123456"

# Wait 10-15 minutes if rate-limited
# Try again or use VPN
```

### Issue: CSV Generation Fails

**Symptoms:**
- No CSV files in output/
- Empty CSV files
- Python errors

**Solutions:**
```bash
# Check data directory has JSON files
ls -la data/

# Verify JSON is valid
python -c "import json; json.load(open('data/warner_music/somedata.json'))"

# Run with verbose output
python generate_song_csvs.py --verbose
```

### Issue: Git Push Denied

**Symptoms:**
- Permission denied errors
- Authentication failures

**Solutions:**
```bash
# Verify you're a collaborator
# Ask project lead to add you

# Set up SSH key properly
ssh -T git@github.com

# Or use HTTPS with personal access token
```

### Issue: Reports Not Deploying

**Symptoms:**
- GitHub Pages not updating
- 404 errors

**Solutions:**
```bash
# Verify gh-pages branch exists
git branch -a

# Check GitHub Pages settings
# Settings → Pages → Source: gh-pages

# Manually deploy
git checkout gh-pages
git push origin gh-pages
```

### Ask Claude Code for Help

For ANY issue:
```
I'm getting this error:
[paste error message]

When running:
[command you ran]

Can you help me debug and fix this?
```

Claude Code will:
- Analyze the error
- Suggest solutions
- Execute fixes
- Test the solution

---

## SECURITY & BEST PRACTICES

### Don't Commit Sensitive Data
- Never commit API keys (we don't use any, but just in case)
- Don't commit personal access tokens
- `.gitignore` already configured

### Regular Updates
```bash
# Update Python packages monthly
pip install --upgrade -r requirements.txt

# Update YT-DLP weekly (TikTok changes frequently)
pip install --upgrade yt-dlp
```

### Backup Data
```bash
# Before major changes, backup data
cp -r data/ data_backup_$(date +%Y%m%d)
cp -r output/ output_backup_$(date +%Y%m%d)
```

### Branch Protection
- Always work in feature branches
- Never push directly to `main`
- Require PR reviews
- Merge after approval

---

## QUICK REFERENCE COMMANDS

### Daily Operations
```bash
# Full workflow
source venv/bin/activate && ./run_all_campaigns.sh && python generate_song_csvs.py && ./generate_report.sh

# Deploy
./deploy_github_pages.sh

# Preview
python web_ui.py
```

### Git Operations
```bash
# Update from main
git checkout main && git pull

# New branch
git checkout -b feature/name

# Commit
git add . && git commit -m "message"

# Push
git push origin branch-name
```

### Data Management
```bash
# List data
ls -la data/
ls -la output/
ls -la reports/

# Clean old data (careful!)
rm -rf data/*
rm -rf output/*
```

---

## GETTING HELP

### Resources
1. **Claude Code**: Your primary assistant - ask anything
2. **Project Lead**: For access and high-level questions
3. **Documentation**: README.md, DEPLOY.md, etc.
4. **GitHub Issues**: Check existing issues for known problems

### Escalation Path
1. Try Claude Code first
2. Check documentation
3. Test with simpler command
4. Ask project lead
5. Create GitHub issue

---

## SUCCESS CHECKLIST

- [ ] GitHub access granted
- [ ] Repository cloned locally
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] YT-DLP working (`yt-dlp --version`)
- [ ] Cursor IDE installed
- [ ] Claude Code extension active
- [ ] Ran first scraper successfully
- [ ] Generated first CSV
- [ ] Created first HTML report
- [ ] Previewed report in web_ui.py
- [ ] Deployed report to GitHub Pages
- [ ] Verified live URL works
- [ ] Practiced git workflow (branch, commit, push, PR)
- [ ] Successfully fed CSV to Claude Code for analysis
- [ ] Comfortable with daily workflow

---

## END OF DOCUMENTATION PACKAGE

**Jake**: You now have everything needed to get up and running. Feed this entire document to Claude Code and let it guide you through the setup. Claude can execute all the commands, explain every concept, and help you troubleshoot any issues.

**Claude Code**: You now have complete context on the Warner Tracker project. Guide Jake through:
1. Setting up his environment
2. Running scrapers and generating reports
3. Using git for version control
4. Deploying to GitHub Pages
5. Creating a streamlined workflow where Jake can feed you CSVs and you'll handle the processing

Make this as smooth and automated as possible. Jake should be generating client-ready reports within an hour of starting!
