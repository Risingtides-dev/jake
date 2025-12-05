#!/usr/bin/env python3
"""
Warner Sound Tracker - Test Report Generator

Generates a clean SHADCN-style HTML report organized by account with collapsible
sections for each sound used. Includes engagement metrics and clickable TikTok links.

Usage:
    python3 generate_test_report.py [--since YYYY-MM-DD] [--limit N]
"""

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config import ACCOUNTS, PROJECT_ROOT, OUTPUT_DIR

# Path to clean Warner songs CSV
WARNER_CSV = PROJECT_ROOT / 'data' / 'warner_songs_clean.csv'

def load_warner_songs():
    """
    Load Warner song list dynamically from clean CSV.
    Returns set of sound keys in "Song - Artist" format.
    """
    warner_songs = set()

    try:
        with open(WARNER_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sound_key = row.get('sound_key', '').strip()
                if sound_key:
                    warner_songs.add(sound_key)

        print(f"✅ Loaded {len(warner_songs)} Warner songs from CSV\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not load Warner songs from CSV: {e}")
        print("   Proceeding without filtering...\n")

    return warner_songs

# Load Warner songs at module level
WARNER_SONGS = load_warner_songs()

def scrape_account(username, since_date=None, limit=None):
    """
    Scrape a TikTok account using tiktok_analyzer.py.

    Args:
        username: TikTok username (with @)
        since_date: Only include videos after this date (datetime object)
        limit: Maximum number of videos to scrape (None for no limit)

    Returns:
        List of video dictionaries
    """
    print(f"Scraping {username}...")

    cmd = [
        'python3',
        str(PROJECT_ROOT / 'tiktok_analyzer.py'),
        '--url', username
    ]

    # Only add limit if specified
    if limit:
        cmd.extend(['--limit', str(limit)])
    else:
        # Use a high limit to get all videos back to October 1st
        cmd.extend(['--limit', '1000'])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"  ❌ Error scraping {username}: {result.stderr}")
            return []

        # Parse the output (get ALL videos first)
        videos = parse_analyzer_output(result.stdout, username, since_date)

        # Filter to only Warner songs AFTER scraping
        warner_videos = [v for v in videos if is_warner_song(v)]

        print(f"  ✅ Found {len(videos)} total videos, {len(warner_videos)} with Warner songs")
        return warner_videos

    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout scraping {username}")
        return []
    except Exception as e:
        print(f"  ❌ Exception scraping {username}: {e}")
        return []


