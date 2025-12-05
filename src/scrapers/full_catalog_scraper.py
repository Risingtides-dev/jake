#!/usr/bin/env python3
"""
Full Catalog Scraper - For In-House Networks
Scrapes ALL videos from accounts and extracts ALL songs used (no filtering)
Generates aggregated song usage report
"""

import csv
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from extract_sound_id import extract_sound_id_from_video
from collections import defaultdict

def load_accounts(csv_path):
    """Load TikTok accounts to scrape"""
    accounts = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '') or row.get('account Handle', '') or row.get('Account', '')
            if url and '@' in url:
                username = url.split('@')[-1].split('?')[0].split('/')[0]
                if username:
                    accounts.append(username)
            elif url and not url.startswith('http'):
                # Handle bare usernames
                username = url.lstrip('@').strip()
                if username:
                    accounts.append(username)

    return accounts

def scrape_account_videos(username, limit=500, start_date=None):
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

            # Filter by date if provided
            if start_date and upload_date != 'Unknown':
                try:
                    upload_dt = datetime.strptime(upload_date, '%Y-%m-%d')
                    if upload_dt < start_date:
                        continue  # Skip videos before start date
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
        print(f"    ⚠️  Timeout after 10 minutes")
        return []
    except Exception as e:
        print(f"    ⚠️  Error: {str(e)[:100]}")
        return []

