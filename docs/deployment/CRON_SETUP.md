# Warner Sound Tracker - Automated Scraping Setup

## Overview

This guide explains how to set up automated, scheduled scraping for the Warner Sound Tracker using cron jobs (macOS/Linux) or Task Scheduler (Windows). The scraper will run automatically at configured intervals to keep your data up-to-date.

## Prerequisites

Before setting up automated scraping:

1. ✅ Database initialized (`python3 init_db.py`)
2. ✅ Configuration populated (`config.py`)
3. ✅ Virtual environment created and dependencies installed
4. ✅ `scraper_daemon.py` tested manually
5. ✅ `yt-dlp` installed and accessible

## Option 1: Cron Jobs (macOS/Linux) - Recommended

### What is Cron?

Cron is a time-based job scheduler in Unix-like operating systems. It allows you to run scripts automatically at specified times/intervals.

### Step 1: Test Manual Execution

First, ensure the scraper works when run manually:

```bash
cd /path/to/warnertracker
source venv/bin/activate
python3 scraper_daemon.py --once
```

If this works successfully, you're ready to automate it.

### Step 2: Create a Wrapper Script

Create a wrapper script that handles the virtual environment activation:

**File: `run_scraper.sh`**

```bash
#!/bin/bash

# Warner Sound Tracker - Cron Wrapper Script
# This script activates the virtual environment and runs the scraper

# Set working directory (CHANGE THIS to your actual path)
PROJECT_DIR="/Users/yourname/path/to/warnertracker"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source venv/bin/activate

# Run scraper (--once flag for single run)
python3 scraper_daemon.py --once

# Exit with scraper's exit code
exit $?
```

### Step 3: Make Script Executable

```bash
chmod +x run_scraper.sh
```

### Step 4: Test the Wrapper Script

```bash
./run_scraper.sh
```

Verify that it runs successfully and check the log file:

```bash
tail -f scraper.log
```

### Step 5: Edit Crontab

Open your crontab for editing:

```bash
crontab -e
```

This will open your crontab in your default editor (usually vim or nano).

### Step 6: Add Cron Job Entry

Add one of the following entries based on your desired schedule:

#### Run Every 24 Hours (Daily at 2:00 AM)

```cron
0 2 * * * /Users/yourname/path/to/warnertracker/run_scraper.sh >> /Users/yourname/path/to/warnertracker/cron.log 2>&1
```

#### Run Every 12 Hours (2:00 AM and 2:00 PM)

```cron
0 2,14 * * * /Users/yourname/path/to/warnertracker/run_scraper.sh >> /Users/yourname/path/to/warnertracker/cron.log 2>&1
```

#### Run Every 6 Hours

```cron
0 */6 * * * /Users/yourname/path/to/warnertracker/run_scraper.sh >> /Users/yourname/path/to/warnertracker/cron.log 2>&1
```

#### Run Every Monday at 9:00 AM

```cron
0 9 * * 1 /Users/yourname/path/to/warnertracker/run_scraper.sh >> /Users/yourname/path/to/warnertracker/cron.log 2>&1
```

### Cron Schedule Format

```
* * * * * command to execute
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 and 7 are Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Step 7: Save and Exit

- **Vim**: Press `Esc`, type `:wq`, press `Enter`
- **Nano**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 8: Verify Cron Job

List your cron jobs to verify:

```bash
crontab -l
```

### Step 9: Monitor Execution

Check the cron log file to see output:

```bash
tail -f cron.log
```

Check the scraper log for detailed information:

```bash
tail -f scraper.log
```

### Step 10: macOS Specific - Grant Full Disk Access

On macOS, cron may need Full Disk Access permission:

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access**
3. Click the lock icon to make changes
4. Add `/usr/sbin/cron` to the allowed list

---

## Option 2: Daemon Mode (Run Continuously)

Instead of cron, you can run the scraper as a persistent daemon:

### Step 1: Create a Launch Agent (macOS)

**File: `~/Library/LaunchAgents/com.warner.tracker.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.warner.tracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourname/path/to/warnertracker/venv/bin/python3</string>
        <string>/Users/yourname/path/to/warnertracker/scraper_daemon.py</string>
        <string>--interval</string>
        <string>24</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/yourname/path/to/warnertracker</string>

    <key>StandardOutPath</key>
    <string>/Users/yourname/path/to/warnertracker/daemon.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/yourname/path/to/warnertracker/daemon.error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### Step 2: Load the Launch Agent

```bash
launchctl load ~/Library/LaunchAgents/com.warner.tracker.plist
```

### Step 3: Start the Service

```bash
launchctl start com.warner.tracker
```

### Step 4: Check Status

```bash
launchctl list | grep warner
```

### Step 5: View Logs

```bash
tail -f ~/path/to/warnertracker/daemon.log
```

### Managing the Service

**Stop:**
```bash
launchctl stop com.warner.tracker
```

