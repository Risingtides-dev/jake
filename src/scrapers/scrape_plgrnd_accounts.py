#!/usr/bin/env python3
"""
Scrape PLGRND accounts since November 12th, 2025.
Shows all videos grouped by song.
"""

import sys
import subprocess
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Warner campaign accounts
WARNER_ACCOUNTS = [
    'beaujenkins',
    'codyjames6.7',
    'coffeesentiments',
    'gavin.wilder1',
    'smoked.999',
]

# PLGRND (Playground) campaign accounts
PLGRND_ACCOUNTS = [
    'chillkyle32',
    'lovelatenightdrives',
    'coffeemusicsoul',
    'coffee.with.her',
    'steves.dreams',
    'radio_kart',
]

def get_profile_username(url_or_username):
    """Extract username from TikTok profile URL or handle"""
    if not url_or_username.startswith('http'):
        username = url_or_username.lstrip('@')
        return username
    match = re.search(r'@([\w\.]+)', url_or_username)
    if match:
        return match.group(1)
    return None

def build_profile_url(username):
    """Build TikTok profile URL from username"""
    return f"https://www.tiktok.com/@{username}"

def scrape_account_videos(account, start_datetime=None, limit=500):
    """Scrape videos from a TikTok account and filter by datetime range"""
    username = get_profile_username(account)
    if not username:
        print(f"  [ERROR] Could not extract username from: {account}")
        return []
    
    profile_url = build_profile_url(username)
    print(f"  Scraping @{username}...")
    
    # Use yt-dlp to get video metadata
    import shutil
    
    yt_dlp_cmd = 'yt-dlp'
    if not shutil.which('yt-dlp'):
        yt_dlp_cmd = [sys.executable, '-m', 'yt_dlp']
    
    cmd = [
        yt_dlp_cmd if isinstance(yt_dlp_cmd, str) else yt_dlp_cmd[0],
        '--flat-playlist',
        '--dump-json',
        '--playlist-end', str(limit),
        profile_url
    ]
    
    if not isinstance(yt_dlp_cmd, str):
        cmd = [sys.executable, '-m', 'yt_dlp'] + cmd[1:]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"    [ERROR] Failed to scrape: {result.stderr[:200]}")
            return []
        
        videos = []
        total_fetched = 0
        skipped_old = 0
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                video_data = json.loads(line)
                total_fetched += 1
                
                # Extract song info
                track = video_data.get('track', '') or 'Unknown'
                artist = video_data.get('artist', '') or (video_data.get('artists', [])[0] if video_data.get('artists') else 'Unknown')
                
                # Get video URL
                video_url = video_data.get('webpage_url') or video_data.get('url', '')
                
                if not video_url:
                    continue
                
                # Determine posted datetime
                video_dt = None
                timestamp = video_data.get('timestamp')
                if timestamp:
                    try:
                        video_dt = datetime.fromtimestamp(timestamp)
                    except (ValueError, OSError):
                        pass
                
                if not video_dt:
                    upload_date = video_data.get('upload_date')
                    if upload_date:
                        try:
                            video_dt = datetime.strptime(upload_date, '%Y%m%d')
                        except ValueError:
                            pass
                
                # Filter by start date if provided
                if start_datetime and video_dt:
                    if video_dt.date() < start_datetime:
                        skipped_old += 1
                        continue
                
                videos.append({
                    'url': video_url,
                    'song': track,
                    'artist': artist,
                    'account': f"@{username}",
                    'views': video_data.get('view_count', 0),
                    'likes': video_data.get('like_count', 0),
                    'upload_date': video_data.get('upload_date', ''),
                    'timestamp': video_dt
                })
            except json.JSONDecodeError:
                continue
        
        date_info = f" (after {start_datetime})" if start_datetime else ""
        print(f"    Fetched {total_fetched} posts | {len(videos)} within window{date_info} | {skipped_old} too old")
        return videos
        
    except subprocess.TimeoutExpired:
        print(f"    [ERROR] Timeout scraping @{username}")
        return []
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []

def normalize_song_key(song, artist):
    """Create normalized song key for grouping"""
    song_clean = song.strip() if song else 'Unknown'
    artist_clean = artist.strip() if artist else 'Unknown'
    return f"{song_clean} - {artist_clean}"