def extract_all_songs(videos):
    """Extract sound IDs and song info from all videos"""
    songs_catalog = defaultdict(lambda: {
        'song_title': '',
        'artist': '',
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

        # Extract sound ID from video page
        sound_id, song_title = extract_sound_id_from_video(video['url'])

        if sound_id:
            # Add to catalog
            song_key = sound_id
            song_data = songs_catalog[song_key]

            # Update song info (use first occurrence data)
            if not song_data['song_title']:
                song_data['song_title'] = song_title or 'Unknown'
                song_data['sound_id'] = sound_id

            # Aggregate stats
            song_data['total_uses'] += 1
            song_data['accounts'].add(video['account'])
            song_data['videos'].append({
                'account': video['account'],
                'url': video['url'],
                'upload_date': video['upload_date'],
                'views': video['views'],
                'likes': video['likes'],
                'comments': video['comments'],
                'shares': video['shares'],
                'title': video['title']
            })
            song_data['total_views'] += video['views']
            song_data['total_likes'] += video['likes']
            song_data['total_comments'] += video['comments']
            song_data['total_shares'] += video['shares']

            print(f"    ✅ Sound ID: {sound_id} | Song: {song_title}")
        else:
            print(f"    ❌ Could not extract sound ID")

    return songs_catalog

def generate_aggregated_csv_report(songs_catalog, output_path):
    """Generate aggregated CSV report showing all songs used"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Song Title',
            'Sound ID',
            'Total Uses',
            'Accounts Using',
            'Account List',
            'Total Views',
            'Avg Views per Video',
            'Total Likes',
            'Total Comments',
            'Total Shares',
            'Avg Engagement Rate (%)',
            'Top Video URL',
            'Top Video Views'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by total uses
        sorted_songs = sorted(songs_catalog.items(),
                            key=lambda x: x[1]['total_uses'],
                            reverse=True)

        for sound_id, song_data in sorted_songs:
            # Calculate averages
            avg_views = song_data['total_views'] // song_data['total_uses'] if song_data['total_uses'] > 0 else 0

            # Calculate average engagement rate
            avg_engagement_rate = 0
            if song_data['total_views'] > 0:
                total_engagement = song_data['total_likes'] + song_data['total_comments'] + song_data['total_shares']
                avg_engagement_rate = (total_engagement / song_data['total_views']) * 100

            # Find top video
            top_video = max(song_data['videos'], key=lambda x: x['views']) if song_data['videos'] else {}

            # Format accounts list
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

def generate_detailed_csv_report(songs_catalog, output_path):
    """Generate detailed CSV report listing all individual videos"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Song Title',
            'Sound ID',
            'Account',
            'Upload Date',
            'Views',
            'Likes',
            'Comments',
            'Shares',
            'Engagement Rate (%)',
            'Video URL',
            'Caption'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by total uses, then by views within each song
        sorted_songs = sorted(songs_catalog.items(),
                            key=lambda x: x[1]['total_uses'],
                            reverse=True)

        for sound_id, song_data in sorted_songs:
            # Sort videos by views
            sorted_videos = sorted(song_data['videos'], key=lambda x: x['views'], reverse=True)

            for video in sorted_videos:
                # Calculate engagement rate
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
                    'Caption': video['title'][:100]  # Truncate long captions
                })

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Full Catalog Scraper - Extract all songs from accounts'
    )
    parser.add_argument('--accounts', required=True,
                       help='Path to accounts CSV file')
    parser.add_argument('--limit', type=int, default=500,
                       help='Video limit per account (default: 500)')
    parser.add_argument('--start-date',
                       help='Start date filter (YYYY-MM-DD)')
    parser.add_argument('--output', default='full_catalog_report',
                       help='Output filename prefix (default: full_catalog_report)')

    args = parser.parse_args()

    print("=" * 80)
    print("FULL CATALOG SCRAPER - IN-HOUSE NETWORK ANALYSIS")
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
        print("Date Filter: None (all videos)")
    print()

    # STEP 1: Load accounts
    print("👥 STEP 1: Loading TikTok Accounts")
    print("-" * 80)
    accounts = load_accounts(args.accounts)
    print(f"✅ Found {len(accounts)} accounts: {', '.join(['@' + a for a in accounts])}")
    print()

    # STEP 2: Scrape all accounts
    print("🔍 STEP 2: Scraping All Accounts")
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

    # STEP 3: Extract all songs
    print("🎵 STEP 3: Extracting ALL Songs from Videos")
    print("-" * 80)
    songs_catalog = extract_all_songs(all_videos)
    print()
    print(f"✅ Found {len(songs_catalog)} unique songs!")
    print()

    # STEP 4: Generate reports
    print("📄 STEP 4: Generating Reports")
    print("-" * 80)

    aggregated_path = f"{args.output}_aggregated.csv"
    detailed_path = f"{args.output}_detailed.csv"

    generate_aggregated_csv_report(songs_catalog, aggregated_path)
    print(f"✅ Aggregated report saved to: {aggregated_path}")

    generate_detailed_csv_report(songs_catalog, detailed_path)
    print(f"✅ Detailed report saved to: {detailed_path}")
    print()

    # Summary statistics
    print("=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print()
    print(f"Accounts scraped: {len(accounts)}")
    print(f"Total videos analyzed: {len(all_videos)}")
    print(f"Unique songs found: {len(songs_catalog)}")
    print()

    # Top 10 songs
    print("Top 10 Most Used Songs:")
    sorted_songs = sorted(songs_catalog.items(),
                         key=lambda x: x[1]['total_uses'],
                         reverse=True)

    for i, (sound_id, song_data) in enumerate(sorted_songs[:10], 1):
        print(f"  {i}. {song_data['song_title']}: {song_data['total_uses']} uses across {len(song_data['accounts'])} account(s)")
    print()

    # Total engagement metrics
    total_views = sum(song['total_views'] for song in songs_catalog.values())
    total_likes = sum(song['total_likes'] for song in songs_catalog.values())
    total_comments = sum(song['total_comments'] for song in songs_catalog.values())
    total_shares = sum(song['total_shares'] for song in songs_catalog.values())

    print("Total engagement across all videos:")
    print(f"  Views: {total_views:,}")
    print(f"  Likes: {total_likes:,}")
    print(f"  Comments: {total_comments:,}")
    print(f"  Shares: {total_shares:,}")
    print()

    print("=" * 80)
    print("✅ FULL CATALOG SCRAPE COMPLETE!")
    print("=" * 80)
    print()
    print(f"📄 Aggregated Report: {aggregated_path}")
    print(f"📄 Detailed Report: {detailed_path}")
    print()

if __name__ == '__main__':
    main()
