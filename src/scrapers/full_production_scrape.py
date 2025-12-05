#!/usr/bin/env python3
"""
Full Production Scrape - Warner Sound Tracker
Scrapes all 5 accounts, matches against Warner songs, generates CSV report
"""

import csv
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from extract_sound_id import extract_sound_id_from_music_link, extract_sound_id_from_video

def load_warner_songs(csv_path):
    """Load Warner songs and extract sound IDs"""
    tracked_songs = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_link = row.get('Song Link', '').strip()
            song = row.get('Song', '').strip()
            artist = row.get('Artist Name', '').strip()

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

def load_accounts(csv_path):
    """Load TikTok accounts to scrape"""
    accounts = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '') or row.get('account Handle', '')
            if url and '@' in url:
                username = url.split('@')[-1].split('?')[0].split('/')[0]
                if username:
                    accounts.append(username)

    return accounts

def scrape_account_videos(username, limit=500):
    """Scrape videos from a TikTok account using tiktok_analyzer.py"""
    print(f"  Running yt-dlp scraper for @{username} (limit: {limit} videos)...")

    cmd = [
        'python3', 'tiktok_analyzer.py',
        '--url', username,
        '--limit', str(limit)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"    ⚠️  Scrape failed: {result.stderr[:100]}")
            return []

        # Parse video data from output
        videos = []
        output = result.stdout

        # Find all video URLs
        video_urls = re.findall(r'URL: (https://www\.tiktok\.com/@[^/]+/video/\d+)', output)

        # Parse engagement metrics for each video
        video_sections = re.split(r'VIDEO #\d+', output)

        for i, section in enumerate(video_sections[1:], 0):  # Skip first empty section
            if i >= len(video_urls):
                break

            video_url = video_urls[i]

            # Extract upload date
            date_match = re.search(r'Upload Date: (\d{4}-\d{2}-\d{2})', section)
            upload_date = date_match.group(1) if date_match else 'Unknown'

            # Filter by date (October 14, 2025 onwards)
            if upload_date != 'Unknown':
                try:
                    upload_dt = datetime.strptime(upload_date, '%Y-%m-%d')
                    start_date = datetime(2025, 10, 14)
                    if upload_dt < start_date:
                        continue  # Only include Oct 14, 2025 onwards
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

            # Extract caption/title
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
        print(f"    ⚠️  Timeout after 5 minutes")
        return []
    except Exception as e:
        print(f"    ⚠️  Error: {str(e)[:100]}")
        return []

def match_videos_to_songs(videos, tracked_songs):
    """Extract sound IDs and match videos to Warner songs"""
    matched_videos = []

    print(f"\n🔍 Extracting sound IDs and matching...")
    print(f"  Processing {len(videos)} videos...")
    print()

    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}] @{video['account']} - {video['url'][:60]}...")

        # Extract sound ID from video page
        sound_id, song_title = extract_sound_id_from_video(video['url'])

        if sound_id and sound_id in tracked_songs:
            # Match found!
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

def generate_csv_report(matched_videos, output_path):
    """Generate CSV report with matched videos"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Account',
            'Song Name',
            'Artist',
            'Upload Date',
            'Views',
            'Likes',
            'Comments',
            'Shares',
            'Engagement Rate (%)',
            'Video URL',
            'Sound ID',
            'Video Caption'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for video in matched_videos:
            # Calculate engagement rate
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
                'Video Caption': video['title'][:100]  # Truncate long captions
            })

def main():
    print("=" * 80)
    print("WARNER SOUND TRACKER - FULL PRODUCTION SCRAPE")
    print("=" * 80)
    print()
    print(f"Date Range: October 14, 2025 onwards (Complete Scrape)")
    print()

    # STEP 1: Load Warner songs
    print("📋 STEP 1: Loading Warner Songs with Sound IDs")
    print("-" * 80)
    warner_csv = "data/Private & Shared 4/WARNER Sound Use Tracker - October 28d1465bb82981929dabde2da2622466_all.csv"
    tracked_songs = load_warner_songs(warner_csv)
    print()
    print(f"✅ Loaded {len(tracked_songs)} Warner songs")
    print()

    # STEP 2: Load accounts
    print("👥 STEP 2: Loading TikTok Accounts")
    print("-" * 80)
    accounts_csv = "data/Private & Shared 4/WARNER Account Logins 28d1465bb82981689f08f0566bc4e987_all.csv"
    accounts = load_accounts(accounts_csv)
    print(f"✅ Found {len(accounts)} accounts: {', '.join(['@' + a for a in accounts])}")
    print()

    # STEP 3: Scrape all accounts
    print("🔍 STEP 3: Scraping All Accounts (500 videos per account)")
    print("-" * 80)
    print()

    all_videos = []
    for i, username in enumerate(accounts, 1):
        print(f"[{i}/{len(accounts)}] Scraping @{username}...")
        videos = scrape_account_videos(username, limit=500)
        all_videos.extend(videos)
        print(f"  ✅ Found {len(videos)} videos from @{username} (after date filter)")
        print()

    print(f"📊 Total videos scraped: {len(all_videos)}")
    print()

    # STEP 4: Match videos to Warner songs
    print("🎵 STEP 4: Matching Videos to Warner Songs by Sound ID")
    print("-" * 80)
    matched_videos = match_videos_to_songs(all_videos, tracked_songs)
    print()
    print(f"✅ Found {len(matched_videos)} videos using Warner songs!")
    print()

    # STEP 5: Generate CSV report
    print("📄 STEP 5: Generating CSV Report")
    print("-" * 80)
    output_path = "warner_song_usage_report_COMPLETE.csv"
    generate_csv_report(matched_videos, output_path)
    print(f"✅ Report saved to: {output_path}")
    print()

    # Summary statistics
    print("=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Videos scraped: {len(all_videos)}")
    print(f"Warner songs tracked: {len(tracked_songs)}")
    print(f"Videos using Warner songs: {len(matched_videos)}")
    print(f"Match rate: {(len(matched_videos) / len(all_videos) * 100):.1f}%")
    print()

    # Breakdown by account
    print("Breakdown by account:")
    for account in accounts:
        account_matches = [v for v in matched_videos if v['account'] == account]
        if account_matches:
            print(f"  @{account}: {len(account_matches)} videos")
    print()

    # Breakdown by song
    print("Top Warner songs used:")
    song_counts = {}
    for video in matched_videos:
        song_key = f"{video['warner_song']} - {video['warner_artist']}"
        song_counts[song_key] = song_counts.get(song_key, 0) + 1

    for song, count in sorted(song_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {song}: {count} videos")
    print()

    # Total engagement metrics
    total_views = sum(v['views'] for v in matched_videos)
    total_likes = sum(v['likes'] for v in matched_videos)
    total_comments = sum(v['comments'] for v in matched_videos)
    total_shares = sum(v['shares'] for v in matched_videos)

    print("Total engagement on Warner song videos:")
    print(f"  Views: {total_views:,}")
    print(f"  Likes: {total_likes:,}")
    print(f"  Comments: {total_comments:,}")
    print(f"  Shares: {total_shares:,}")
    print()

    print("=" * 80)
    print("✅ SCRAPE COMPLETE!")
    print("=" * 80)
    print()
    print(f"📄 CSV Report: {output_path}")
    print()

if __name__ == '__main__':
    main()
