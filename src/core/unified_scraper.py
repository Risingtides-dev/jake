#!/usr/bin/env python3
"""
Unified TikTok Scraper - Handles both filtered and full catalog modes
"""

import csv
import subprocess
import json
import re
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from extract_sound_id import extract_sound_id_from_video, extract_sound_id_from_music_link

def load_accounts(csv_path):
    """Load TikTok accounts from CSV"""
    accounts = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try different column names
            url = row.get('URL', '') or row.get('account Handle', '') or row.get('Account', '')
            if url:
                if '@' in url:
                    username = url.split('@')[-1].split('?')[0].split('/')[0]
                else:
                    username = url.strip().lstrip('@')
                if username:
                    accounts.append(username)
    return accounts

def load_songs(csv_path):
    """Load songs to track from CSV"""
    tracked_songs = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_link = row.get('Song Link', '').strip()
            song = row.get('Song', '').strip()
            artist = row.get('Artist Name', '') or row.get('Artist', '')
            artist = artist.strip()

            if song_link and song:
                print(f"  Processing: {song} - {artist}")
                sound_id, fetched_title, fetched_artist = extract_sound_id_from_music_link(song_link)
                if sound_id:
                    tracked_songs[sound_id] = {
                        'song': song,
                        'artist': artist,
                        'link': song_link
                    }
                    print(f"    ✅ Sound ID: {sound_id}")
                else:
                    print(f"    ⚠️  Could not extract sound ID")
    return tracked_songs

def scrape_account_videos(username, limit=500, start_date=None):
    """Scrape videos from a TikTok account"""
    print(f"  Running yt-dlp scraper for @{username} (limit: {limit} videos)...")

    # Use absolute path to tiktok_analyzer.py
    analyzer_path = SCRIPT_DIR / 'tiktok_analyzer.py'

    cmd = [
        'python3', str(analyzer_path),
        '--url', username,
        '--limit', str(limit)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"    ⚠️  Scrape failed: {result.stderr[:100]}")
            return []

        videos = []
        output = result.stdout

        video_urls = re.findall(r'URL: (https://www\.tiktok\.com/@[^/]+/video/\d+)', output)
        video_sections = re.split(r'VIDEO #\d+', output)

        for i, section in enumerate(video_sections[1:], 0):
            if i >= len(video_urls):
                break

            video_url = video_urls[i]

            # Extract upload date
            date_match = re.search(r'Upload Date: (\d{4}-\d{2}-\d{2})', section)
            upload_date = date_match.group(1) if date_match else 'Unknown'

            # Filter by date if provided
            if start_date and upload_date != 'Unknown':
                try:
                    upload_dt = datetime.strptime(upload_date, '%Y-%m-%d')
                    if upload_dt < start_date:
                        continue
                except:
                    pass

            # Extract engagement metrics
            views_match = re.search(r'Views:\s+[\d.KM]+\s+\(([0-9,]+)\)', section)
            likes_match = re.search(r'Likes:\s+[\d.KM]+\s+\(([0-9,]+)\)', section)
            comments_match = re.search(r'Comments:\s+[\d.KM]+\s+\(([0-9,]+)\)', section)
            shares_match = re.search(r'Shares:\s+[\d.KM]+\s+\(([0-9,]+)\)', section)

            views = int(views_match.group(1).replace(',', '')) if views_match else 0
            likes = int(likes_match.group(1).replace(',', '')) if likes_match else 0
            comments = int(comments_match.group(1).replace(',', '')) if comments_match else 0
            shares = int(shares_match.group(1).replace(',', '')) if shares_match else 0

            title_match = re.search(r'Title/Caption: (.+)', section)
            title = title_match.group(1).strip() if title_match else ''

            video_data = {
                'account': username,
                'url': video_url,
                'upload_date': upload_date,
                'title': title,
                'views': views,
                'likes': likes,
                'comments': comments,
                'shares': shares
            }

            videos.append(video_data)

        return videos

    except subprocess.TimeoutExpired:
        print(f"    ⚠️  Timeout after 10 minutes")
        return []
    except Exception as e:
        print(f"    ⚠️  Error: {str(e)[:100]}")
        return []

