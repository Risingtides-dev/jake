# Warner Sound Tracker - Database Schema Documentation

## Overview

The Warner Sound Tracker uses SQLite as its database engine to store persistent data about TikTok accounts, videos, sounds, and scraping history. This document describes the complete database schema, relationships, and usage patterns.

**Database File:** `tracker.db` (in project root)

## Quick Reference

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `accounts` | TikTok accounts being tracked | username, last_scraped_at |
| `videos` | Individual TikTok videos | video_id, views, likes, engagement_rate |
| `sounds` | Songs/sounds used in videos | sound_key, is_exclusive |
| `scrape_sessions` | Scraping job history | session_id, start_time, status |
| `scrape_logs` | Per-account scrape details | account_id, videos_found |
| `video_history` | Historical metric snapshots | video_id, scraped_at |
| `exclusive_songs` | Songs to filter from reports | sound_key, song_title |

---

## Table Schemas

### 1. accounts

Stores information about TikTok accounts being tracked.

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,           -- @username format
    display_name TEXT,                        -- Account display name
    followers INTEGER,                        -- Follower count
    following INTEGER,                        -- Following count
    total_videos INTEGER,                     -- Total videos on profile
    total_likes INTEGER,                      -- Total likes on profile
    bio TEXT,                                 -- Account bio/description
    is_active BOOLEAN DEFAULT 1,             -- Is account currently active?
    is_target_account BOOLEAN DEFAULT 0,     -- Is this a target account for exclusive song analysis?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP,               -- When was this account last scraped?
    scrape_count INTEGER DEFAULT 0,          -- How many times has this been scraped?
    notes TEXT                               -- Admin notes
)
```

**Indexes:**
- `idx_accounts_username` on `username`
- `idx_accounts_active` on `is_active`
- `idx_accounts_target` on `is_target_account`
- `idx_accounts_last_scraped` on `last_scraped_at`

**Key Features:**
- `username` is unique (enforced by constraint)
- `last_scraped_at` tracks when incremental scraping should start
- `is_target_account` flag used for exclusive song filtering
- Automatic `updated_at` timestamp via trigger

---

### 2. videos

Stores individual TikTok video metadata and engagement metrics.

```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,           -- TikTok video ID (from URL)
    account_id INTEGER NOT NULL,             -- Foreign key to accounts table
    tiktok_url TEXT NOT NULL,                -- Full TikTok URL
    upload_date TEXT NOT NULL,               -- ISO 8601 format: YYYY-MM-DD
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,        -- Calculated: ((likes+comments+shares)/views)*100
    caption TEXT,                            -- Video caption/description
    hashtags TEXT,                           -- Comma-separated hashtags
    sound_id INTEGER,                        -- Foreign key to sounds table
    duration INTEGER,                        -- Video duration in seconds
    is_deleted BOOLEAN DEFAULT 0,            -- Has this video been deleted from TikTok?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    FOREIGN KEY (sound_id) REFERENCES sounds (id) ON DELETE SET NULL
)
```

**Indexes:**
- `idx_videos_video_id` on `video_id`
- `idx_videos_account_id` on `account_id`
- `idx_videos_sound_id` on `sound_id`
- `idx_videos_upload_date` on `upload_date`
- `idx_videos_views` on `views`
- `idx_videos_engagement` on `engagement_rate`

**Key Features:**
- `video_id` is unique (one entry per video)
- Cascading delete when account is removed
- `upload_date` stored as text for easy date filtering
- Engagement rate pre-calculated for performance
- Historical changes tracked in `video_history` table

---

### 3. sounds

Aggregated information about songs/sounds used across videos.

```sql
CREATE TABLE sounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sound_key TEXT NOT NULL UNIQUE,          -- Format: "Song Title - Artist Name"
    song_title TEXT NOT NULL,
    artist_name TEXT,
    is_exclusive BOOLEAN DEFAULT 0,          -- Is this song exclusive to target accounts?
    total_usage_count INTEGER DEFAULT 0,     -- How many videos use this sound?
    total_views INTEGER DEFAULT 0,           -- Sum of views across all videos
    total_likes INTEGER DEFAULT 0,           -- Sum of likes across all videos
    total_comments INTEGER DEFAULT 0,        -- Sum of comments across all videos
    total_shares INTEGER DEFAULT 0,          -- Sum of shares across all videos
    avg_engagement_rate REAL DEFAULT 0.0,    -- Average engagement rate
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
)
```

**Indexes:**
- `idx_sounds_sound_key` on `sound_key`
- `idx_sounds_exclusive` on `is_exclusive`
- `idx_sounds_usage_count` on `total_usage_count`

**Key Features:**
- `sound_key` format standardizes matching: "Title - Artist"
- Aggregated metrics calculated from all videos using this sound
- `is_exclusive` flag set when sound only used by target accounts
- Used for report generation and filtering

---

### 4. scrape_sessions

Tracks each scraping job/session for auditing and debugging.

```sql
CREATE TABLE scrape_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,         -- UUID or timestamp-based ID
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'running',           -- running, completed, failed, partial
    total_accounts INTEGER DEFAULT 0,
    successful_scrapes INTEGER DEFAULT 0,
    failed_scrapes INTEGER DEFAULT 0,
    total_videos_scraped INTEGER DEFAULT 0,
    total_new_videos INTEGER DEFAULT 0,
    total_updated_videos INTEGER DEFAULT 0,
    error_log TEXT,                          -- JSON or text log of errors
    configuration TEXT,                      -- JSON snapshot of config used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_sessions_session_id` on `session_id`
- `idx_sessions_start_time` on `start_time`
- `idx_sessions_status` on `status`

**Key Features:**
- One entry per scraping run
- Tracks success/failure metrics
- Stores configuration snapshot for reproducibility
- Links to individual account logs via `session_id`

---

### 5. scrape_logs

Detailed per-account scraping logs for each session.

```sql
CREATE TABLE scrape_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,                -- Links to scrape_sessions
    account_id INTEGER NOT NULL,             -- Links to accounts
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,                    -- success, failed, skipped
    videos_found INTEGER DEFAULT 0,          -- Total videos found for account
    new_videos INTEGER DEFAULT 0,            -- New videos added
    updated_videos INTEGER DEFAULT 0,        -- Existing videos updated
    error_message TEXT,                      -- Error details if failed
    execution_time_seconds REAL,             -- How long did this scrape take?
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
)
```

**Indexes:**
- `idx_logs_session_id` on `session_id`
- `idx_logs_account_id` on `account_id`
- `idx_logs_timestamp` on `timestamp`

**Key Features:**
- One entry per account per session
- Tracks individual account scraping performance
- Useful for debugging failed scrapes
- Performance metrics (execution time)

---

### 6. video_history

Historical snapshots of video metrics for trend analysis.

```sql
CREATE TABLE video_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,                  -- Links to videos.video_id
    session_id TEXT NOT NULL,                -- Links to scrape_sessions
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE
)
```

**Indexes:**
- `idx_history_video_id` on `video_id`
- `idx_history_session_id` on `session_id`
- `idx_history_scraped_at` on `scraped_at`

**Key Features:**
- Stores metric snapshots every time a video is scraped
- Enables historical trend analysis
- Shows how videos perform over time
- Used for growth rate calculations

**Example Query:**
```sql
-- Get view growth over time for a video
SELECT scraped_at, views,
       views - LAG(views) OVER (ORDER BY scraped_at) AS view_increase
