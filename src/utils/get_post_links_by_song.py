#!/usr/bin/env python3
"""
Get post links for last 36 hours from accounts and compile by song
"""

import sys
import subprocess
import json
import re
import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


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

def scrape_account_videos(account, start_datetime=None, end_datetime=None, limit=500):
    """Scrape videos from a TikTok account and filter by datetime range"""
    username = get_profile_username(account)
    if not username:
        print(f"  [ERROR] Could not extract username from: {account}")
        return []
    
    profile_url = build_profile_url(username)
    print(f"  Scraping @{username}...")
    
    # Use yt-dlp to get video metadata
    import sys
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
                
                # Determine posted datetime - try multiple methods
                video_dt = None
                
                # Method 1: Use timestamp (most accurate)
                timestamp = video_data.get('timestamp')
                if timestamp:
                    try:
                        video_dt = datetime.fromtimestamp(timestamp)
                    except (ValueError, OSError):
                        pass
                
                # Method 2: Use upload_date (YYYYMMDD format)
                if not video_dt:
                    upload_date = video_data.get('upload_date')
                    if upload_date:
                        try:
                            video_dt = datetime.strptime(upload_date, '%Y%m%d')
                        except ValueError:
                            pass
                
                # Filter by datetime range if provided
                if video_dt:
                    if start_datetime and video_dt < start_datetime:
                        skipped_old += 1
                        continue
                    if end_datetime and video_dt > end_datetime:
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
        
        date_info = ""
        if start_datetime and end_datetime:
            date_info = f" (window: {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')})"
        elif start_datetime:
            date_info = f" (after {start_datetime.strftime('%Y-%m-%d %H:%M')})"
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
    parser = argparse.ArgumentParser(
        description='Get post links for TikTok accounts and compile by song',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: last 36 hours
  python get_post_links_by_song.py
  
  # Custom date range
  python get_post_links_by_song.py --start-datetime "2024-11-26 05:00" --end-datetime "2024-11-27 12:00"
  
  # From specific date/time to now
  python get_post_links_by_song.py --start-datetime "2024-11-26 05:00"
        """
    )
    parser.add_argument('--start-datetime', 
                       help='Start datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS). Default: 36 hours ago')
    parser.add_argument('--end-datetime',
                       help='End datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS). Default: now')
    parser.add_argument('accounts', nargs='*',
                       help='TikTok account usernames (without @). If not provided, uses default internal accounts list')
    
    args = parser.parse_args()
    
    # Get accounts from command line or use default list
    if args.accounts:
        accounts = args.accounts
    else:
        # Default account list
        accounts = [
            'brew.pilled',
            'trailheadtravis',
            'earl.boone1',
            'dirtroad.drivin',
            'gusjohnson_quotes',
            'backroaddriver',
            'coffeesentiments',
            'boone.reynolds',
            'buck.wilders',
            'coffee.yearnings',
            'dearest.arthur',
            'quinnbmovin',
            'humans.are.awesome',
            'sopranosyndrome',
            'hookedupfishing61',
            'dieselmechanic4life',
            'dallasramsey5.3',
            'cash.culpepper',
            'coffee.healing.peace',
            'ghostofarthurmorgan',
            'southpawoutlaw1',
            'dale.yearnhardt',
            'baker.mansfield',
            'geoff.gordon24',
            'lucki6.7',
            'yearnest.hemingway',
            'pardon.the.yearn',
            'pinkfonthalfspeed',
            'ericcromartie',
            'yellowfont.halfspeed',

        ]
    
    if not accounts:
        print("ERROR: No accounts specified.")
        sys.exit(1)
    
    # Parse datetime arguments
    end_datetime = datetime.now()
    start_datetime = None
    
    if args.end_datetime:
        try:
            # Try with seconds first
            try:
                end_datetime = datetime.strptime(args.end_datetime, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try without seconds
                end_datetime = datetime.strptime(args.end_datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            print(f"ERROR: Invalid end-datetime format: {args.end_datetime}")
            print("Expected format: YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    if args.start_datetime:
        try:
            # Try with seconds first
            try:
                start_datetime = datetime.strptime(args.start_datetime, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try without seconds
                start_datetime = datetime.strptime(args.start_datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            print(f"ERROR: Invalid start-datetime format: {args.start_datetime}")
            print("Expected format: YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    else:
        # Default: last 36 hours
        start_datetime = end_datetime - timedelta(hours=36)
    
    print("=" * 80)
    print("GETTING POST LINKS BY SONG")
    print("=" * 80)
    print(f"\nProcessing {len(accounts)} accounts...")
    print(f"Collecting posts from {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}\n")
    
    all_videos = []
    
    # Scrape each account
    for account in accounts:
        videos = scrape_account_videos(account, start_datetime=start_datetime, end_datetime=end_datetime, limit=500)
        all_videos.extend(videos)
    
    print(f"\nTotal videos collected within window: {len(all_videos)}")
    
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
        # Handle encoding errors for special characters
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
        
        # Sort videos by views (descending)
        sorted_videos = sorted(data['videos'], key=lambda x: x['views'], reverse=True)
        
        for i, video in enumerate(sorted_videos, 1):
            print(f"  {i}. {video['url']}")
            print(f"     Account: {video['account']} | Views: {video['views']:,} | Likes: {video['likes']:,}")
    
    # Save to file (detailed version)
    output_file = Path('output') / 'post_links_by_song.txt'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("POST LINKS GROUPED BY SONG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Accounts processed: {len(accounts)}\n")
        f.write(f"Total videos: {len(all_videos)}\n")
        f.write(f"Unique songs: {len(songs_dict)}\n\n")
        
        for song_key, data in sorted_songs:
            f.write(f"\n{'=' * 80}\n")
            # Handle encoding for file writing
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
    
    # Save copy-paste friendly version (just links, one per line per song)
    copy_paste_file = Path('output') / 'post_links_copy_paste.txt'
    
    with open(copy_paste_file, 'w', encoding='utf-8') as f:
        f.write("POST LINKS - COPY/PASTE FORMAT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Time window: {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Accounts processed: {len(accounts)}\n")
        f.write(f"Total videos: {len(all_videos)}\n")
        f.write(f"Unique songs: {len(songs_dict)}\n\n")
        f.write("=" * 80 + "\n\n")
        
        for song_key, data in sorted_songs:
            # Handle encoding for file writing
            song_safe = data['song'].encode('utf-8', errors='replace').decode('utf-8')
            artist_safe = data['artist'].encode('utf-8', errors='replace').decode('utf-8')
            
            f.write(f"\n{'=' * 80}\n")
            f.write(f"SONG: {song_safe} - {artist_safe}\n")
            f.write(f"Total Uses: {len(data['videos'])} | Total Views: {data['total_views']:,}\n")
            f.write(f"{'=' * 80}\n\n")
            
            # Just the links, one per line
            sorted_videos = sorted(data['videos'], key=lambda x: x['views'], reverse=True)
            for video in sorted_videos:
                f.write(f"{video['url']}\n")
            
            f.write("\n")  # Blank line between songs
    
    print(f"\n{'=' * 80}")
    print(f"[SUCCESS] Results saved to:")
    print(f"  Detailed: {output_file}")
    print(f"  Copy/Paste: {copy_paste_file}")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()

