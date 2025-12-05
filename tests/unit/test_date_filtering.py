#!/usr/bin/env python3
"""Test script to check date filtering logic"""

from datetime import datetime, timedelta
import subprocess
import json
import sys

# Test with one account to see what dates we're getting
account = "@dirtroad.drivin"
profile_url = f"https://www.tiktok.com/{account}"

# Get time window
hours_window = 24
cutoff_time = datetime.utcnow() - timedelta(hours=hours_window)

print(f"Cutoff time: {cutoff_time}")
print(f"Current time: {datetime.utcnow()}")
print(f"Time window: {hours_window} hours")
print()

# Fetch videos
cmd = [sys.executable, '-m', 'yt_dlp', '--flat-playlist', '--dump-json', '--playlist-end', '20', profile_url]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

if result.returncode != 0:
    print(f"Error: {result.stderr[:200]}")
    sys.exit(1)

print("Recent videos from @dirtroad.drivin:")
print("=" * 80)

videos_in_window = []
videos_outside = []

for line in result.stdout.strip().split('\n'):
    if not line:
        continue
    try:
        video_data = json.loads(line)
        
        video_dt = None
        timestamp = video_data.get('timestamp')
        upload_date = video_data.get('upload_date')
        
        if timestamp:
            video_dt = datetime.fromtimestamp(timestamp)
        elif upload_date:
            try:
                video_dt = datetime.strptime(upload_date, '%Y%m%d')
                video_dt = video_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
        
        video_url = video_data.get('webpage_url', '')
        track = video_data.get('track', 'Unknown')
        
        if video_dt:
            status = "IN WINDOW" if video_dt >= cutoff_time else "TOO OLD"
            print(f"{status}: {video_dt} | {track[:40]}")
            print(f"  URL: {video_url}")
            
            if video_dt >= cutoff_time:
                videos_in_window.append(video_data)
            else:
                videos_outside.append(video_data)
        else:
            print(f"NO DATE: {track[:40]}")
            print(f"  URL: {video_url}")
            print(f"  upload_date: {upload_date}, timestamp: {timestamp}")
    
    except json.JSONDecodeError:
        continue

print()
print("=" * 80)
print(f"Videos IN window: {len(videos_in_window)}")
print(f"Videos OUTSIDE window: {len(videos_outside)}")