**Unload:**
```bash
launchctl unload ~/Library/LaunchAgents/com.warner.tracker.plist
```

**Restart:**
```bash
launchctl stop com.warner.tracker
launchctl start com.warner.tracker
```

---

## Option 3: Systemd Service (Linux)

### Step 1: Create Service File

**File: `/etc/systemd/system/warner-tracker.service`**

```ini
[Unit]
Description=Warner Sound Tracker Scraper
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/warnertracker
ExecStart=/home/youruser/warnertracker/venv/bin/python3 /home/youruser/warnertracker/scraper_daemon.py --interval 24
Restart=on-failure
RestartSec=60
StandardOutput=append:/home/youruser/warnertracker/daemon.log
StandardError=append:/home/youruser/warnertracker/daemon.error.log

[Install]
WantedBy=multi-user.target
```

### Step 2: Reload Systemd

```bash
sudo systemctl daemon-reload
```

### Step 3: Enable and Start Service

```bash
sudo systemctl enable warner-tracker
sudo systemctl start warner-tracker
```

### Step 4: Check Status

```bash
sudo systemctl status warner-tracker
```

### Managing the Service

**Stop:**
```bash
sudo systemctl stop warner-tracker
```

**Restart:**
```bash
sudo systemctl restart warner-tracker
```

**View Logs:**
```bash
sudo journalctl -u warner-tracker -f
```

**Disable Auto-start:**
```bash
sudo systemctl disable warner-tracker
```

---

## Option 4: Task Scheduler (Windows)

### Step 1: Create a Batch Script

**File: `run_scraper.bat`**

```batch
@echo off
REM Warner Sound Tracker - Windows Batch Script

REM Change to project directory
cd /d "C:\Users\YourName\path\to\warnertracker"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run scraper
python scraper_daemon.py --once

REM Exit with scraper's exit code
exit /b %ERRORLEVEL%
```

### Step 2: Test the Batch Script

Double-click `run_scraper.bat` to test it works.

### Step 3: Open Task Scheduler

1. Press `Win+R`
2. Type `taskschd.msc`
3. Press `Enter`

### Step 4: Create a New Task

1. Click **Create Basic Task** in the right panel
2. Name: `Warner Sound Tracker`
3. Description: `Automated TikTok scraping for Warner accounts`
4. Click **Next**

### Step 5: Configure Trigger

Choose one:
- **Daily** - Runs once per day at specified time
- **Weekly** - Runs on specific days of the week
- **Monthly** - Runs on specific days of the month

Configure your preferred schedule and click **Next**.

### Step 6: Configure Action

1. Select **Start a program**
2. Click **Next**
3. **Program/script:** Browse to `run_scraper.bat`
4. **Start in:** `C:\Users\YourName\path\to\warnertracker`
5. Click **Next**

### Step 7: Additional Settings

1. Click **Finish**
2. Right-click the task and select **Properties**
3. Under **General** tab:
   - Check **Run whether user is logged on or not**
   - Check **Run with highest privileges**
4. Under **Conditions** tab:
   - Uncheck **Start the task only if the computer is on AC power**
5. Click **OK**

### Step 8: Test the Task

Right-click the task and select **Run** to test it immediately.

### Step 9: View Task History

1. Right-click the task
2. Select **Properties**
3. Click the **History** tab to see execution logs

---

## Monitoring and Maintenance

### Check Scraper Logs

```bash
# View entire log
cat scraper.log

# View last 50 lines
tail -50 scraper.log

# Follow log in real-time
tail -f scraper.log

# Search for errors
grep ERROR scraper.log

# View successful scrapes
grep "✅" scraper.log
```

### Check Database Status

```bash
python3 init_db.py --info
```

### Query Recent Scrape Sessions

```bash
sqlite3 tracker.db "
SELECT
    session_id,
    start_time,
    status,
    successful_scrapes,
    failed_scrapes,
    total_new_videos
FROM scrape_sessions
ORDER BY start_time DESC
LIMIT 10;
"
```

### Check Last Scrape Times

```bash
sqlite3 tracker.db "
SELECT username, last_scraped_at, scrape_count
FROM accounts
WHERE is_active = 1
ORDER BY last_scraped_at DESC;
"
```

---

## Troubleshooting

### Cron Job Not Running

**Check cron service is running:**
```bash
# macOS
sudo launchctl list | grep cron

# Linux
systemctl status cron
```

**Check cron logs:**
```bash
# macOS
tail -f /var/log/system.log | grep cron

# Linux
grep CRON /var/log/syslog
```

**Verify script permissions:**
```bash
ls -la run_scraper.sh
# Should show: -rwxr-xr-x (executable)
```

### "Command not found" Errors

**Issue:** Cron has a limited PATH

**Solution:** Use absolute paths in your script:
```bash
#!/bin/bash
/usr/local/bin/python3 /full/path/to/scraper_daemon.py --once
```

