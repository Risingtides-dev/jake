#!/usr/bin/env python3
"""
Find songs used exclusively by specific accounts
"""

import sys
import subprocess
import json
from collections import defaultdict
from datetime import datetime

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Use accounts from config
TARGET_ACCOUNTS = config.TARGET_ACCOUNTS
ACCOUNTS = config.ACCOUNTS

def scrape_account(account, limit=100):
    """Scrape a single TikTok account using yt-dlp"""
    profile_url = f"https://www.tiktok.com/{account}"

    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--dump-json',
        '--playlist-end', str(limit),
        profile_url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return []

    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                video_data = json.loads(line)

                # Filter for configured year and month
                upload_date = video_data.get('upload_date', '')
                if upload_date:
                    try:
                        upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                        if (upload_datetime.year != config.EXCLUSIVE_SONGS_YEAR or 
                            upload_datetime.month != config.EXCLUSIVE_SONGS_MONTH):
                            continue
                    except:
                        continue

                song_title = video_data.get('track', '') or 'Unknown'
                song_artist = video_data.get('artist', '') or video_data.get('creator', '') or 'Unknown'
                sound_key = f"{song_title} - {song_artist}"

                videos.append({
                    'account': account,
                    'sound_key': sound_key,
                    'song_title': song_title,
                    'song_artist': song_artist
                })

            except json.JSONDecodeError:
                continue

    return videos

def main():
    if not ACCOUNTS:
        print("ERROR: No accounts configured. Please add accounts to config.ACCOUNTS")
        return
    
    if not TARGET_ACCOUNTS:
        print("ERROR: No target accounts configured. Please add target accounts to config.TARGET_ACCOUNTS")
        return

    print("Analyzing song usage across all accounts...")
    print("Looking for songs used EXCLUSIVELY by:")
    for acc in sorted(TARGET_ACCOUNTS):
        print(f"  - {acc}")
    print("\n" + "="*80 + "\n")

    # Collect all videos
    all_videos = []
    for account in ACCOUNTS:
        print(f"Scraping {account}...", end=" ")
        videos = scrape_account(account, limit=config.DEFAULT_VIDEO_LIMIT)
        all_videos.extend(videos)
        print(f"{len(videos)} videos")

    print(f"\nTotal videos collected: {len(all_videos)}")
    print("\n" + "="*80 + "\n")

    # Build a map of sound -> set of accounts using it
    sound_usage = defaultdict(set)
    sound_info = {}  # Store song title and artist for each sound_key

    for video in all_videos:
        sound_key = video['sound_key']
        account = video['account']
        sound_usage[sound_key].add(account)
        sound_info[sound_key] = {
            'title': video['song_title'],
            'artist': video['song_artist']
        }

    # Find songs used ONLY by target accounts
    exclusive_sounds = []

    for sound_key, accounts_using in sound_usage.items():
        # Check if ALL accounts using this sound are in TARGET_ACCOUNTS
        if accounts_using and accounts_using.issubset(TARGET_ACCOUNTS):
            exclusive_sounds.append({
                'sound_key': sound_key,
                'title': sound_info[sound_key]['title'],
                'artist': sound_info[sound_key]['artist'],
                'accounts': sorted(list(accounts_using))
            })

    # Sort by number of target accounts using it, then alphabetically
    exclusive_sounds.sort(key=lambda x: (len(x['accounts']), x['title']))

    # Display results
    print("SONGS USED EXCLUSIVELY BY TARGET ACCOUNTS")
    print("="*80)
    target_accounts_str = ', '.join(sorted(TARGET_ACCOUNTS))
    print(f"\nFound {len(exclusive_sounds)} songs used ONLY by: {target_accounts_str}\n")

    if not exclusive_sounds:
        print("No exclusive songs found!")
        return

    for i, song in enumerate(exclusive_sounds, 1):
        print(f"#{i}")
        print(f"  Song:   {song['title']}")
        print(f"  Artist: {song['artist']}")
        print(f"  Used by: {', '.join(song['accounts'])}")
        print()

    # Summary
    print("="*80)
    print(f"\nSUMMARY:")
    print(f"  Total songs analyzed: {len(sound_usage)}")
    print(f"  Exclusive to target accounts: {len(exclusive_sounds)}")
    print(f"  Songs to keep (shared with other accounts): {len(sound_usage) - len(exclusive_sounds)}")
    print()

if __name__ == '__main__':
    main()
