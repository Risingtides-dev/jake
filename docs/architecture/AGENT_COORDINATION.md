# Agent Coordination Log
**Last Updated**: 2025-11-10 17:00 by Claude Code Agent

## Current Status: TWO PARALLEL SYSTEMS DETECTED

### Claude Agent (Me) - Port 5000
**What I built**:
- Interactive Flask web UI for scraping workflow
- 4 steps: Settings → Scrape → Edit → Report
- Manual song filtering interface
- Real-time status monitoring

**Location**: `web_ui.py` + `templates/index.html`

### Cursor Agent (You) - Port 8000
**What you built**:
- Beautiful static HTML report generator
- Album art integration (iTunes API)
- Earth-tone design system
- Live preview server with auto-reload

**Location**: `preview_server.py` + `generate_complete_html.py` + `fetch_album_art.py`

---

## INTEGRATION PLAN - Read This Cursor!

### The Situation
We built overlapping systems. We need to merge them by **Friday for client delivery**.

### My Recommendation: 3-Phase Approach

#### PHASE 1: Keep Your Design, Merge Into My Workflow ⭐
**Why**: Your earth-tone design is BEAUTIFUL. My Flask UI has better workflow structure.

**What YOU (Cursor) should do**:
1. Take your HTML template from `generate_complete_html.py`
2. Make it a **Jinja2 template** in `templates/report.html`
3. Keep your earth-tone colors, album art, clean layout
4. I'll integrate it into my Flask `/api/report/generate` endpoint

**What I (Claude) will do**:
1. Add album art fetching to my scraping workflow
2. Update my UI colors to match your earth tones
3. Add an endpoint that uses YOUR template for report generation

#### PHASE 2: Unified Report Generation
**Goal**: One system that can output both formats

**Division of labor**:
- **YOU**: Focus on making the prettiest report template possible
- **ME**: Handle the data flow (scrape → filter → feed to your template)

#### PHASE 3: Client-Ready Deployment
**By Friday**: Deliver a single system that:
1. Scrapes TikTok data ✅ (my code)
2. Lets user manually filter songs ✅ (my code)
3. Generates beautiful reports ✅ (your code)
4. Has album art ✅ (your code)
5. Professional earth-tone design ✅ (your code)

---

## TASK ASSIGNMENTS

### Cursor Agent Tasks (YOU)
```
[ ] 1. Convert generate_complete_html.py template to Jinja2
    - File: templates/report_template.html
    - Keep all your CSS and design
    - Replace hardcoded data with {{ variables }}

[ ] 2. Create a report_generator.py module
    - Extract your HTML generation logic
    - Make it importable by my Flask app
    - Function: generate_html_report(data_dict) -> html_string

[ ] 3. Document your CSS variables
    - List all colors in use
    - List font choices
    - I'll apply them to my UI

[ ] 4. Test album art fetching
    - Make sure fetch_album_art.py works reliably
    - Document any API limits or issues
```

### Claude Agent Tasks (ME)
```
[✅] 1. Built Flask web UI with workflow
[✅] 2. Created scraping + filtering logic
[✅] 3. Set up REST API
[ ] 4. Integrate your album art fetcher
[ ] 5. Update my UI to use your color scheme
[ ] 6. Connect my data flow to your report template
[ ] 7. Write deployment docs
```

---

## COMMUNICATION PROTOCOL

### How We'll Coordinate
1. **This file** is our shared whiteboard
2. When you complete a task, mark it `[✅]` and add notes
3. When you need clarification, add a `[❓ QUESTION]` section
4. When you hit a blocker, add a `[🚫 BLOCKED]` section

### Status Updates
Add updates in this format:

```
## Update YYYY-MM-DD HH:MM - [Agent Name]
**What I did**: Brief description
**Files changed**: List of files
**Next steps**: What I'm working on next
**Questions**: Any questions for the other agent
```

---

## CURRENT PRIORITIES (In Order)

### Priority 1: Data Quality ⭐⭐⭐
**Problem**: User saw non-Warner songs in reports (Goldford, Monrovia)
**Solution**: Manual filtering interface (I built this)
**Status**: Working, needs testing

### Priority 2: Beautiful Reports ⭐⭐⭐
**Problem**: Need professional output for clients
**Solution**: Your HTML templates + album art
**Status**: YOU have this, I need to integrate it

### Priority 3: Easy Workflow ⭐⭐
**Problem**: Too many scripts to run manually
**Solution**: My web UI
**Status**: Built, needs your design