def match_videos_filtered(videos, tracked_songs):
    """Match videos against specific songs (filtered mode)"""
    matched_videos = []

    print(f"\n🔍 Extracting sound IDs and matching...")
    print(f"  Processing {len(videos)} videos...")
    print()

    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}] @{video['account']} - {video['url'][:60]}...")

        sound_id, song_title = extract_sound_id_from_video(video['url'])

        if sound_id and sound_id in tracked_songs:
            matched_video = {
                **video,
                'sound_id': sound_id,
                'warner_song': tracked_songs[sound_id]['song'],
                'warner_artist': tracked_songs[sound_id]['artist'],
                'detected_song_title': song_title
            }
            matched_videos.append(matched_video)
            print(f"    ✅ MATCH! {tracked_songs[sound_id]['song']} - {tracked_songs[sound_id]['artist']}")
        else:
            print(f"    ❌ No match (Sound ID: {sound_id})")

    return matched_videos

def extract_all_songs(videos):
    """Extract all songs from videos (full catalog mode)"""
    songs_catalog = defaultdict(lambda: {
        'song_title': '',
        'sound_id': '',
        'total_uses': 0,
        'accounts': set(),
        'videos': [],
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0
    })

    print(f"\n🔍 Extracting sound IDs from all videos...")
    print(f"  Processing {len(videos)} videos...")
    print()

    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}] @{video['account']} - {video['url'][:60]}...")

        sound_id, song_title = extract_sound_id_from_video(video['url'])

        if sound_id:
            song_data = songs_catalog[sound_id]

            if not song_data['song_title']:
                song_data['song_title'] = song_title or 'Unknown'
                song_data['sound_id'] = sound_id

            song_data['total_uses'] += 1
            song_data['accounts'].add(video['account'])
            song_data['videos'].append(video)
            song_data['total_views'] += video['views']
            song_data['total_likes'] += video['likes']
            song_data['total_comments'] += video['comments']
            song_data['total_shares'] += video['shares']

            print(f"    ✅ Sound ID: {sound_id} | Song: {song_title}")
        else:
            print(f"    ❌ Could not extract sound ID")

    return songs_catalog