FROM video_history
WHERE video_id = '7234567890123456789'
ORDER BY scraped_at;
```

---

### 7. exclusive_songs

List of songs that should be filtered from reports.

```sql
CREATE TABLE exclusive_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sound_key TEXT NOT NULL UNIQUE,          -- Format: "Song Title - Artist Name"
    song_title TEXT NOT NULL,
    artist_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT DEFAULT 'system',          -- Who added this? (system, admin name)
    reason TEXT,                             -- Why is this exclusive?
    FOREIGN KEY (sound_key) REFERENCES sounds (sound_key) ON DELETE CASCADE
)
```

**Key Features:**
- Populated from `config.EXCLUSIVE_SONGS`
- Used to filter songs from Excel/HTML reports
- Can be manually managed through this table
- Links to `sounds` table for consistency

---

## Relationships

```
accounts (1) ─────< (M) videos
                        │
                        ├──> (M) video_history
                        │
                        └──> (1) sounds
                                  │
                                  └──> exclusive_songs (1)

scrape_sessions (1) ───< (M) scrape_logs
      │
      └───< (M) video_history
```

### Relationship Details:

1. **accounts → videos** (One-to-Many)
   - One account has many videos
   - Cascade delete: removing account deletes all its videos

2. **videos → sounds** (Many-to-One)
   - Many videos can use the same sound
   - Set NULL on delete: removing sound doesn't delete videos

3. **videos → video_history** (One-to-Many)
   - One video has many historical snapshots
   - Cascade delete: removing video deletes its history

4. **scrape_sessions → scrape_logs** (One-to-Many)
   - One session has many per-account logs
   - Non-enforced relationship (via session_id)

5. **scrape_sessions → video_history** (One-to-Many)
   - One session creates many history entries
   - Non-enforced relationship (via session_id)

6. **sounds → exclusive_songs** (One-to-One optional)
   - Some sounds are marked as exclusive
   - Cascade delete: removing sound removes exclusive entry

---

## Triggers

### Auto-Update Timestamps

Three triggers automatically update `updated_at` timestamps:

```sql
CREATE TRIGGER update_accounts_timestamp
AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER update_videos_timestamp
AFTER UPDATE ON videos
BEGIN
    UPDATE videos SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER update_sounds_timestamp