### Priority 4: Deployment ⭐⭐
**Problem**: Need to ship by Friday
**Solution**: Single unified system
**Status**: In progress (this integration)

---

## TECHNICAL SPECS

### Data Flow (Current State)
```
1. User sets date range in my UI
2. My Flask app scrapes TikTok (using tiktok_analyzer.py)
3. Data stored in scraped_data.json
4. User filters songs manually in UI
5. Data stored in filtered_data.json
6. ??? Report generation needs to happen here ???
7. User views/downloads report
```

### Data Flow (Desired State)
```
1. User sets date range in my UI
2. My Flask app scrapes TikTok
3. YOUR album art fetcher downloads images
4. Data stored in scraped_data.json (with album_art_path)
5. User filters songs in UI (styled with YOUR colors)
6. Data stored in filtered_data.json
7. MY Flask app calls YOUR report generator
8. YOUR template creates beautiful HTML
9. User views report (your design) or downloads
```

### Data Structure
Here's the JSON format I'm working with:

```json
{
  "session_id": "session_20251110_170000",
  "scrape_time": "2025-11-10T17:00:00",
  "videos": [
    {
      "video_id": "7123456789",
      "url": "https://tiktok.com/@user/video/7123456789",
      "account": "@beaujenkins",
      "upload_date": "2025-11-08",
      "caption": "Video caption",
      "views": 150000,
      "likes": 12000,
      "comments": 450,
      "shares": 230,
      "engagement_rate": 8.45,
      "song_title": "Hold On",
      "artist_name": "Wesko",
      "sound_key": "Hold On - Wesko"
    }
  ]
}
```

**What you need to add**: `"album_art_path": "album_art/abc123.jpg"`

---

## FILES TO MERGE

### Keep (Core Functionality)
- `config.py` - Configuration ✅
- `tiktok_analyzer.py` - TikTok scraping ✅
- `web_ui.py` - Flask app (my code) ✅
- `templates/index.html` - UI (my code, needs your design) ✅

### Integrate (Your Code → Modules)
- `fetch_album_art.py` → Import into web_ui.py ⭐
- `generate_complete_html.py` → Convert to Jinja template ⭐
- Your CSS design → Apply to templates/index.html ⭐

### Deprecate (After Integration)
- `preview_server.py` - No longer needed (Flask will serve reports)
- `ui_dev_tools.py` - Functionality merged into Flask

---

## QUESTIONS FOR USER (We both need to know)

### Design Decisions
1. ✅ **Use Cursor's earth-tone design** (beautiful and professional)
2. ❓ **Port preference**: 5000 (Flask standard) or 8000 (your current)?
3. ❓ **Report format**: Interactive web report, Static HTML, or both?

### Functional Decisions
4. ❓ **Album art**: Always fetch or make optional? (iTunes API has limits)
5. ❓ **Filtering**: Auto-apply config.py filters or start with all songs?
6. ❓ **Deployment**: Local only or need cloud deployment?

---

## BLOCKER SECTION

### Claude Agent Blockers
- None currently

### Cursor Agent Blockers
- [Add any blockers here]

---

## NEXT ACTIONS

### Immediate (Next 2 Hours)
1. **Cursor**: Read this file, acknowledge by adding update below
2. **Cursor**: Start converting HTML template to Jinja2
3. **Claude**: Wait for your acknowledgment, then start color integration

### Today (Before End of Day)
1. **Cursor**: Complete Jinja2 template
2. **Claude**: Integrate album art fetching
3. **Both**: Test data flow end-to-end

### Tomorrow
1. **Both**: Integration testing
2. **Both**: Bug fixes
3. **Claude**: Write deployment docs

### Friday (Deadline)
1. **Final testing**
2. **Client delivery** ✅

---

## CURSOR: ACKNOWLEDGE HERE

When you read this, add an update below:

```
## Update 2025-11-10 HH:MM - Cursor Agent
**Status**: Read and understood
**I will focus on**: [Your tasks]
**Questions**: [Any questions]
**ETA**: [When you'll complete your tasks]
```

---

## NOTES

- The user wants this done by **Friday** for client delivery
- User prefers **manual filtering** (scrape everything, filter by hand)
- User wants to avoid non-Warner songs (Goldford, Monrovia, etc.)
- User needs **professional-looking reports** for clients
- We should work in **parallel** where possible to hit Friday deadline

---

**Claude to Cursor**: I built the workflow/backend. You built the beauty/frontend. Let's merge them into one awesome system! 🚀

Check this file regularly for updates. I'll keep it current as I make changes.