def parse_analyzer_output(output, username, since_date=None):
    """Parse tiktok_analyzer.py output into structured data."""
    videos = []

    # Split by video sections
    video_sections = re.split(r'VIDEO #\d+', output)

    for section in video_sections[1:]:  # Skip first empty section
        video = {}

        # Extract URL
        url_match = re.search(r'URL: (https://www\.tiktok\.com/@[^/]+/video/\d+)', section)
        if url_match:
            video['url'] = url_match.group(1)
            # Extract video ID from URL
            video_id_match = re.search(r'/video/(\d+)', video['url'])
            if video_id_match:
                video['video_id'] = video_id_match.group(1)

        # Extract upload date
        date_match = re.search(r'Upload Date: (\d{4}-\d{2}-\d{2})', section)
        if date_match:
            video['upload_date'] = date_match.group(1)
            upload_dt = datetime.strptime(video['upload_date'], '%Y-%m-%d')

            # Filter by date if specified
            if since_date and upload_dt < since_date:
                continue

        # Extract caption/title
        caption_match = re.search(r'Title/Caption: (.+?)(?:\n|URL:)', section, re.DOTALL)
        if caption_match:
            video['caption'] = caption_match.group(1).strip()

        # Extract metrics
        views_match = re.search(r'Views:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        likes_match = re.search(r'Likes:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        comments_match = re.search(r'Comments:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        shares_match = re.search(r'Shares:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        engagement_match = re.search(r'Engagement Rate: ([\d.]+)%', section)

        if views_match:
            video['views'] = int(views_match.group(1).replace(',', ''))
        if likes_match:
            video['likes'] = int(likes_match.group(1).replace(',', ''))
        if comments_match:
            video['comments'] = int(comments_match.group(1).replace(',', ''))
        if shares_match:
            video['shares'] = int(shares_match.group(1).replace(',', ''))
        if engagement_match:
            video['engagement_rate'] = float(engagement_match.group(1))

        # Extract song info
        song_match = re.search(r'Song: (.+)', section)
        artist_match = re.search(r'Artist: (.+)', section)

        if song_match:
            video['song_title'] = song_match.group(1).strip()
        if artist_match:
            video['artist_name'] = artist_match.group(1).strip()

        # Create sound key
        if 'song_title' in video:
            if 'artist_name' in video:
                video['sound_key'] = f"{video['song_title']} - {video['artist_name']}"
            else:
                video['sound_key'] = video['song_title']
        else:
            video['sound_key'] = 'Unknown Sound'

        video['account'] = username

        # Only add if we have minimum required data
        if 'url' in video and 'upload_date' in video:
            videos.append(video)

    return videos


def is_warner_song(video):
    """
    Check if a video uses a Warner song.
    STRICT EXACT matching - only matches sound_key in "Song - Artist" format.

    Args:
        video: Video dictionary with sound_key

    Returns:
        True if video uses a Warner song, False otherwise
    """
    sound_key = video.get('sound_key', '')

    # ONLY exact match on sound_key (format: "Song - Artist")
    return sound_key in WARNER_SONGS


def format_number(num):
    """Format number with K/M suffixes."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)


def generate_html_report(accounts_data, output_file):
    """Generate SHADCN-style HTML report."""

    # Calculate total statistics
    total_videos = sum(len(videos) for videos in accounts_data.values())
    total_sounds = len(set(v['sound_key'] for videos in accounts_data.values() for v in videos))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Warner Sound Tracker - Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --background: 0 0% 100%;
            --foreground: 222.2 84% 4.9%;
            --card: 0 0% 100%;
            --card-foreground: 222.2 84% 4.9%;
            --popover: 0 0% 100%;
            --popover-foreground: 222.2 84% 4.9%;
            --primary: 221.2 83.2% 53.3%;
            --primary-foreground: 210 40% 98%;
            --secondary: 210 40% 96.1%;
            --secondary-foreground: 222.2 47.4% 11.2%;
            --muted: 210 40% 96.1%;
            --muted-foreground: 215.4 16.3% 46.9%;
            --accent: 210 40% 96.1%;
            --accent-foreground: 222.2 47.4% 11.2%;
            --destructive: 0 84.2% 60.2%;
            --destructive-foreground: 210 40% 98%;
            --border: 214.3 31.8% 91.4%;
            --input: 214.3 31.8% 91.4%;
            --ring: 221.2 83.2% 53.3%;
            --radius: 0.5rem;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: hsl(var(--background));
            color: hsl(var(--foreground));
            line-height: 1.6;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: var(--radius);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: hsl(var(--foreground));
        }}

        .header p {{
            color: hsl(var(--muted-foreground));
            font-size: 1rem;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .stat-card {{
            background: hsl(var(--secondary));
            padding: 1rem;
            border-radius: calc(var(--radius) - 2px);
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: hsl(var(--muted-foreground));
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: hsl(var(--primary));
            margin-top: 0.25rem;
        }}

        .account-section {{
            background: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: var(--radius);
            margin-bottom: 1.5rem;
            overflow: hidden;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        }}

        .account-header {{
            padding: 1.5rem;
            cursor: pointer;
            user-select: none;
            transition: background 0.15s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .account-header:hover {{
            background: hsl(var(--accent));
        }}

        .account-title {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .account-title h2 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}

        .account-badge {{
            background: hsl(var(--primary));
            color: hsl(var(--primary-foreground));
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .chevron {{
            transition: transform 0.2s;
            font-size: 1.5rem;
            color: hsl(var(--muted-foreground));
        }}

        .chevron.open {{
            transform: rotate(180deg);
        }}

        .account-content {{
            display: none;
            padding: 0 1.5rem 1.5rem;
        }}

        .account-content.open {{
            display: block;
        }}

        .sound-group {{
            margin-bottom: 2rem;
        }}

        .sound-header {{
            background: hsl(var(--muted));
            padding: 1rem;
            border-radius: calc(var(--radius) - 2px);
            margin-bottom: 1rem;
            border-left: 4px solid hsl(var(--primary));
        }}

        .sound-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: hsl(var(--foreground));
        }}

        .sound-subtitle {{
            font-size: 0.875rem;
            color: hsl(var(--muted-foreground));
            margin-top: 0.25rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }}

        thead {{
            background: hsl(var(--muted));
        }}

        th {{
            text-align: left;
            padding: 0.75rem;
            font-weight: 600;
            color: hsl(var(--foreground));
            border-bottom: 1px solid hsl(var(--border));
        }}

        td {{
            padding: 0.75rem;
            border-bottom: 1px solid hsl(var(--border));
        }}

        tbody tr:hover {{
            background: hsl(var(--accent));
        }}

        .link {{
            color: hsl(var(--primary));
            text-decoration: none;
            font-weight: 500;
        }}

        .link:hover {{
            text-decoration: underline;
        }}

        .metric {{
            font-variant-numeric: tabular-nums;
        }}

        .metric-high {{
            color: #10b981;
            font-weight: 600;
        }}

        .metric-medium {{
            color: #f59e0b;
            font-weight: 600;
        }}

        .metric-low {{
            color: hsl(var(--muted-foreground));
        }}

        .date {{
            color: hsl(var(--muted-foreground));
            font-size: 0.875rem;
        }}

        .footer {{
            text-align: center;
            padding: 2rem;
            color: hsl(var(--muted-foreground));
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Warner Sound Tracker</h1>
            <p>Test Report - Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-label">Accounts</div>
                    <div class="stat-value">{len(accounts_data)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Videos</div>
                    <div class="stat-value">{total_videos}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Unique Sounds</div>
                    <div class="stat-value">{total_sounds}</div>
                </div>
            </div>
        </div>
"""

    # Generate account sections
    for account, videos in sorted(accounts_data.items()):
        if not videos:
            continue

        # Group videos by sound
        sounds = defaultdict(list)
        for video in videos:
            sounds[video['sound_key']].append(video)

        account_id = account.replace('@', '')

        html += f"""
        <div class="account-section">
            <div class="account-header" onclick="toggleAccount('{account_id}')">
                <div class="account-title">
                    <h2>{account}</h2>
                    <span class="account-badge">{len(videos)} videos</span>
                </div>
                <span class="chevron" id="chevron-{account_id}">▼</span>
            </div>
            <div class="account-content" id="content-{account_id}">
"""

        # Generate sound sections
        for sound_key, sound_videos in sorted(sounds.items(), key=lambda x: -len(x[1])):
            # Calculate sound stats
            total_views = sum(v.get('views', 0) for v in sound_videos)
            total_likes = sum(v.get('likes', 0) for v in sound_videos)
            avg_engagement = sum(v.get('engagement_rate', 0) for v in sound_videos) / len(sound_videos)

            html += f"""
                <div class="sound-group">
                    <div class="sound-header">
                        <div class="sound-title">{sound_key}</div>
                        <div class="sound-subtitle">{len(sound_videos)} videos · {format_number(total_views)} total views · {format_number(total_likes)} total likes · {avg_engagement:.1f}% avg engagement</div>
                    </div>

                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>TikTok Link</th>
                                <th>Views</th>
                                <th>Likes</th>
                                <th>Comments</th>
                                <th>Shares</th>
                                <th>Engagement</th>
                            </tr>
                        </thead>
                        <tbody>
"""

            # Sort videos by date (newest first)
            for video in sorted(sound_videos, key=lambda x: x.get('upload_date', ''), reverse=True):
                engagement = video.get('engagement_rate', 0)
                engagement_class = 'metric-high' if engagement >= 15 else 'metric-medium' if engagement >= 10 else 'metric-low'

                html += f"""
                            <tr>
                                <td class="date">{video.get('upload_date', 'N/A')}</td>
                                <td><a href="{video.get('url', '#')}" class="link" target="_blank">View on TikTok</a></td>
                                <td class="metric">{format_number(video.get('views', 0))}</td>
                                <td class="metric">{format_number(video.get('likes', 0))}</td>
                                <td class="metric">{video.get('comments', 0)}</td>
                                <td class="metric">{video.get('shares', 0)}</td>
                                <td class="metric {engagement_class}">{engagement:.1f}%</td>
                            </tr>
"""

            html += """
                        </tbody>
                    </table>
                </div>
"""

        html += """
            </div>
        </div>
"""

    # Add footer and JavaScript
    html += """
        <div class="footer">
            Warner Music Group · Sound Tracking System<br>
            Data collected from TikTok public profiles
        </div>
    </div>

    <script>
        function toggleAccount(accountId) {
            const content = document.getElementById('content-' + accountId);
            const chevron = document.getElementById('chevron-' + accountId);

            if (content.classList.contains('open')) {
                content.classList.remove('open');
                chevron.classList.remove('open');
            } else {
                content.classList.add('open');
                chevron.classList.add('open');
            }
        }

        // Open first account by default
        const firstAccount = document.querySelector('.account-content');
        const firstChevron = document.querySelector('.chevron');
        if (firstAccount) {
            firstAccount.classList.add('open');
            firstChevron.classList.add('open');
        }
    </script>
</body>
</html>
"""

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate Warner Sound Tracker test report')
    parser.add_argument('--since', type=str, default='2025-10-01',
                       help='Only include videos after this date (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum videos per account (default: 1000 to get all videos)')
    args = parser.parse_args()

    # Parse since date
    since_date = datetime.strptime(args.since, '%Y-%m-%d')

    print("="*80)
    print("WARNER SOUND TRACKER - TEST REPORT GENERATION")
    print("="*80)
    print(f"Scraping {len(ACCOUNTS)} accounts")
    print(f"Date filter: Videos after {args.since}")
    print(f"Limit: {args.limit if args.limit else '1000 (default)'} videos per account")
    print()

    # Scrape all accounts
    accounts_data = {}
    for account in ACCOUNTS:
        videos = scrape_account(account, since_date, args.limit)
        accounts_data[account] = videos

    print()
    print("="*80)
    print("Generating HTML report...")
    print("="*80)

    # Generate report
    output_file = OUTPUT_DIR / 'test_report.html'
    generate_html_report(accounts_data, output_file)

    # Summary
    total_videos = sum(len(v) for v in accounts_data.values())
    print(f"\n📊 Summary:")
    print(f"   Accounts: {len(accounts_data)}")
    print(f"   Videos: {total_videos}")
    print(f"   Report: {output_file}")
    print(f"\n🌐 Open in browser: file://{output_file.absolute()}")


if __name__ == '__main__':
    main()