AFTER UPDATE ON sounds
BEGIN
    UPDATE sounds SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

---

## Common Queries

### 1. Get accounts needing scraping (older than 24 hours)

```sql
SELECT username, last_scraped_at
FROM accounts
WHERE is_active = 1
  AND (last_scraped_at IS NULL
       OR last_scraped_at < datetime('now', '-24 hours'))
ORDER BY last_scraped_at ASC;
```

### 2. Get top 10 videos by engagement for an account

```sql
SELECT v.tiktok_url, v.views, v.likes, v.engagement_rate, s.song_title
FROM videos v
LEFT JOIN sounds s ON v.sound_id = s.id
WHERE v.account_id = (SELECT id FROM accounts WHERE username = '@someaccount')
ORDER BY v.engagement_rate DESC
LIMIT 10;
```

### 3. Get sound usage statistics (excluding exclusive songs)

```sql
SELECT s.sound_key, s.total_usage_count, s.total_views, s.avg_engagement_rate
FROM sounds s
WHERE s.is_exclusive = 0
  AND s.sound_key NOT IN (SELECT sound_key FROM exclusive_songs)
ORDER BY s.total_usage_count DESC;
```

### 4. Get videos uploaded after a specific date

```sql
SELECT v.*, a.username
FROM videos v
JOIN accounts a ON v.account_id = a.id
WHERE v.upload_date >= '2025-10-01'
ORDER BY v.upload_date DESC;
```

### 5. Get scraping session summary

```sql
SELECT
    session_id,
    start_time,
    status,
    total_accounts,
    successful_scrapes,
    total_new_videos,
    CAST((julianday(end_time) - julianday(start_time)) * 24 * 60 AS INTEGER) AS duration_minutes
FROM scrape_sessions
ORDER BY start_time DESC
LIMIT 10;
```

### 6. Get account performance summary

```sql
SELECT
    a.username,
    COUNT(v.id) AS total_videos,
    SUM(v.views) AS total_views,
    AVG(v.engagement_rate) AS avg_engagement,
    MAX(v.upload_date) AS latest_video
FROM accounts a
LEFT JOIN videos v ON a.id = v.account_id
WHERE a.is_active = 1
GROUP BY a.id
ORDER BY avg_engagement DESC;
```

---

## Data Flow

### 1. Initial Setup

```
extract_accounts_from_csv.py
    ↓
config.py (ACCOUNTS list)
    ↓
init_db.py --reset
    ↓
Database created with schema
```

### 2. First Scrape

```
scraper_daemon.py starts
    ↓
Creates scrape_session entry (status='running')
    ↓
For each account:
    - Calls tiktok_analyzer.py
    - Inserts/updates account record
    - Inserts new videos
    - Updates existing videos
    - Creates scrape_log entry
    - Takes video_history snapshot
    ↓
Updates scrape_session (status='completed')
    ↓
Updates accounts.last_scraped_at
```

### 3. Incremental Scrape

