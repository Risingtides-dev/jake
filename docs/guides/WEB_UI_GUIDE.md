# Warner Sound Tracker - Web UI Guide

## Overview

The Warner Sound Tracker Web UI provides an interactive workflow for managing TikTok scraping, manual song filtering, and analytics report generation. This eliminates the need to manually edit code or configuration files.

## Quick Start

### 1. Start the Web UI

```bash
./start_ui.sh
```

Or manually:

```bash
source venv/bin/activate
python3 web_ui.py
```

### 2. Access the Interface

Open your browser to: **http://localhost:5000**

## Workflow Steps

### Step 1: Settings

Configure your scraping parameters:

- **Start Date**: Beginning date for video scraping (default: October 14, 2025)
- **End Date**: End date for video scraping (default: today)
- **Scrape Limit**: Maximum videos to scrape per account (default: 1000)

Click **Save Settings** to persist your configuration.

### Step 2: Scrape

1. Click **Start Scraping** to begin scraping all configured TikTok accounts
2. Monitor real-time status for each account:
   - ✅ **Completed**: Scraping finished successfully
   - ⏳ **Running**: Currently scraping
   - ❌ **Error**: Scraping failed (error message displayed)
   - ⏰ **Timeout**: Scraping took too long (>10 minutes)

3. View video counts for each account as scraping progresses

**What happens during scraping:**
- All TikTok accounts from `config.py` are scraped in parallel
- ALL videos and sounds are captured (no filtering at this stage)
- Videos are filtered by date range only
- Raw data is saved to `output/scraped_data.json`

### Step 3: Edit

Manual song filtering interface - this is where you control what gets included in reports.

1. Click **Load Scraped Data** to view all scraped songs
2. Review the list of songs:
   - Songs are sorted by video count (most used first)
   - Each song shows: video count, total views, total likes
   - All songs are **selected by default** (green background)

3. **Filter songs manually:**
   - Click any song to toggle selection
   - Selected (green) = KEEP in report
   - Deselected (red) = REMOVE from report
   - Click the checkbox or anywhere on the song card

4. Review the selection:
   - Top of the list shows: Total songs, Selected count
   - Scroll through and remove non-Warner songs

5. Click **Apply Filter** when done
   - Filtered data is saved to `output/filtered_data.json`
   - You'll see a confirmation with kept/removed counts

**Tips for filtering:**
- Look for artist names that aren't Warner Music Group
- Remove songs like "Goldford", "Monrovia", or other non-Warner artists
- Keep only legitimate Warner songs from the CSV
- You can reload and re-filter as many times as needed

### Step 4: Report

Generate analytics and view the final report.

1. Click **Generate Report** to create analytics from filtered data
2. View the report:
   - Summary stats: total videos, accounts, generation time
   - Per-account breakdown
   - Top 5 sounds for each account
   - Engagement metrics: views, likes, comments, shares

3. Click **View Report** to scroll to the report section

**Report includes:**
- Total videos across all accounts
- Number of accounts tracked
- Per-account statistics
- Sound usage rankings
- Engagement rates
- Clickable video counts and metrics

## Data Files

All data is saved to the `output/` directory:

| File | Purpose |
|------|---------|
| `scraped_data.json` | Raw scraped data from TikTok |
| `filtered_data.json` | Manually filtered data (Warner songs only) |
| `settings.json` | Saved scraping configuration |

## API Endpoints

The web UI provides a REST API for programmatic access:

### Settings
- `GET /api/settings` - Get current settings
- `POST /api/settings` - Update settings

### Warner Songs
- `GET /api/warner-songs` - Get Warner song list from CSV

### Scraping
- `POST /api/scrape/start` - Start scraping session
- `GET /api/scrape/status` - Get scraping status

### Data Management
- `GET /api/scraped-data` - Get scraped data grouped by song
- `POST /api/filter-songs` - Apply manual song filtering
- `POST /api/report/generate` - Generate analytics report

## Configuration

### Accounts

Edit `config.py` to add/remove TikTok accounts:

```python
ACCOUNTS = [
    '@beaujenkins',
    '@codyjames6.7',
    '@coffeesentiments',
    '@gavin.wilder1',
    '@smoked.999',
]
```

### Warner Songs CSV

The system loads Warner songs from `data/warner_songs_clean.csv`:

```csv
sound_key,song,artist,song_link
Hold On - Wesko,Hold On,Wesko,https://...
Pink Skies - Zach Bryan,Pink Skies,Zach Bryan,https://...
```

**CSV Format:**
- `sound_key`: Song title + artist in "Song - Artist" format
- `song`: Song title only
- `artist`: Artist name only
- `song_link`: TikTok music page URL