def generate_filtered_report(matched_videos, output_path):
    """Generate CSV report for filtered mode"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Account', 'Song Name', 'Artist', 'Upload Date',
            'Views', 'Likes', 'Comments', 'Shares',
            'Engagement Rate (%)', 'Video URL', 'Sound ID', 'Video Caption'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for video in matched_videos:
            engagement_rate = 0
            if video['views'] > 0:
                engagement_rate = ((video['likes'] + video['comments'] + video['shares']) / video['views']) * 100

            writer.writerow({
                'Account': f"@{video['account']}",
                'Song Name': video['warner_song'],
                'Artist': video['warner_artist'],
                'Upload Date': video['upload_date'],
                'Views': video['views'],
                'Likes': video['likes'],
                'Comments': video['comments'],
                'Shares': video['shares'],
                'Engagement Rate (%)': f"{engagement_rate:.2f}",
                'Video URL': video['url'],
                'Sound ID': video['sound_id'],
                'Video Caption': video['title'][:100]
            })

def generate_catalog_reports(songs_catalog, output_base):
    """Generate CSV reports for full catalog mode"""
    # Aggregated report
    agg_path = f"{output_base}_aggregated.csv"
    with open(agg_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Song Title', 'Sound ID', 'Total Uses', 'Accounts Using', 'Account List',
            'Total Views', 'Avg Views per Video', 'Total Likes', 'Total Comments',
            'Total Shares', 'Avg Engagement Rate (%)', 'Top Video URL', 'Top Video Views'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        sorted_songs = sorted(songs_catalog.items(), key=lambda x: x[1]['total_uses'], reverse=True)

        for sound_id, song_data in sorted_songs:
            avg_views = song_data['total_views'] // song_data['total_uses'] if song_data['total_uses'] > 0 else 0
            avg_engagement_rate = 0
            if song_data['total_views'] > 0:
                total_engagement = song_data['total_likes'] + song_data['total_comments'] + song_data['total_shares']
                avg_engagement_rate = (total_engagement / song_data['total_views']) * 100

            top_video = max(song_data['videos'], key=lambda x: x['views']) if song_data['videos'] else {}
            accounts_list = ', '.join([f"@{a}" for a in sorted(song_data['accounts'])])

            writer.writerow({
                'Song Title': song_data['song_title'],
                'Sound ID': song_data['sound_id'],
                'Total Uses': song_data['total_uses'],
                'Accounts Using': len(song_data['accounts']),
                'Account List': accounts_list,
                'Total Views': song_data['total_views'],
                'Avg Views per Video': avg_views,
                'Total Likes': song_data['total_likes'],
                'Total Comments': song_data['total_comments'],
                'Total Shares': song_data['total_shares'],
                'Avg Engagement Rate (%)': f"{avg_engagement_rate:.2f}",
                'Top Video URL': top_video.get('url', ''),
                'Top Video Views': top_video.get('views', 0)
            })

    # Detailed report
    det_path = f"{output_base}_detailed.csv"
    with open(det_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Song Title', 'Sound ID', 'Account', 'Upload Date',
            'Views', 'Likes', 'Comments', 'Shares',
            'Engagement Rate (%)', 'Video URL', 'Caption'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        sorted_songs = sorted(songs_catalog.items(), key=lambda x: x[1]['total_uses'], reverse=True)

        for sound_id, song_data in sorted_songs:
            sorted_videos = sorted(song_data['videos'], key=lambda x: x['views'], reverse=True)

            for video in sorted_videos:
                engagement_rate = 0
                if video['views'] > 0:
                    engagement_rate = ((video['likes'] + video['comments'] + video['shares']) / video['views']) * 100

                writer.writerow({
                    'Song Title': song_data['song_title'],
                    'Sound ID': song_data['sound_id'],
                    'Account': f"@{video['account']}",
                    'Upload Date': video['upload_date'],
                    'Views': video['views'],
                    'Likes': video['likes'],
                    'Comments': video['comments'],
                    'Shares': video['shares'],
                    'Engagement Rate (%)': f"{engagement_rate:.2f}",
                    'Video URL': video['url'],
                    'Caption': video['title'][:100]
                })

    return agg_path, det_path

def main():
    parser = argparse.ArgumentParser(description='Unified TikTok Scraper')
    parser.add_argument('--accounts', required=True, help='Path to accounts CSV')
    parser.add_argument('--songs', help='Path to songs CSV (optional - for filtered mode)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=500, help='Video limit per account')
    parser.add_argument('--output', required=True, help='Output filename (without extension)')

    args = parser.parse_args()

    print("=" * 80)
    print("TIKTOK TRACKER - UNIFIED SCRAPER")
    print("=" * 80)
    print()

    # Parse start date
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            print(f"Date Filter: {args.start_date} onwards")
        except:
            print(f"⚠️  Invalid date format: {args.start_date}")
            return 1
    else:
        print("Date Filter: None (all time)")
    print()

    # Determine mode
    mode = "filtered" if args.songs else "full_catalog"

    # Load songs if in filtered mode
    tracked_songs = {}
    if mode == "filtered":
        print("📋 STEP 1: Loading Songs to Track")
        print("-" * 80)
        tracked_songs = load_songs(args.songs)
        print()
        print(f"✅ Loaded {len(tracked_songs)} songs")
        print()

    # Load accounts
    print("👥 STEP 2: Loading TikTok Accounts")
    print("-" * 80)
    accounts = load_accounts(args.accounts)
    print(f"✅ Found {len(accounts)} accounts: {', '.join(['@' + a for a in accounts])}")
    print()

    # Scrape accounts
    print(f"🔍 STEP 3: Scraping All Accounts ({args.limit} videos per account)")
    print("-" * 80)
    print()

    all_videos = []
    for i, username in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Scraping @{username}...")
        videos = scrape_account_videos(username, limit=args.limit, start_date=start_date)
        all_videos.extend(videos)
        print(f"  ✅ Found {len(videos)} videos from @{username}")
        print()

    print(f"📊 Total videos scraped: {len(all_videos)}")
    print()

    # Process based on mode
    if mode == "filtered":
        print("🎵 STEP 4: Matching Videos to Tracked Songs")
        print("-" * 80)
        matched_videos = match_videos_filtered(all_videos, tracked_songs)
        print()
        print(f"✅ Found {len(matched_videos)} videos using tracked songs!")
        print()

        print("📄 STEP 5: Generating CSV Report")
        print("-" * 80)
        output_path = f"{args.output}.csv"
        generate_filtered_report(matched_videos, output_path)
        print(f"✅ Report saved to: {output_path}")

    else:  # full_catalog
        print("🎵 STEP 4: Extracting ALL Songs from Videos")
        print("-" * 80)
        songs_catalog = extract_all_songs(all_videos)
        print()
        print(f"✅ Found {len(songs_catalog)} unique songs!")
        print()

        print("📄 STEP 5: Generating CSV Reports")
        print("-" * 80)
        agg_path, det_path = generate_catalog_reports(songs_catalog, args.output)
        print(f"✅ Aggregated report: {agg_path}")
        print(f"✅ Detailed report: {det_path}")

    print()
    print("=" * 80)
    print("✅ SCRAPE COMPLETE!")
    print("=" * 80)
    print()

if __name__ == '__main__':
    main()