```
scraper_daemon.py checks accounts.last_scraped_at
    ↓
Only scrapes accounts older than threshold
    ↓
Compares video_id to existing records
    ↓
Only processes new/changed videos
    ↓
Updates metrics + creates history snapshot
```

### 4. Report Generation

```
generate_*.py scripts
    ↓
Query videos table (filtered by date/exclusive songs)
    ↓
Aggregate by sound using sounds table
    ↓
Generate HTML/Excel reports
    ↓
Save to output/ directory
```

---

## Database Maintenance

### Initialization

```bash
# Create fresh database
python3 init_db.py

# Reset database (WARNING: deletes all data)
python3 init_db.py --reset

# Show database info
python3 init_db.py --info
```

### Backup

```bash
# Create backup
cp tracker.db tracker_backup_$(date +%Y%m%d).db

# Or use SQLite's backup command
sqlite3 tracker.db ".backup tracker_backup.db"
```

### Vacuum (reclaim space)

```bash
sqlite3 tracker.db "VACUUM;"
```

### Check integrity

```bash
sqlite3 tracker.db "PRAGMA integrity_check;"
```

---

## Performance Considerations

### Indexing Strategy

All foreign keys and frequently queried columns have indexes:
- `username` for account lookups
- `video_id` for deduplication
- `upload_date` for date filtering
- `sound_key` for aggregation
- `session_id` for log queries

### Query Optimization Tips

1. **Use indexes**: Queries on indexed columns are 10-100x faster
2. **EXPLAIN QUERY PLAN**: Check if your query uses indexes
   ```sql
   EXPLAIN QUERY PLAN
   SELECT * FROM videos WHERE upload_date >= '2025-10-01';
   ```
3. **Limit large result sets**: Always use `LIMIT` for testing
4. **Aggregate at database level**: Use SQL aggregation instead of Python loops
5. **Batch inserts**: Use transactions for bulk inserts

### Storage Estimates

| Rows | Approximate Size |
|------|------------------|
| 50 accounts | ~10 KB |
| 10,000 videos | ~5 MB |
| 1,000 sounds | ~200 KB |
| 100 scrape sessions | ~50 KB |
| 50,000 history entries | ~10 MB |

**Expected total after 6 months:** ~50-100 MB

---

## Migration Strategy

If schema changes are needed:

1. **Backup current database**
2. **Create migration script** (e.g., `migrations/001_add_column.sql`)
3. **Test on copy of database**
4. **Apply to production**
5. **Update `init_db.py` to reflect changes**

### Example Migration

```sql
-- Migration: Add 'verified' column to accounts
BEGIN TRANSACTION;

ALTER TABLE accounts ADD COLUMN is_verified BOOLEAN DEFAULT 0;
CREATE INDEX idx_accounts_verified ON accounts(is_verified);

-- Update schema version
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER);
INSERT INTO schema_version VALUES (2);

COMMIT;
```

---

## Security Notes

- **No authentication**: SQLite has no built-in access control
- **File permissions**: Set restrictive permissions on `tracker.db`
  ```bash
  chmod 600 tracker.db
  ```
- **SQL injection**: Always use parameterized queries
  ```python
  # GOOD
  cursor.execute('SELECT * FROM accounts WHERE username = ?', (username,))

  # BAD
  cursor.execute(f'SELECT * FROM accounts WHERE username = "{username}"')
  ```
- **Sensitive data**: Don't store passwords or API keys in database

---

## Troubleshooting

### Database is locked

**Cause:** Another process is writing to the database

**Solution:**
```python
# Increase timeout in connection
conn = sqlite3.connect('tracker.db', timeout=30.0)
```

### Foreign key constraint failed

**Cause:** Trying to insert video with non-existent account_id

**Solution:** Ensure account exists before inserting videos

### Performance degradation

**Cause:** Database fragmentation or missing indexes

**Solution:**
```bash
# Rebuild database
sqlite3 tracker.db "VACUUM;"

# Reanalyze for query planner
sqlite3 tracker.db "ANALYZE;"
```

---

## Related Documentation

- [TRACKER_DOCUMENTATION.md](TRACKER_DOCUMENTATION.md) - General usage
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- SQLite Documentation: https://www.sqlite.org/docs.html

---

**Last Updated:** November 2025
**Schema Version:** 1.0
