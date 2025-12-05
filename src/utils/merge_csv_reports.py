#!/usr/bin/env python3
"""
Merge two Warner song usage CSV reports and remove duplicates
"""

import csv
from datetime import datetime

def load_csv_data(csv_path):
    """Load CSV data into list of dictionaries"""
    videos = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            videos.append(row)

    return videos

def merge_and_deduplicate(csv1_path, csv2_path, output_path):
    """Merge two CSV files and remove duplicates based on Video URL"""
    print("=" * 80)
    print("MERGING CSV REPORTS")
    print("=" * 80)
    print()

    # Load both CSV files
    print(f"Loading {csv1_path}...")
    videos1 = load_csv_data(csv1_path)
    print(f"  ✅ Loaded {len(videos1)} videos")

    print(f"Loading {csv2_path}...")
    videos2 = load_csv_data(csv2_path)
    print(f"  ✅ Loaded {len(videos2)} videos")

    print()
    print(f"Total videos before deduplication: {len(videos1) + len(videos2)}")
    print()

    # Merge and deduplicate by Video URL
    seen_urls = set()
    merged_videos = []

    # Add videos from both CSVs, skipping duplicates
    for video in videos1 + videos2:
        video_url = video.get('Video URL', '')
        if video_url and video_url not in seen_urls:
            seen_urls.add(video_url)
            merged_videos.append(video)

    print(f"Total videos after deduplication: {len(merged_videos)}")
    print(f"Duplicates removed: {len(videos1) + len(videos2) - len(merged_videos)}")
    print()

    # Sort by upload date (most recent first)
    print("Sorting by upload date...")
    merged_videos.sort(key=lambda x: x.get('Upload Date', ''), reverse=True)
    print()

    # Write to output CSV
    print(f"Writing merged CSV to {output_path}...")
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

        for video in merged_videos:
            writer.writerow(video)

    print(f"✅ Merged CSV saved to: {output_path}")
    print()

    # Summary statistics
    print("=" * 80)
    print("MERGED CSV SUMMARY")
    print("=" * 80)
    print()

    # Date range
    dates = [v['Upload Date'] for v in merged_videos if v.get('Upload Date') and v['Upload Date'] != 'Unknown']
    if dates:
        dates.sort()
        print(f"Date range: {dates[0]} to {dates[-1]}")

    print(f"Total videos: {len(merged_videos)}")
    print()

    # Breakdown by account
    print("Videos by account:")
    accounts = {}
    for video in merged_videos:
        account = video.get('Account', '')
        accounts[account] = accounts.get(account, 0) + 1

    for account, count in sorted(accounts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {account}: {count} videos")

    print()

    # Top songs
    print("Top Warner songs used:")
    songs = {}
    for video in merged_videos:
        song_key = f"{video.get('Song Name', '')} - {video.get('Artist', '')}"
        songs[song_key] = songs.get(song_key, 0) + 1

    for song, count in sorted(songs.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {song}: {count} videos")

    print()

    # Total engagement
    total_views = sum(int(v.get('Views', 0)) for v in merged_videos if v.get('Views'))
    total_likes = sum(int(v.get('Likes', 0)) for v in merged_videos if v.get('Likes'))
    total_comments = sum(int(v.get('Comments', 0)) for v in merged_videos if v.get('Comments'))
    total_shares = sum(int(v.get('Shares', 0)) for v in merged_videos if v.get('Shares'))

    print("Total engagement:")
    print(f"  Views: {total_views:,}")
    print(f"  Likes: {total_likes:,}")
    print(f"  Comments: {total_comments:,}")
    print(f"  Shares: {total_shares:,}")
    print()

    print("=" * 80)
    print("✅ MERGE COMPLETE!")
    print("=" * 80)
    print()

def main():
    csv1 = "warner_song_usage_report.csv"
    csv2 = "warner_song_usage_report_OCT14_29.csv"
    output = "warner_song_usage_report_COMPLETE.csv"

    print()
    print(f"Merging:")
    print(f"  1. {csv1} (Oct 28/29 onwards)")
    print(f"  2. {csv2} (Oct 14-29 gap fill)")
    print(f"Output: {output}")
    print()

    merge_and_deduplicate(csv1, csv2, output)

if __name__ == '__main__':
    main()
