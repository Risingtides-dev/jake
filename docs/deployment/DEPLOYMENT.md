# Warner Sound Tracker - Production Deployment Guide

## Overview

This guide walks you through deploying the Warner Sound Tracker in a production environment. Whether you're setting it up on a dedicated server, cloud instance, or local machine, this document covers best practices for reliability, security, and maintainability.

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| **Local Machine** | Testing, small-scale | Low | Free |
| **Dedicated Server** | Production, control | Medium | Hardware cost |
| **Cloud VM** (AWS EC2, DigitalOcean) | Production, scalability | Medium | $5-50/month |
| **Serverless** (AWS Lambda) | Intermittent scraping | High | Pay-per-use |

**Recommendation:** Start with a local machine or small cloud VM ($5-10/month).

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All scripts tested locally
- [ ] Database schema created and tested
- [ ] Configuration file (`config.py`) fully populated
- [ ] Virtual environment works correctly
- [ ] `yt-dlp` installed and functional
- [ ] Sample scraping run successful
- [ ] Reports generate correctly
- [ ] Git repository up to date
- [ ] Documentation reviewed

---

## Production Deployment - Step by Step

### Phase 1: Server Setup

#### Option A: Cloud VM (DigitalOcean/AWS/Linode)

**1. Create a Droplet/Instance**

Recommended specs:
- **OS:** Ubuntu 22.04 LTS
- **RAM:** 1-2 GB
- **Storage:** 25-50 GB SSD
- **CPU:** 1-2 cores

**2. SSH into server**

```bash
ssh root@your-server-ip
```

**3. Update system**

```bash
apt update && apt upgrade -y
```

**4. Create non-root user**

```bash
adduser warnertracker
usermod -aG sudo warnertracker
su - warnertracker
```

#### Option B: Local Server/Machine

Skip server creation steps and proceed with software installation.

---

### Phase 2: Software Installation

#### 1. Install Python 3

```bash
# Check if Python is installed
python3 --version

# If not installed (Ubuntu/Debian)
sudo apt install python3 python3-pip python3-venv -y

# macOS (using Homebrew)
brew install python3
```

#### 2. Install yt-dlp

```bash
# Option 1: Homebrew (macOS)
brew install yt-dlp

# Option 2: pip (Linux/macOS)
sudo pip3 install yt-dlp

# Option 3: Direct download
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Verify installation
yt-dlp --version
```

#### 3. Install Git

```bash
# Ubuntu/Debian
sudo apt install git -y

# macOS
brew install git

# Verify
git --version
```

#### 4. Install SQLite (usually pre-installed)

```bash
sqlite3 --version

# If not installed (Ubuntu/Debian)
sudo apt install sqlite3 -y
```

---

### Phase 3: Project Deployment

#### 1. Clone Repository

```bash
# Navigate to project directory
cd ~
mkdir projects
cd projects

# Clone your repository
git clone https://github.com/Risingtides-dev/Tracker-Warner.git
cd Tracker-Warner

# Or if using SSH
git clone git@github.com:Risingtides-dev/Tracker-Warner.git
cd Tracker-Warner
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Verify Installation

```bash
python3 -c "import openpyxl; print('openpyxl:', openpyxl.__version__)"
yt-dlp --version
```

---

### Phase 4: Configuration

#### 1. Populate Configuration

**Extract accounts from CSV (if you have CSV files):**

```bash
python3 extract_accounts_from_csv.py
```

**Edit config.py:**

```bash
nano config.py  # or vim, or use your preferred editor
```

Update the following:

```python
# Account lists
ACCOUNTS = [
    '@account1',
    '@account2',
    # ... add all accounts
]

TARGET_ACCOUNTS = {
    '@account1',
    # ... target accounts for exclusive analysis
}

# Date filters
CUTOFF_DATE = datetime(2025, 10, 1)
EXCLUSIVE_SONGS_YEAR = 2025
EXCLUSIVE_SONGS_MONTH = 11