def main():
    # Start date: November 12th, 2025
    start_date = datetime(2025, 11, 12).date()
    
    print("=" * 80)
    print("PLGRND (PLAYGROUND) ACCOUNTS SCRAPE - SINCE NOVEMBER 12, 2025")
    print("=" * 80)
    print(f"\nScraping {len(PLGRND_ACCOUNTS)} PLGRND accounts...")
    print(f"Start date: {start_date}\n")
    
    all_videos = []
    
    # Scrape each account
    for account in PLGRND_ACCOUNTS:
        videos = scrape_account_videos(account, start_datetime=start_date, limit=500)
        all_videos.extend(videos)
    
    print(f"\nTotal videos collected since {start_date}: {len(all_videos)}")
    
    # Group by song
    songs_dict = defaultdict(lambda: {
        'song': '',
        'artist': '',
        'videos': [],
        'accounts': set(),
        'total_views': 0,
        'total_likes': 0
    })
    
    for video in all_videos:
        song_key = normalize_song_key(video['song'], video['artist'])
        songs_dict[song_key]['song'] = video['song']
        songs_dict[song_key]['artist'] = video['artist']
        songs_dict[song_key]['videos'].append(video)
        songs_dict[song_key]['accounts'].add(video['account'])
        songs_dict[song_key]['total_views'] += video['views']
        songs_dict[song_key]['total_likes'] += video['likes']
    
    # Sort songs by total views (descending)
    sorted_songs = sorted(songs_dict.items(), key=lambda x: x[1]['total_views'], reverse=True)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS GROUPED BY SONG")
    print("=" * 80)
    
    for song_key, data in sorted_songs:
        print(f"\n{'=' * 80}")
        try:
            print(f"SONG: {data['song']}")
            print(f"ARTIST: {data['artist']}")
        except UnicodeEncodeError:
            print(f"SONG: {data['song'].encode('ascii', 'ignore').decode('ascii')}")
            print(f"ARTIST: {data['artist'].encode('ascii', 'ignore').decode('ascii')}")
        print(f"Total Uses: {len(data['videos'])}")
        print(f"Accounts: {', '.join(sorted(data['accounts']))}")
        print(f"Total Views: {data['total_views']:,}")
        print(f"Total Likes: {data['total_likes']:,}")
        print(f"\nPost Links ({len(data['videos'])} videos):")
        print("-" * 80)
        
        sorted_videos = sorted(data['videos'], key=lambda x: x['views'], reverse=True)
        for i, video in enumerate(sorted_videos, 1):
            print(f"  {i}. {video['url']}")
            print(f"     Account: {video['account']} | Views: {video['views']:,} | Likes: {video['likes']:,}")
    
    # Save to file
    output_file = Path('output') / 'plgrnd_accounts_since_nov12.txt'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PLGRND (PLAYGROUND) ACCOUNTS - POST LINKS GROUPED BY SONG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Start Date: {start_date}\n")
        f.write(f"Accounts processed: {len(PLGRND_ACCOUNTS)}\n")
        f.write(f"Total videos: {len(all_videos)}\n")
        f.write(f"Unique songs: {len(songs_dict)}\n\n")
        
        for song_key, data in sorted_songs:
            f.write(f"\n{'=' * 80}\n")
            song_safe = data['song'].encode('utf-8', errors='replace').decode('utf-8')
            artist_safe = data['artist'].encode('utf-8', errors='replace').decode('utf-8')
            f.write(f"SONG: {song_safe}\n")
            f.write(f"ARTIST: {artist_safe}\n")
            f.write(f"Total Uses: {len(data['videos'])}\n")
            f.write(f"Accounts: {', '.join(sorted(data['accounts']))}\n")
            f.write(f"Total Views: {data['total_views']:,}\n")
            f.write(f"Total Likes: {data['total_likes']:,}\n")
            f.write(f"\nPost Links ({len(data['videos'])} videos):\n")
            f.write("-" * 80 + "\n")
            
            sorted_videos = sorted(data['videos'], key=lambda x: x['views'], reverse=True)
            for i, video in enumerate(sorted_videos, 1):
                f.write(f"  {i}. {video['url']}\n")
                f.write(f"     Account: {video['account']} | Views: {video['views']:,} | Likes: {video['likes']:,}\n")
    
    # Copy-paste version
    copy_paste_file = Path('output') / 'plgrnd_accounts_since_nov12_copy_paste.txt'
    
    with open(copy_paste_file, 'w', encoding='utf-8') as f:
        f.write("PLGRND (PLAYGROUND) ACCOUNTS - COPY/PASTE FORMAT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Start Date: {start_date}\n")
        f.write(f"Accounts: {', '.join(PLGRND_ACCOUNTS)}\n")
        f.write(f"Total videos: {len(all_videos)}\n")
        f.write(f"Unique songs: {len(songs_dict)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for song_key, data in sorted_songs:
            song_safe = data['song'].encode('utf-8', errors='replace').decode('utf-8')
            artist_safe = data['artist'].encode('utf-8', errors='replace').decode('utf-8')
            
            f.write(f"SONG: {song_safe} - {artist_safe}\n")
            f.write(f"Total Uses: {len(data['videos'])} | Total Views: {data['total_views']:,}\n")
            f.write("=" * 80 + "\n\n")
            
            sorted_videos = sorted(data['videos'], key=lambda x: x['views'], reverse=True)
            for video in sorted_videos:
                f.write(f"{video['url']}\n")
            f.write("\n")
    
    print(f"\n{'=' * 80}")
    print(f"[SUCCESS] Results saved to:")
    print(f"  Detailed: {output_file}")
    print(f"  Copy/Paste: {copy_paste_file}")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()