## Troubleshooting

### Scraping Issues

**Timeout errors:**
- Individual accounts timeout after 10 minutes
- Reduce the scrape limit or scrape date range
- Check your internet connection

**No videos found:**
- Verify date range (start/end dates)
- Check that accounts are public and have videos
- Ensure yt-dlp is installed: `brew install yt-dlp`

**Account errors:**
- Verify account usernames include @ prefix
- Check that accounts exist and are public
- Review error message in scrape status

### Filtering Issues

**No scraped data available:**
- Run a scrape first (Step 2)
- Check `output/scraped_data.json` exists
- Verify scraping completed successfully

**Can't load filtered data:**
- Run the Edit step first (Step 3)
- Apply filter at least once
- Check `output/filtered_data.json` exists

### Report Issues

**No filtered data available:**
- Complete Steps 1-3 first
- Ensure you clicked "Apply Filter" in Step 3
- Check that some songs were selected (not all removed)

## Best Practices

### Date Range Selection
- Use October 14, 2025 as start date (configurable)
- Set end date to "today" for current data
- Adjust range based on analysis needs

### Manual Filtering
- Review ALL songs before filtering
- Look for non-Warner artists
- Double-check artist names against Warner CSV
- Keep the selection focused on legitimate Warner songs

### Scraping Frequency
- Don't scrape too frequently (rate limiting)
- Wait at least 1 hour between full scrapes
- Use incremental scraping for updates (future feature)

### Data Management
- Backup scraped data before re-filtering
- Keep multiple filtered datasets for comparison
- Export reports before regenerating

## Advanced Usage

### Programmatic Access

Use the REST API for automation:

```python
import requests

# Start scraping
response = requests.post('http://localhost:5000/api/scrape/start')
session_id = response.json()['session_id']

# Check status
while True:
    status = requests.get('http://localhost:5000/api/scrape/status').json()
    if status['session']['status'] == 'completed':
        break
    time.sleep(5)

# Get scraped data
data = requests.get('http://localhost:5000/api/scraped-data').json()

# Filter songs (keep only these)
kept_songs = ['Hold On - Wesko', 'Pink Skies - Zach Bryan']
requests.post('http://localhost:5000/api/filter-songs',
              json={'kept_songs': kept_songs})

# Generate report
report = requests.post('http://localhost:5000/api/report/generate').json()
```

### Custom Themes

Edit `templates/index.html` to customize colors and styles:

```css
/* Change primary color */
background: linear-gradient(135deg, #your-color 0%, #your-color-2 100%);

/* Change accent color */
.btn { background: #your-accent-color; }
```

### Export Options

Access raw data files for export:

```bash
# Copy scraped data
cp output/scraped_data.json ~/Desktop/

# Convert to Excel
python3 generate_song_excel.py

# Generate HTML report
python3 generate_complete_html.py
```

## Security Notes

- Web UI runs on localhost only (not accessible externally)
- No authentication required (local use only)
- Don't expose port 5000 to the internet
- Keep your `data/` directory private (contains account info)

## Future Enhancements

Planned features:
- ✅ Manual song filtering interface
- ✅ Real-time scraping status
- ✅ Analytics report generation
- 🔜 Second scan to check for missed songs
- 🔜 Export to multiple formats (Excel, PDF, HTML)
- 🔜 Chart visualizations (Chart.js integration)
- 🔜 Incremental scraping (only new videos)
- 🔜 Historical comparison reports

## Support

For issues, questions, or feature requests:
1. Check this documentation first
2. Review error messages in the web UI
3. Check the terminal output where `web_ui.py` is running
4. Review log files in `output/` directory
5. Open an issue on GitHub

## Quick Reference

```bash
# Start web UI
./start_ui.sh

# Access UI
open http://localhost:5000

# Stop server
Ctrl+C in terminal

# View logs
tail -f output/*.log

# Reset everything
rm output/scraped_data.json output/filtered_data.json output/settings.json
```

## Workflow Diagram

```
┌─────────────┐
│  1. SETTINGS │  Configure date range & parameters
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  2. SCRAPE  │  Scrape all TikTok accounts
└──────┬──────┘  (saves to scraped_data.json)
       │
       ▼
┌─────────────┐
│  3. EDIT    │  Manual song filtering
└──────┬──────┘  (saves to filtered_data.json)
       │
       ▼
┌─────────────┐
│  4. REPORT  │  Generate analytics
└─────────────┘  (view in browser)
```

---

**Warner Sound Tracker Web UI** - Making TikTok analytics simple and interactive.
