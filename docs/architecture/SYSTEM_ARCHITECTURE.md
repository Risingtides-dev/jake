# Warner Tracker - System Architecture

## Two-Port System Design

### Port 5001: INTERNAL DASHBOARD (Your Team)
**URL**: http://localhost:5001
**Purpose**: Tool for managing TikTok scraping and report generation
**Users**: You and your team members
**Status**: ✅ Running now

**Features**:
- **Step 1 - Settings**: Configure date ranges (Oct 14, 2025 - Today)
- **Step 2 - Scrape**: Pull data from 5 TikTok accounts
- **Step 3 - Edit**: Manual song filtering (remove non-Warner songs)
- **Step 4 - Generate**: Create client-ready reports

**What It Does**:
1. Loads Warner songs from CSV
2. Scrapes all TikTok accounts in parallel
3. Shows you EVERY song found
4. You manually click to keep/remove songs
5. Exports clean data for client reports

---

### Port 8000: CLIENT REPORTS (Their View)
**URL**: http://localhost:8000
**Purpose**: Beautiful HTML reports for clients
**Users**: Warner Music Group, other clients
**Status**: ✅ Running (Cursor is styling this)

**Features**:
- Professional earth-tone design
- Album art for each song
- Engagement metrics and charts
- Clean, shareable HTML
- Read-only (no editing)

**What It Shows**:
- Only filtered/approved Warner songs
- Beautiful visualizations
- Professional branding
- Ready to send to clients

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PORT 5001 (Internal)                      │
│                                                               │
│  Your Team Uses This:                                        │
│  1. Set dates → 2. Scrape → 3. Filter → 4. Generate         │
│                                                               │
│  Outputs:                                                    │
│  ├─ scraped_data.json    (all videos, all songs)           │
│  ├─ filtered_data.json   (Warner songs only)               │
│  └─ album_art/*.jpg      (downloaded from iTunes)          │
└───────────────────────┬───────────────────────────────────── ┘
                        │
                        │ Data feeds to...
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    PORT 8000 (Client)                        │
│                                                               │
│  Clients See This:                                           │
│  - Beautiful HTML report                                     │
│  - Album art thumbnails                                      │
│  - Engagement stats                                          │
│  - Professional design                                       │
│                                                               │
│  Input: filtered_data.json + album_art/                     │
│  Output: sound_usage_complete_report.html                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Current System Status

### ✅ Working Now
- [x] Port 5001: Internal dashboard running
- [x] Port 8000: Client report preview running
- [x] TikTok scraper (tiktok_analyzer.py)
- [x] Warner songs CSV (33 songs)
- [x] Config with filtered artists/songs
- [x] Album art fetcher (iTunes API)

### 🔄 In Progress
- [ ] Test full scraping workflow
- [ ] Test manual filtering interface
- [ ] Connect Port 5001 data → Port 8000 reports
- [ ] Integrate album art into scraping
- [ ] Apply config.py filters automatically

### 📅 To Do (By Friday)
- [ ] End-to-end testing
- [ ] Bug fixes
- [ ] Documentation for your team
- [ ] Client delivery package

---

## File Structure

```
warnertracker/
├── PORT 5001 (Internal Tool)
│   ├── web_ui.py                   # Flask backend
│   ├── templates/index.html        # Internal UI
│   ├── start_ui.sh                 # Startup script
│   └── config.py                   # Settings & filters
│
├── PORT 8000 (Client Reports)
│   ├── generate_complete_html.py   # Report generator
│   ├── fetch_album_art.py          # Album art fetcher
│   ├── preview_server.py           # Preview server
│   └── output/
│       └── sound_usage_complete_report.html
│
├── Core Data Pipeline
│   ├── tiktok_analyzer.py          # TikTok scraper
│   ├── data/
│   │   └── warner_songs_clean.csv  # 33 Warner songs
│   └── output/
│       ├── scraped_data.json       # (will be created)
│       ├── filtered_data.json      # (will be created)
│       └── album_art/              # (will be populated)
│
└── Documentation
    ├── WEB_UI_GUIDE.md             # User guide
    ├── AGENT_COORDINATION.md       # Agent sync file
    └── SYSTEM_ARCHITECTURE.md      # This file
```

---

## Team Workflow

### Daily Use (Your Team)

**Morning**: Start both systems
```bash
# Terminal 1: Start internal dashboard
cd warnertracker
./start_ui.sh
# Access at http://localhost:5001

# Terminal 2: Start client preview (Cursor handles this)
# Already running at http://localhost:8000
```

**Scraping** (15-30 min):
1. Open http://localhost:5001
2. Set date range
3. Click "Start Scraping"
4. Wait for all 5 accounts to complete
5. Review any timeouts/errors

**Filtering** (10-20 min):
1. Click "Load Scraped Data"
2. Review all songs
3. Remove non-Warner songs:
   - Goldford ❌
   - Monrovia ❌
   - Original sounds ❌
4. Click "Apply Filter"

**Report Generation** (5 min):
1. Click "Generate Report"
2. Check preview
3. Open http://localhost:8000 for client view
4. Download/share HTML with client

---

## Integration Points

### Where Systems Connect

**Data Exchange**:
```
Port 5001 creates:  filtered_data.json + album_art/
Port 8000 reads:    filtered_data.json + album_art/
```

**Next Steps**:
1. Port 5001 generates `filtered_data.json`
2. Port 8000's `generate_complete_html.py` reads it
3. Both systems share `output/` directory
4. Album art downloaded once, used by both

---

## Why Two Ports?

**Separation of Concerns**:
- Port 5001 = Messy work (scraping, filtering, debugging)
- Port 8000 = Clean output (client-ready reports)

**Benefits**:
1. Internal tool can be complex/ugly if needed
2. Client reports always look professional
3. Easy to iterate on design without breaking workflow
4. Can run client previews independently

**Trade-off**:
- Two servers to manage
- Data syncing between them
- But: Cleaner architecture, easier to maintain

---

## Deployment Notes

### For Local Use (Current)
- Both ports run on localhost
- Your team accesses Port 5001
- Preview client reports on Port 8000
- Share HTML files with clients

### For Production (Future)
- Port 5001: Deploy to internal server (password protected)
- Port 8000: Static HTML hosting (AWS S3, Netlify, etc.)
- Or: Merge into single system with different routes

---

## Contact & Support

**Questions**:
- Check AGENT_COORDINATION.md for latest updates
- See WEB_UI_GUIDE.md for usage instructions

**Issues**:
- Port conflicts: Change ports in web_ui.py
- Scraping errors: Check tiktok_analyzer.py output
- Filtering issues: Review config.py filters
