#!/usr/bin/env python3
"""
Aggregate Sound Usage Analysis
Parses TikTok analytics from multiple accounts and aggregates by sound usage
"""

import re
from collections import defaultdict
import subprocess
import os
import sys

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Use accounts from config
# If ACCOUNTS_DICT is provided, use it; otherwise convert ACCOUNTS list to dict
if config.ACCOUNTS_DICT:
    ACCOUNTS = config.ACCOUNTS_DICT
else:
    # Convert ACCOUNTS list to dict with placeholder keys
    ACCOUNTS = {f'acc_{i}': acc for i, acc in enumerate(config.ACCOUNTS)}

def get_bash_output(bash_id):
    """Retrieve output from background bash process"""
    cmd = ['claude', 'bash-output', bash_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def parse_video_data(text, account):
    """Parse video data from analyzer output"""
    videos = []

    # Split by VIDEO #
    video_blocks = re.split(r'VIDEO #\d+', text)

    for block in video_blocks[1:]:  # Skip first empty split
        video = {'account': account}

        # Extract URL
        url_match = re.search(r'URL: (https://[^\s]+)', block)
        if url_match:
            video['url'] = url_match.group(1)

        # Extract metrics
        views_match = re.search(r'Views:\s+[\d\.KM]+\s+\(([0-9,]+)\)', block)
        likes_match = re.search(r'Likes:\s+[\d\.KM]+\s+\(([0-9,]+)\)', block)
        comments_match = re.search(r'Comments:\s+[\d\.KM]+\s+\(([0-9,]+)\)', block)
        shares_match = re.search(r'Shares:\s+[\d\.KM]+\s+\(([0-9,]+)\)', block)
        engagement_match = re.search(r'Engagement Rate: ([\d\.]+)%', block)

        video['views'] = int(views_match.group(1).replace(',', '')) if views_match else 0
        video['likes'] = int(likes_match.group(1).replace(',', '')) if likes_match else 0
        video['comments'] = int(comments_match.group(1).replace(',', '')) if comments_match else 0
        video['shares'] = int(shares_match.group(1).replace(',', '')) if shares_match else 0
        video['engagement_rate'] = float(engagement_match.group(1)) if engagement_match else 0

        # Extract song info
        song_match = re.search(r'Song: (.+)', block)
        artist_match = re.search(r'Artist: (.+)', block)

        video['song'] = song_match.group(1).strip() if song_match else 'Unknown'
        video['artist'] = artist_match.group(1).strip() if artist_match else 'Unknown'

        # Create sound key (song + artist)
        video['sound_key'] = f"{video['song']} - {video['artist']}"

        videos.append(video)

    return videos

def aggregate_by_sound(all_videos):
    """Aggregate videos by sound/song"""
    sound_stats = defaultdict(lambda: {
        'total_uses': 0,
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0,
        'total_engagement': 0,
        'videos': [],
        'accounts': set(),
        'song': '',
        'artist': ''
    })

    for video in all_videos:
        sound_key = video['sound_key']
        sound_stats[sound_key]['total_uses'] += 1
        sound_stats[sound_key]['total_views'] += video['views']
        sound_stats[sound_key]['total_likes'] += video['likes']
        sound_stats[sound_key]['total_comments'] += video['comments']
        sound_stats[sound_key]['total_shares'] += video['shares']
        sound_stats[sound_key]['total_engagement'] += video['engagement_rate']
        sound_stats[sound_key]['videos'].append(video)
        sound_stats[sound_key]['accounts'].add(video['account'])
        sound_stats[sound_key]['song'] = video['song']
        sound_stats[sound_key]['artist'] = video['artist']

    # Calculate averages
    for sound_key, stats in sound_stats.items():
        uses = stats['total_uses']
        stats['avg_views'] = stats['total_views'] // uses if uses > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // uses if uses > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // uses if uses > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // uses if uses > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / uses if uses > 0 else 0

        # Sort videos by engagement rate
        stats['videos'].sort(key=lambda x: x['engagement_rate'], reverse=True)

        # Convert accounts set to list
        stats['accounts'] = sorted(list(stats['accounts']))

    return sound_stats

def format_number(num):
    """Format number with commas"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def print_report(sound_stats):
    """Print structured report of sound usage"""

    # Sort sounds by total uses, then by average engagement rate
    sorted_sounds = sorted(
        sound_stats.items(),
        key=lambda x: (x[1]['total_uses'], x[1]['avg_engagement_rate']),
        reverse=True
    )

    print("\n" + "="*120)
    print("SOUND USAGE ANALYSIS - AGGREGATED REPORT")
    print("="*120)
    print(f"\nAnalyzed {len(sound_stats)} unique sounds/songs across {len(ACCOUNTS)} accounts")
    print("\n")

    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        print(f"#{i} - {stats['song']}")
        print(f"{'─'*120}")
        print(f"Artist: {stats['artist']}")
        print(f"Total Uses: {stats['total_uses']} videos")
        print(f"Used by: {', '.join(stats['accounts'])}")
        print("")

        print("AVERAGE PERFORMANCE METRICS:")
        print(f"  Avg Views:    {format_number(stats['avg_views']):>10} ({stats['avg_views']:,})")
        print(f"  Avg Likes:    {format_number(stats['avg_likes']):>10} ({stats['avg_likes']:,})")
        print(f"  Avg Comments: {format_number(stats['avg_comments']):>10} ({stats['avg_comments']:,})")
        print(f"  Avg Shares:   {format_number(stats['avg_shares']):>10} ({stats['avg_shares']:,})")
        print(f"  Avg Engagement Rate: {stats['avg_engagement_rate']:.2f}%")
        print("")

        print("TOTAL CUMULATIVE METRICS:")
        print(f"  Total Views:    {format_number(stats['total_views']):>10} ({stats['total_views']:,})")
        print(f"  Total Likes:    {format_number(stats['total_likes']):>10} ({stats['total_likes']:,})")
        print(f"  Total Comments: {format_number(stats['total_comments']):>10} ({stats['total_comments']:,})")
        print(f"  Total Shares:   {format_number(stats['total_shares']):>10} ({stats['total_shares']:,})")
        print("")

        # Show top 3 performing videos for this sound
        top_videos = stats['videos'][:3]
        if top_videos:
            print("TOP PERFORMING VIDEOS:")
            for j, video in enumerate(top_videos, 1):
                print(f"  {j}. {video['account']} - {format_number(video['views'])} views, {video['engagement_rate']:.2f}% engagement")
                print(f"     {video['url']}")

        print("")
        print("")

def main():
    print(f"Aggregating sound usage data from {len(ACCOUNTS)} TikTok accounts...")
    print("")

    if not ACCOUNTS:
        print("ERROR: No accounts configured. Please add accounts to config.ACCOUNTS or config.ACCOUNTS_DICT")
        return

    all_videos = []

    # Get project root directory (parent of script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = script_dir

    # We'll collect the output from the grep commands
    for bash_id, account in ACCOUNTS.items():
        print(f"Processing {account}...")

        # Run the analyzer again to get full output
        analyzer_script = os.path.join(base_dir, 'tiktok_analyzer.py')
        cmd = [
            config.PYTHON_CMD, analyzer_script,
            '--url', account,
            '--limit', str(config.DEFAULT_VIDEO_LIMIT)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=base_dir)
        videos = parse_video_data(result.stdout, account)
        all_videos.extend(videos)
        print(f"  Found {len(videos)} videos")

    print(f"\nTotal videos collected: {len(all_videos)}")
    print("")

    # Aggregate by sound
    sound_stats = aggregate_by_sound(all_videos)

    # Print report
    print_report(sound_stats)

if __name__ == '__main__':
    main()