### Virtual Environment Not Activating

**Issue:** Script can't find venv

**Solution:** Use absolute path:
```bash
source /full/path/to/warnertracker/venv/bin/activate
```

### Permission Denied Errors

**Issue:** Cron user doesn't have permissions

**Solution:** Check file ownership:
```bash
ls -la scraper_daemon.py
chown youruser:yourgroup scraper_daemon.py
chmod 755 scraper_daemon.py
```

### Database Lock Errors

**Issue:** Multiple scraper instances running

**Solution:** Use a lock file:
```bash
#!/bin/bash
LOCKFILE="/tmp/warner_scraper.lock"

if [ -e "$LOCKFILE" ]; then
    echo "Scraper already running"
    exit 1
fi

touch "$LOCKFILE"
python3 scraper_daemon.py --once
rm "$LOCKFILE"
```

### Scraper Crashes or Fails

**Check error logs:**
```bash
tail -100 scraper.log | grep -A 5 ERROR
```

**Test manually:**
```bash
python3 scraper_daemon.py --once --verbose --accounts @testaccount
```

---

## Email Notifications (Optional)

### Option 1: Using `mail` Command (Linux/macOS)

Add to your cron wrapper script:

```bash
#!/bin/bash

# Run scraper
python3 scraper_daemon.py --once > /tmp/scraper_output.txt 2>&1

# Check exit code
if [ $? -ne 0 ]; then
    # Send email on failure
    cat /tmp/scraper_output.txt | mail -s "Warner Tracker: Scrape Failed" your@email.com
fi
```

### Option 2: Using Python Script

Create `notify.py`:

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'tracker@yourcompany.com'
    msg['To'] = 'your@email.com'

    # Configure your SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your@email.com', 'your-app-password')
    server.send_message(msg)
    server.quit()

if __name__ == '__main__':
    import sys
    send_notification(sys.argv[1], sys.argv[2])
```

Call from wrapper:
```bash
python3 notify.py "Scrape Complete" "$(tail -20 scraper.log)"
```

---

## Best Practices

### 1. Start with Longer Intervals

Begin with 24-hour intervals and adjust based on:
- How frequently accounts post
- TikTok rate limiting
- Server resources

### 2. Monitor for Rate Limiting

If you see increased failures:
- Increase scrape interval
- Reduce accounts per run
- Add delays between accounts

### 3. Regular Database Maintenance

```bash
# Weekly: Vacuum database
sqlite3 tracker.db "VACUUM;"

# Monthly: Backup database
cp tracker.db "backups/tracker_$(date +%Y%m%d).db"
```

### 4. Log Rotation

Prevent log files from growing indefinitely:

**Using `logrotate` (Linux):**

Create `/etc/logrotate.d/warner-tracker`:
```
/home/youruser/warnertracker/*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

**Manual rotation:**
```bash
# In your wrapper script
LOG_FILE="scraper.log"
if [ $(stat -f%z "$LOG_FILE") -gt 10485760 ]; then
    mv "$LOG_FILE" "$LOG_FILE.old"
fi
```

### 5. Health Checks

Create a monitoring script that checks:
- Last successful scrape time
- Database size
- Disk space
- Error rate

Run daily and alert if issues found.

---

## Performance Tuning

### Reduce Scrape Time

**Use specific accounts instead of all:**
```bash
python3 scraper_daemon.py --once --accounts @account1,@account2
```

**Reduce video limit per account:**
Modify in `scraper_daemon.py`:
```python
'--limit', '50',  # Instead of 100
```

### Parallel Scraping (Advanced)

Modify `scraper_daemon.py` to use threading:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(self.scrape_account, acc) for acc in accounts]
```

---

## Summary Checklist

- [ ] Tested scraper manually
- [ ] Created wrapper script (`run_scraper.sh` or `run_scraper.bat`)
- [ ] Made wrapper executable (`chmod +x`)
- [ ] Set up cron job / Task Scheduler / systemd service
- [ ] Verified cron runs successfully
- [ ] Configured log rotation
- [ ] Set up monitoring/notifications (optional)
- [ ] Documented schedule and configuration

---

## Quick Reference

### Cron Syntax

```bash
# Every day at 2 AM
0 2 * * *

# Every 12 hours
0 */12 * * *

# Every Monday at 9 AM
0 9 * * 1

# Every 6 hours
0 */6 * * *
```

### Common Commands

```bash
# Edit crontab
crontab -e

# List crontabs
crontab -l

# View scraper log
tail -f scraper.log

# Test scraper
python3 scraper_daemon.py --once --verbose

# Check database
python3 init_db.py --info
```

---

## Related Documentation

- [README.md](README.md) - Project overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [TRACKER_DOCUMENTATION.md](TRACKER_DOCUMENTATION.md) - Technical documentation
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure

---

**Last Updated:** November 2025