# Exclusive songs (if any)
EXCLUSIVE_SONGS = {
    'Song Title - Artist Name',
    # ... add exclusive songs
}
```

#### 2. Initialize Database

```bash
python3 init_db.py
```

Verify:
```bash
python3 init_db.py --info
```

---

### Phase 5: Testing

#### 1. Test Single Account Scraping

```bash
python3 tiktok_analyzer.py --url @testaccount --limit 5
```

#### 2. Test Database Storage

```bash
python3 scraper_daemon.py --once --accounts @testaccount
```

Check database:
```bash
sqlite3 tracker.db "SELECT * FROM accounts;"
```

#### 3. Test Report Generation

```bash
python3 generate_glass_html.py
ls -la output/
```

Open the generated HTML file in a browser to verify.

---

### Phase 6: Automation Setup

#### Option 1: Cron Job (Recommended)

See [CRON_SETUP.md](CRON_SETUP.md) for detailed instructions.

**Quick setup:**

```bash
# Create wrapper script
nano run_scraper.sh
```

Add:
```bash
#!/bin/bash
cd /home/warnertracker/projects/Tracker-Warner
source venv/bin/activate
python3 scraper_daemon.py --once
```

Make executable:
```bash
chmod +x run_scraper.sh
```

Add to crontab:
```bash
crontab -e
```

Add line:
```cron
0 2 * * * /home/warnertracker/projects/Tracker-Warner/run_scraper.sh >> /home/warnertracker/projects/Tracker-Warner/cron.log 2>&1
```

#### Option 2: Systemd Service (Linux)

See [CRON_SETUP.md](CRON_SETUP.md) for full systemd setup.

---

### Phase 7: Monitoring & Logging

#### 1. Configure Log Rotation

Create `/etc/logrotate.d/warner-tracker`:

```bash
sudo nano /etc/logrotate.d/warner-tracker
```

Add:
```
/home/warnertracker/projects/Tracker-Warner/*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 0644 warnertracker warnertracker
}
```

#### 2. Set Up Monitoring Script

Create `monitor.sh`:

```bash
#!/bin/bash

# Check last successful scrape
LAST_SCRAPE=$(sqlite3 tracker.db "SELECT MAX(start_time) FROM scrape_sessions WHERE status='completed';")
CURRENT_TIME=$(date +%s)
LAST_SCRAPE_TIME=$(date -d "$LAST_SCRAPE" +%s 2>/dev/null || echo 0)
HOURS_SINCE=$(( ($CURRENT_TIME - $LAST_SCRAPE_TIME) / 3600 ))

if [ $HOURS_SINCE -gt 48 ]; then
    echo "WARNING: No successful scrape in $HOURS_SINCE hours"
    # Send alert (configure email/Slack here)
fi

# Check disk space
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage at ${DISK_USAGE}%"
fi

# Check database size
DB_SIZE=$(du -m tracker.db | cut -f1)
if [ $DB_SIZE -gt 500 ]; then
    echo "WARNING: Database size is ${DB_SIZE}MB"
fi
```

Run daily via cron:
```cron
0 8 * * * /home/warnertracker/projects/Tracker-Warner/monitor.sh
```

---

## Security Best Practices

### 1. File Permissions

```bash
# Set restrictive permissions on database
chmod 600 tracker.db

# Set proper ownership
chown warnertracker:warnertracker tracker.db

# Protect configuration
chmod 600 config.py
```

### 2. SSH Key Authentication (Cloud Servers)

**Disable password authentication:**

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 3. Firewall Configuration

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow ssh
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 4. Automatic Security Updates (Ubuntu)

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 5. Sensitive Data

**Never commit to Git:**
- `tracker.db`
- `data/` directory
- `.env` files
- Logs with sensitive info

**Verify `.gitignore`:**
```bash
cat .gitignore | grep -E "data/|*.db|*.log"
```

---

## Backup Strategy

### 1. Database Backups

**Automated daily backup script:**

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/warnertracker/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/home/warnertracker/projects/Tracker-Warner/tracker.db"

mkdir -p "$BACKUP_DIR"

# Create backup
cp "$DB_PATH" "$BACKUP_DIR/tracker_$DATE.db"

# Compress
gzip "$BACKUP_DIR/tracker_$DATE.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "tracker_*.db.gz" -mtime +30 -delete

echo "Backup created: tracker_$DATE.db.gz"
```

**Add to crontab (daily at 3 AM):**
```cron
0 3 * * * /home/warnertracker/projects/Tracker-Warner/backup.sh
```

### 2. Configuration Backup

```bash
# Backup entire config
cp config.py config.py.backup

# Or commit to private Git repository
git add config.py
git commit -m "Update configuration"
git push
```

### 3. Remote Backups (Optional)

**Option 1: rsync to another server**

```bash
rsync -avz tracker.db user@backup-server:/backups/
```

**Option 2: AWS S3**

```bash
aws s3 cp tracker.db s3://your-bucket/backups/tracker_$(date +%Y%m%d).db
```

**Option 3: Dropbox/Google Drive**

Use `rclone`:
```bash
rclone copy tracker.db dropbox:/backups/
```

---

## Performance Optimization

### 1. Database Optimization

**Regular maintenance:**

```bash
# Weekly vacuum
sqlite3 tracker.db "VACUUM;"

# Analyze for query optimization
sqlite3 tracker.db "ANALYZE;"
```

**Add to crontab (weekly on Sunday at 4 AM):**
```cron
0 4 * * 0 sqlite3 /home/warnertracker/projects/Tracker-Warner/tracker.db "VACUUM; ANALYZE;"
```

### 2. Parallel Scraping

Modify `scraper_daemon.py` to scrape multiple accounts in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(scrape_account, acc) for acc in accounts]
```

### 3. Caching

Implement caching for yt-dlp results:

```bash
mkdir -p cache/
```

Add to scraper:
```python
cache_file = f"cache/{username}.json"
if os.path.exists(cache_file):
    # Load from cache if recent
    pass
```

---

## Troubleshooting Production Issues

### Issue: Scraper Fails Silently

**Solution:** Check logs

```bash
tail -100 scraper.log
grep ERROR scraper.log
```

### Issue: Database Lock Errors

**Solution:** Ensure only one scraper instance runs

```bash
# Check for multiple processes
ps aux | grep scraper_daemon

# Kill duplicate processes
pkill -f scraper_daemon
```

### Issue: Out of Disk Space

**Solution:** Clean up old files

```bash
# Check disk usage
df -h

# Clean old logs
find . -name "*.log" -mtime +30 -delete

# Clean old backups
find backups/ -name "*.db.gz" -mtime +30 -delete

# Vacuum database
sqlite3 tracker.db "VACUUM;"
```

### Issue: Rate Limited by TikTok

**Solution:** Reduce scraping frequency

```bash
# Increase interval to 48 hours
python3 scraper_daemon.py --interval 48
```

Or reduce accounts per run:
```python
# In scraper_daemon.py, scrape in batches
accounts_batch = accounts[:10]  # Only 10 at a time
```

### Issue: Memory Usage Too High

**Solution:** Optimize processing

```python
# Process videos in batches instead of all at once
for video_batch in chunks(videos, 100):
    process_batch(video_batch)
```

---

## Scaling Considerations

### Current Capacity

| Metric | Limit | Bottleneck |
|--------|-------|------------|
| Accounts | ~50 | yt-dlp rate limits |
| Videos | ~100K | SQLite performance |
| Scrape time | ~1 hour | Sequential processing |
| Database size | ~100MB | Storage |

### Scaling to 100+ Accounts

**1. Parallel Scraping**
- Use ThreadPoolExecutor
- Scrape 3-5 accounts simultaneously

**2. Distributed Scraping**
- Deploy multiple scraper instances
- Partition accounts across instances
- Use shared database or aggregate results

**3. Upgrade to PostgreSQL**
- Better concurrent access
- Advanced indexing
- Replication support

**4. Add Caching Layer**
- Redis for frequently accessed data
- Reduce database queries

### Scaling to 500+ Accounts

**1. Message Queue Architecture**
- Use RabbitMQ or Redis Queue
- Worker pool consumes scraping jobs
- Better fault tolerance

**2. Kubernetes Deployment**
- Auto-scaling based on queue depth
- Easy horizontal scaling

**3. Cloud Functions**
- AWS Lambda for scraping
- S3 for storage
- RDS for database

---

## Maintenance Schedule

### Daily
- [ ] Check scraper logs for errors
- [ ] Verify scraping completed successfully
- [ ] Monitor disk space

### Weekly
- [ ] Review scraping statistics
- [ ] Check database size
- [ ] Vacuum database
- [ ] Review error patterns

### Monthly
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Update yt-dlp (`pip install -U yt-dlp`)
- [ ] Review and archive old data
- [ ] Test backup restoration
- [ ] Review configuration (accounts added/removed?)

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Capacity planning
- [ ] Documentation updates

---

## Rollback Procedure

If something goes wrong:

### 1. Stop the Scraper

```bash
# If using systemd
sudo systemctl stop warner-tracker

# If using cron, disable
crontab -e  # Comment out the cron job

# Kill running processes
pkill -f scraper_daemon
```

### 2. Restore Database Backup

```bash
# Find latest backup
ls -lt backups/

# Restore
gunzip -c backups/tracker_20251110_030000.db.gz > tracker.db
```

### 3. Revert Code Changes

```bash
# Check git log
git log --oneline -10

# Revert to previous commit
git revert <commit-hash>

# Or reset hard (WARNING: loses uncommitted changes)
git reset --hard <commit-hash>
```

### 4. Test Before Resuming

```bash
# Test with single account
python3 scraper_daemon.py --once --accounts @testaccount

# Verify database
python3 init_db.py --info
```

### 5. Resume Operations

```bash
# Restart service
sudo systemctl start warner-tracker

# Or re-enable cron job
crontab -e
```

---

## Monitoring Dashboard (Optional)

### Simple Web Dashboard

Create `dashboard.py`:

```python
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()

    # Get statistics
    cursor.execute('SELECT COUNT(*) FROM accounts WHERE is_active=1')
    active_accounts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM videos')
    total_videos = cursor.fetchone()[0]

    cursor.execute('''
        SELECT session_id, start_time, status
        FROM scrape_sessions
        ORDER BY start_time DESC
        LIMIT 10
    ''')
    recent_sessions = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html',
                          active_accounts=active_accounts,
                          total_videos=total_videos,
                          recent_sessions=recent_sessions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run:
```bash
pip install flask
python3 dashboard.py
```

Access at `http://your-server-ip:5000`

---

## CI/CD Integration (Advanced)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Warner Tracker

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/warnertracker/projects/Tracker-Warner
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart warner-tracker
```

---

## Summary Checklist

- [ ] Server provisioned and secured
- [ ] All dependencies installed
- [ ] Project cloned from GitHub
- [ ] Virtual environment created
- [ ] Configuration populated
- [ ] Database initialized
- [ ] Test scraping successful
- [ ] Automation configured (cron/systemd)
- [ ] Backups automated
- [ ] Monitoring set up
- [ ] Log rotation configured
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## Support & Resources

### Documentation
- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure
- [CRON_SETUP.md](CRON_SETUP.md) - Automation setup
- [TRACKER_DOCUMENTATION.md](TRACKER_DOCUMENTATION.md) - Technical docs

### External Resources
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Cron Tutorial](https://crontab.guru/)

### GitHub Repository
- **URL:** https://github.com/Risingtides-dev/Tracker-Warner
- **Issues:** Report bugs and request features
- **Wiki:** Additional documentation and guides

---

**Last Updated:** November 2025
**Version:** 1.0
