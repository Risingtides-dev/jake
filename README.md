# Warner Sound Tracker

A comprehensive TikTok analytics and tracking system designed to monitor sound/song usage across multiple Warner Music Group TikTok accounts. This system automatically scrapes TikTok data, analyzes engagement metrics, identifies shared vs exclusive songs, and generates detailed reports.

## Overview

The Warner Sound Tracker helps you:
- **Track TikTok accounts** associated with Warner Music Group (currently configured for 5 accounts)
- **Monitor sound/song usage** across all accounts in real-time
- **Analyze engagement metrics** (views, likes, comments, shares)
- **Identify trends** and top-performing content
- **Generate professional reports** in HTML and Excel formats with album art
- **Interactive web dashboard** for managing scrapes and filtering songs
- **Automate data collection** with scheduled scraping

## Quick Start

### Prerequisites
- Python 3.7 or higher
- `yt-dlp` installed ([installation guide](https://github.com/yt-dlp/yt-dlp#installation))

### Installation

1. Clone this repository:
```bash
git clone https://github.com/Risingtides-dev/Tracker-Warner.git
cd Tracker-Warner
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your accounts (see [Configuration](#configuration) section)

## Core Scripts

### Web Interface
- **[src/web/web_ui.py](src/web/web_ui.py)** - Flask-based interactive dashboard for managing scrapes, filtering songs, and generating reports (runs on port 5001)

### Data Collection
- **[src/core/tiktok_analyzer.py](src/core/tiktok_analyzer.py)** - Core scraping engine for individual TikTok accounts with music link extraction
- **[src/scrapers/inhouse_network_scraper.py](src/scrapers/inhouse_network_scraper.py)** - Main production tool for tracking all accounts
- **[src/core/scraper_daemon.py](src/core/scraper_daemon.py)** - Automated scraper with timestamp tracking and SQLite storage (in development)

### Data Analysis
- **[src/analysis/aggregate_sound_analysis.py](src/analysis/aggregate_sound_analysis.py)** - Aggregates sound usage across multiple accounts
- **[src/analysis/find_exclusive_songs.py](src/analysis/find_exclusive_songs.py)** - Identifies songs used exclusively by target accounts

### Report Generation
- **[src/reports/generate_song_excel.py](src/reports/generate_song_excel.py)** - Creates Excel reports organized by song
- **[src/reports/generate_complete_html.py](src/reports/generate_complete_html.py)** - Generates clean, modern HTML reports with earth-tone palette
- **[src/reports/generate_glass_html.py](src/reports/generate_glass_html.py)** - Advanced HTML reports with album art, CSV filtering, and glassmorphism design

### Utilities
- **[src/utils/fetch_album_art.py](src/utils/fetch_album_art.py)** - Downloads album artwork from iTunes API for enhanced reports
- **[src/analysis/extract_warner_songs.py](src/analysis/extract_warner_songs.py)** - Extracts Warner song list from CSV files
- **[src/utils/extract_accounts_from_csv.py](src/utils/extract_accounts_from_csv.py)** - Extracts TikTok accounts from CSV files
- **[src/database/init_db.py](src/database/init_db.py)** - Initializes the SQLite database for scraper daemon

## Configuration

All configuration is centralized in **[src/utils/config.py](src/utils/config.py)**. You'll need to populate:

1. **Account lists** - TikTok accounts to track
2. **Date filters** - Cutoff dates for data collection
3. **Exclusive songs** - Songs to filter from reports
4. **Output paths** - Where to save generated reports

See [docs/TRACKER_DOCUMENTATION.md](docs/TRACKER_DOCUMENTATION.md) for detailed configuration instructions.

## Usage Examples

### Start the Web Dashboard
```bash
python3 src/web/web_ui.py
# Visit http://localhost:5001 in your browser
```

### Analyze a Single Account
```bash
python3 src/core/tiktok_analyzer.py --url @username --limit 20
```

### Run Full Network Scrape
```bash
python3 src/scrapers/inhouse_network_scraper.py
```

### Generate Advanced HTML Report (with album art)
```bash
python3 src/reports/generate_glass_html.py
```

### Generate Simple HTML Report
```bash
python3 src/reports/generate_complete_html.py
```

### Generate Excel Report
```bash
python3 src/reports/generate_song_excel.py
```

## Architecture

```
TikTok Profiles → yt-dlp → JSON → Python Scripts → SQLite DB → Reports (HTML/Excel)
```

For detailed architecture information, see [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md).

## Documentation

- **[docs/TRACKER_DOCUMENTATION.md](docs/TRACKER_DOCUMENTATION.md)** - Comprehensive technical documentation
- **[docs/setup/SETUP_MAC.md](docs/setup/SETUP_MAC.md)** - macOS setup guide
- **[docs/setup/SETUP_WINDOWS.md](docs/setup/SETUP_WINDOWS.md)** - Windows setup guide
- **[docs/architecture/PLATFORM_DIFFERENCES.md](docs/architecture/PLATFORM_DIFFERENCES.md)** - Cross-platform compatibility notes
- **[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - Database structure documentation
- **[docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)** - Production deployment guide
- **[docs/deployment/CRON_SETUP.md](docs/deployment/CRON_SETUP.md)** - Automated scraping setup

## Features

### Current Features ✅
- Multi-account TikTok scraping
- Engagement metrics calculation (views, likes, comments, shares)
- Sound/song aggregation across accounts
- CSV-based song whitelist filtering
- Album art integration via iTunes API
- Interactive web dashboard (Flask-based)
- Manual song filtering interface
- HTML report generation (2 themes: clean modern & glassmorphism)
- Excel report generation
- Date-based filtering
- Music link extraction from TikTok
- Configurable accounts and settings (centralized in config.py)
- Background scraping with progress tracking

### In Development 🚧
- SQLite database integration (init_db.py exists, scraper_daemon.py incomplete)
- Automated scheduled scraping with daemon mode
- Timestamp-based incremental updates
- Historical trend analysis

### Future Enhancements 💡
- Email/Slack notifications
- API endpoints for data access
- Advanced analytics and insights

## Project Structure

```
tracker-warner/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
│
├── src/                              # All source code
│   ├── core/                         # Core scrapers & daemon
│   ├── scrapers/                     # Account/campaign scrapers
│   ├── analysis/                     # Data analysis tools
│   ├── reports/                      # Report generation
│   ├── web/                          # Web UI
│   ├── database/                     # Database operations
│   ├── api/                          # REST API (future)
│   ├── utils/                        # Utilities & config
│   └── cli/                          # CLI tools
│
├── docs/                             # Documentation
│   ├── setup/                        # Setup guides
│   ├── deployment/                   # Deployment guides
│   ├── guides/                       # User guides
│   └── architecture/                 # Architecture docs
│
├── data/                             # Input data
│   ├── campaigns/                    # Campaign CSVs
│   └── accounts/                     # Account lists
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── fixtures/                     # Test fixtures
│
├── scripts/                          # Shell/batch scripts
│   └── legacy/                       # Deprecated scripts
│
├── cache/                            # Scraping cache (not in git)
├── output/                           # Generated reports (not in git)
├── deployment/                       # Deployment configs
└── .github/                          # GitHub workflows
```

## Contributing

This is an internal Warner Music Group project. For questions or issues, contact the development team.

## License

Internal use only - Warner Music Group

## Support

For technical documentation and troubleshooting:
- See [docs/TRACKER_DOCUMENTATION.md](docs/TRACKER_DOCUMENTATION.md)
- Check platform-specific setup guides ([Mac](docs/setup/SETUP_MAC.md) | [Windows](docs/setup/SETUP_WINDOWS.md))
- Review [docs/architecture/PLATFORM_DIFFERENCES.md](docs/architecture/PLATFORM_DIFFERENCES.md) for compatibility issues

---

**Repository:** https://github.com/risingtides-dev/jake
**Last Updated:** December 2025
