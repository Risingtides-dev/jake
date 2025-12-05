#!/usr/bin/env python3
"""
Generate Complete HTML Sound Usage Report
Creates a clean, modern HTML report with earth tones and sleek design
"""

import subprocess
import re
from collections import defaultdict
import os
import sys

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Use accounts from config
ACCOUNTS = config.ACCOUNTS

def parse_video_data(text, account):
    """Parse video data from analyzer output"""
    videos = []
    video_blocks = re.split(r'VIDEO #\d+', text)

    for block in video_blocks[1:]:
        video = {'account': account}

        # Extract URL
        url_match = re.search(r'URL: (https://[^\s]+)', block)
        if url_match:
            video['url'] = url_match.group(1)
        else:
            continue

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

    for sound_key, stats in sound_stats.items():
        uses = stats['total_uses']
        stats['avg_views'] = stats['total_views'] // uses if uses > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // uses if uses > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // uses if uses > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // uses if uses > 0 else 0
        stats['avg_engagement'] = stats['total_engagement'] / uses if uses > 0 else 0
        stats['videos'].sort(key=lambda x: x['engagement_rate'], reverse=True)
        stats['accounts'] = sorted(list(stats['accounts']))

    return sound_stats

def format_number(num):
    """Format number with commas"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:,}"

def get_engagement_class(rate):
    """Get CSS class for engagement rate"""
    if rate >= 15:
        return 'engagement-high'
    elif rate >= 10:
        return 'engagement-medium'
    else:
        return 'engagement-low'

def generate_html(sound_stats, all_videos):
    """Generate modern, clean HTML report with earth tones"""
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_uses'], reverse=True)
    total_views = sum(v['views'] for v in all_videos)
    total_likes = sum(v['likes'] for v in all_videos)
    total_comments = sum(v['comments'] for v in all_videos)
    total_shares = sum(v['shares'] for v in all_videos)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sound Analytics Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            /* Earth tone palette */
            --sandstone: #d4c5b9;
            --warm-gray: #8b8075;
            --taupe: #a89f94;
            --beige: #f5f1eb;
            --stone: #e8e3db;
            --charcoal: #3d3a35;
            --dark-stone: #5a5752;
            --light-sand: #faf9f7;
            --accent: #8b7355;
            --accent-dark: #6b5d47;
            
            /* Neutrals */
            --white: #ffffff;
            --gray-50: #fafafa;
            --gray-100: #f5f5f5;
            --gray-200: #e5e5e5;
            --gray-300: #d4d4d4;
            --gray-400: #a3a3a3;
            --gray-500: #737373;
            --gray-600: #525252;
            --gray-700: #404040;
            --gray-800: #262626;
            --gray-900: #171717;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--light-sand);
            color: var(--charcoal);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}

        /* Header */
        .header {{
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--gray-200);
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--charcoal);
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            font-size: 0.9375rem;
            color: var(--gray-600);
            font-weight: 400;
        }}

        /* Stats Summary */
        .stats-summary {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            padding: 2rem;
            margin-bottom: 2rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}

        .stat-card {{
            background: var(--gray-50);
            border: 1px solid var(--gray-200);
            padding: 1.5rem;
            transition: all 0.2s ease;
        }}

        .stat-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
            letter-spacing: -0.01em;
        }}

        .stat-label {{
            font-size: 0.8125rem;
            color: var(--gray-600);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Sound Sections */
        .sound-section {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: border-color 0.2s ease;
        }}

        .sound-section:hover {{
            border-color: var(--accent);
        }}

        .sound-header {{
            border-bottom: 1px solid var(--gray-200);
            padding-bottom: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .sound-title-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}

        .sound-rank {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent);
            color: var(--white);
            width: 2.5rem;
            height: 2.5rem;
            font-weight: 600;
            font-size: 1rem;
        }}

        .sound-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--charcoal);
            letter-spacing: -0.01em;
        }}

        .sound-artist {{
            font-size: 1rem;
            color: var(--gray-600);
            font-weight: 400;
            margin-top: 0.25rem;
        }}

        .sound-meta {{
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            margin-top: 1.5rem;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 500;
        }}

        .meta-value {{
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--charcoal);
        }}

        .accounts-used {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--gray-200);
        }}

        .accounts-label {{
            font-size: 0.8125rem;
            color: var(--gray-600);
            margin-bottom: 0.75rem;
            font-weight: 500;
        }}

        .account-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .account-tag {{
            display: inline-block;
            background: var(--gray-100);
            border: 1px solid var(--gray-300);
            color: var(--gray-700);
            padding: 0.375rem 0.75rem;
            font-size: 0.8125rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .account-tag:hover {{
            background: var(--accent);
            border-color: var(--accent);
            color: var(--white);
        }}

        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
            border: 1px solid var(--gray-200);
        }}

        thead {{
            background: var(--gray-50);
            border-bottom: 2px solid var(--gray-200);
        }}

        th {{
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.8125rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--gray-700);
            border-right: 1px solid var(--gray-200);
        }}

        th:last-child {{
            border-right: none;
        }}

        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--gray-200);
            border-right: 1px solid var(--gray-200);
            color: var(--charcoal);
            font-size: 0.875rem;
        }}

        td:last-child {{
            border-right: none;
        }}

        tbody tr {{
            transition: background-color 0.15s ease;
        }}

        tbody tr:hover {{
            background: var(--gray-50);
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .video-rank {{
            font-weight: 600;
            color: var(--accent);
        }}

        .account-name {{
            font-weight: 500;
            color: var(--charcoal);
        }}

        .metric-value {{
            font-weight: 500;
            color: var(--gray-700);
        }}

        .engagement-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            font-size: 0.8125rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .engagement-high {{
            background: var(--accent);
            color: var(--white);
        }}

        .engagement-medium {{
            background: var(--taupe);
            color: var(--white);
        }}

        .engagement-low {{
            background: var(--gray-300);
            color: var(--gray-700);
        }}

        .video-link {{
            color: var(--accent);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: color 0.2s ease;
        }}

        .video-link:hover {{
            color: var(--accent-dark);
            text-decoration: underline;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 1.5rem;
            margin-top: 3rem;
            border-top: 1px solid var(--gray-200);
            color: var(--gray-600);
            font-size: 0.875rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .sound-title {{
                font-size: 1.25rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }}

            table {{
                font-size: 0.8125rem;
            }}

            th, td {{
                padding: 0.5rem 0.75rem;
            }}

            .sound-meta {{
                gap: 1rem;
            }}
        }}

        @media (max-width: 480px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            table {{
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sound Analytics</h1>
            <div class="subtitle">Performance metrics across {len(ACCOUNTS)} TikTok accounts</div>
        </div>

        <div class="stats-summary">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{format_number(len(all_videos))}</div>
                    <div class="stat-label">Total Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sound_stats)}</div>
                    <div class="stat-label">Unique Sounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(ACCOUNTS)}</div>
                    <div class="stat-label">Accounts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_views)}</div>
                    <div class="stat-label">Total Views</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_likes)}</div>
                    <div class="stat-label">Total Likes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_comments + total_shares)}</div>
                    <div class="stat-label">Engagements</div>
                </div>
            </div>
        </div>
'''

    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        engagement_class = get_engagement_class(stats['avg_engagement'])
        
        html += f'''
        <div class="sound-section">
            <div class="sound-header">
                <div class="sound-title-row">
                    <span class="sound-rank">{i}</span>
                    <div>
                        <div class="sound-title">{stats['song']}</div>
                        <div class="sound-artist">{stats['artist']}</div>
                    </div>
                </div>
                <div class="sound-meta">
                    <div class="meta-item">
                        <span class="meta-label">Total Uses</span>
                        <span class="meta-value">{stats['total_uses']}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Avg Views</span>
                        <span class="meta-value">{format_number(stats['avg_views'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Avg Engagement</span>
                        <span class="meta-value">{stats['avg_engagement']:.2f}%</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Views</span>
                        <span class="meta-value">{format_number(stats['total_views'])}</span>
                    </div>
                </div>
                <div class="accounts-used">
                    <div class="accounts-label">Used by {len(stats['accounts'])} account(s):</div>
                    <div class="account-tags">
'''

        for account in stats['accounts']:
            html += f'                        <span class="account-tag">{account}</span>\n'

        html += '''                    </div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Account</th>
                        <th>Views</th>
                        <th>Likes</th>
                        <th>Comments</th>
                        <th>Shares</th>
                        <th>Engagement</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
'''

        for j, video in enumerate(stats['videos'], 1):
            engagement_class_video = get_engagement_class(video['engagement_rate'])
            html += f'''                    <tr>
                        <td class="video-rank">#{j}</td>
                        <td class="account-name">{video['account']}</td>
                        <td class="metric-value">{format_number(video['views'])}</td>
                        <td class="metric-value">{format_number(video['likes'])}</td>
                        <td class="metric-value">{format_number(video['comments'])}</td>
                        <td class="metric-value">{format_number(video['shares'])}</td>
                        <td><span class="engagement-badge {engagement_class_video}">{video['engagement_rate']:.2f}%</span></td>
                        <td><a href="{video['url']}" class="video-link" target="_blank">View</a></td>
                    </tr>
'''

        html += '''                </tbody>
            </table>
        </div>
'''

    html += f'''
        <div class="footer">
            <p>{len(all_videos)} videos analyzed across {len(ACCOUNTS)} accounts</p>
            <p style="margin-top: 0.5rem; color: var(--gray-500);">Data sourced via yt-dlp</p>
        </div>
    </div>
</body>
</html>
'''

    return html

def main():
    if not ACCOUNTS:
        print("ERROR: No accounts configured. Please add accounts to config.ACCOUNTS")
        return

    print(f"Collecting video data from {len(ACCOUNTS)} accounts...")

    all_videos = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = script_dir

    for account in ACCOUNTS:
        print(f"Processing {account}...")
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

    # Aggregate by sound
    sound_stats = aggregate_by_sound(all_videos)

    # Generate HTML
    print("Generating HTML report...")
    html_content = generate_html(sound_stats, all_videos)

    # Write to file
    output_file = config.HTML_OUTPUT_FILE
    with open(str(output_file), 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ Complete HTML report generated: {output_file}")
    print(f"   Total sounds: {len(sound_stats)}")
    print(f"   Total videos: {len(all_videos)}")
    print(f"   Accounts analyzed: {len(ACCOUNTS)}")

if __name__ == '__main__':
    main()
