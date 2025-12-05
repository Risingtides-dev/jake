#!/usr/bin/env python3
"""
In-House Network Scraper and HTML Generator
Scrapes TikTok accounts and generates HTML tracker
"""

import subprocess
import json
import re
from collections import defaultdict
from datetime import datetime
import sys

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Use accounts and exclusive songs from config
ACCOUNTS = config.ACCOUNTS
EXCLUSIVE_SONGS = config.EXCLUSIVE_SONGS

def scrape_account(account):
    """Scrape a single TikTok account using yt-dlp - ALL videos"""
    print(f"Scraping {account}...")

    profile_url = f"https://www.tiktok.com/{account}"

    cmd = [
        config.YT_DLP_CMD,
        '--flat-playlist',
        '--dump-json',
        profile_url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ⚠️  Error scraping {account}: {result.stderr}")
        return []

    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                video_data = json.loads(line)

                # Extract upload date
                upload_date = video_data.get('upload_date', '')
                if upload_date:
                    try:
                        upload_datetime = datetime.strptime(upload_date, '%Y%m%d')

                        # Filter for configured cutoff date
                        if upload_datetime < config.CUTOFF_DATE:
                            continue

                        formatted_date = upload_datetime.strftime('%Y-%m-%d')
                    except:
                        formatted_date = upload_date
                else:
                    formatted_date = 'Unknown'
                    continue  # Skip if no date

                video_info = {
                    'id': video_data.get('id'),
                    'url': video_data.get('webpage_url') or video_data.get('url'),
                    'title': video_data.get('title', '').strip(),
                    'description': video_data.get('description', '').strip(),
                    'views': video_data.get('view_count', 0),
                    'likes': video_data.get('like_count', 0),
                    'comments': video_data.get('comment_count', 0),
                    'shares': video_data.get('repost_count', 0),
                    'duration': video_data.get('duration', 0),
                    'upload_date': formatted_date,
                    'timestamp': video_data.get('timestamp', 0),
                    'song_title': video_data.get('track', ''),
                    'song_artist': video_data.get('artist', ''),
                    'account': account
                }

                # Calculate engagement rate
                if video_info['views'] > 0:
                    engagement = ((video_info['likes'] + video_info['comments'] + video_info['shares']) / video_info['views']) * 100
                    video_info['engagement_rate'] = engagement
                else:
                    video_info['engagement_rate'] = 0

                videos.append(video_info)

            except json.JSONDecodeError as e:
                print(f"  ⚠️  Error parsing JSON for {account}: {e}")
                continue

    cutoff_date_str = config.CUTOFF_DATE.strftime('%Y-%m-%d')
    print(f"  ✓ Found {len(videos)} videos from {cutoff_date_str} onwards")
    return videos

def aggregate_by_sound(all_videos):
    """Aggregate videos by sound/song - filtering out exclusive songs"""
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

    filtered_count = 0
    for video in all_videos:
        song = video['song_title'] or 'Unknown'
        artist = video['song_artist'] or 'Unknown'
        sound_key = f"{song} - {artist}"

        # Skip exclusive songs
        if sound_key in EXCLUSIVE_SONGS:
            filtered_count += 1
            continue

        sound_stats[sound_key]['total_uses'] += 1
        sound_stats[sound_key]['total_views'] += video['views']
        sound_stats[sound_key]['total_likes'] += video['likes']
        sound_stats[sound_key]['total_comments'] += video['comments']
        sound_stats[sound_key]['total_shares'] += video['shares']
        sound_stats[sound_key]['total_engagement'] += video['engagement_rate']
        sound_stats[sound_key]['videos'].append(video)
        sound_stats[sound_key]['accounts'].add(video['account'])
        sound_stats[sound_key]['song'] = song
        sound_stats[sound_key]['artist'] = artist

    print(f"  Filtered out {filtered_count} videos using exclusive songs")

    # Calculate averages and sort
    for sound_key, stats in sound_stats.items():
        uses = stats['total_uses']
        stats['avg_views'] = stats['total_views'] // uses if uses > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // uses if uses > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // uses if uses > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // uses if uses > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / uses if uses > 0 else 0

        # Sort videos by views
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)

        # Convert accounts set to list
        stats['accounts'] = sorted(list(stats['accounts']))

    return sound_stats

def aggregate_by_account(all_videos):
    """Aggregate videos by account"""
    account_stats = defaultdict(lambda: {
        'total_videos': 0,
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0,
        'total_engagement': 0,
        'videos': [],
        'unique_sounds': set()
    })

    for video in all_videos:
        account = video['account']
        sound_key = f"{video['song_title'] or 'Unknown'} - {video['song_artist'] or 'Unknown'}"

        account_stats[account]['total_videos'] += 1
        account_stats[account]['total_views'] += video['views']
        account_stats[account]['total_likes'] += video['likes']
        account_stats[account]['total_comments'] += video['comments']
        account_stats[account]['total_shares'] += video['shares']
        account_stats[account]['total_engagement'] += video['engagement_rate']
        account_stats[account]['videos'].append(video)
        account_stats[account]['unique_sounds'].add(sound_key)

    # Calculate averages
    for account, stats in account_stats.items():
        video_count = stats['total_videos']
        stats['avg_views'] = stats['total_views'] // video_count if video_count > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // video_count if video_count > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // video_count if video_count > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // video_count if video_count > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / video_count if video_count > 0 else 0

        # Sort videos by views
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)

        # Count unique sounds
        stats['unique_sounds_count'] = len(stats['unique_sounds'])

    return account_stats

def format_number(num):
    """Format number with K/M suffix"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def get_engagement_class(rate):
    """Get CSS class for engagement rate"""
    if rate >= 10:
        return 'engagement-high'
    elif rate >= 5:
        return 'engagement-medium'
    else:
        return 'engagement-low'

def generate_html(sound_stats, account_stats, total_videos):
    """Generate HTML report with glassmorphism design and tabs"""

    # Sort sounds by total uses, then by average views
    sorted_sounds = sorted(
        sound_stats.items(),
        key=lambda x: (x[1]['total_uses'], x[1]['avg_views']),
        reverse=True
    )

    # Sort accounts by average engagement rate (descending - best first)
    sorted_accounts = sorted(
        account_stats.items(),
        key=lambda x: x[1]['avg_engagement_rate'],
        reverse=True
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>In-House Network Tracker - Oct-Nov 2025</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e8e8e8;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 60px;
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a855f7 0%, #8a2be2 50%, #c4b5fd 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }}

        .header .subtitle {{
            font-size: 1.125rem;
            color: #c4b5fd;
            font-weight: 500;
        }}

        .stats-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 24px;
            margin-bottom: 60px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 32px;
            box-shadow:
                0 8px 32px 0 rgba(0, 0, 0, 0.37),
                inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(168, 85, 247, 0.4);
            box-shadow:
                0 12px 40px 0 rgba(0, 0, 0, 0.5),
                inset 0 1px 0 0 rgba(255, 255, 255, 0.1);
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: #c4b5fd;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffffff;
            line-height: 1;
        }}

        .sound-card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 32px;
            box-shadow:
                0 8px 32px 0 rgba(0, 0, 0, 0.37),
                inset 0 1px 0 0 rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }}

        .sound-card:hover {{
            border-color: rgba(168, 85, 247, 0.3);
        }}

        .sound-header {{
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .sound-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}

        .sound-artist {{
            font-size: 1.125rem;
            color: #a855f7;
            margin-bottom: 16px;
        }}

        .sound-meta {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            font-size: 0.875rem;
            color: #c4b5fd;
        }}

        .sound-meta-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .sound-meta-item strong {{
            color: #ffffff;
            font-weight: 600;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
            padding: 24px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .metric-item {{
            text-align: center;
        }}

        .metric-label {{
            font-size: 0.75rem;
            color: #c4b5fd;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
            font-weight: 600;
        }}

        .metric-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
        }}

        .videos-section {{
            margin-top: 32px;
        }}

        .videos-header {{
            font-size: 1.125rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 20px;
            padding-left: 8px;
            border-left: 3px solid #a855f7;
        }}

        .table-wrapper {{
            overflow-x: auto;
            overflow-y: hidden;
            margin: 0 -20px;
            padding: 0 20px;
            scrollbar-width: thin;
            scrollbar-color: rgba(168, 85, 247, 0.5) rgba(255, 255, 255, 0.05);
        }}

        .table-wrapper::-webkit-scrollbar {{
            height: 8px;
        }}

        .table-wrapper::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }}

        .table-wrapper::-webkit-scrollbar-thumb {{
            background: rgba(168, 85, 247, 0.5);
            border-radius: 4px;
        }}

        .table-wrapper::-webkit-scrollbar-thumb:hover {{
            background: rgba(168, 85, 247, 0.7);
        }}

        .video-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 12px;
            min-width: 1000px;
        }}

        .video-row {{
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            transition: all 0.2s ease;
        }}

        .video-row:hover {{
            background: rgba(255, 255, 255, 0.05);
            transform: translateX(4px);
        }}

        .video-row td {{
            padding: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .video-row td:first-child {{
            border-left: 1px solid rgba(255, 255, 255, 0.05);
            border-top-left-radius: 12px;
            border-bottom-left-radius: 12px;
        }}

        .video-row td:last-child {{
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            border-top-right-radius: 12px;
            border-bottom-right-radius: 12px;
        }}

        .video-account {{
            color: #a855f7;
            font-weight: 600;
            font-size: 0.875rem;
        }}

        .video-link {{
            color: #8a2be2;
            text-decoration: none;
            font-size: 0.813rem;
            transition: color 0.2s ease;
        }}

        .video-link:hover {{
            color: #c4b5fd;
        }}

        .video-stats {{
            display: flex;
            gap: 16px;
            font-size: 0.875rem;
        }}

        .stat {{
            color: #e8e8e8;
        }}

        .stat strong {{
            color: #ffffff;
            font-weight: 600;
        }}

        .engagement-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .engagement-high {{
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}

        .engagement-medium {{
            background: rgba(234, 179, 8, 0.2);
            color: #fde047;
            border: 1px solid rgba(234, 179, 8, 0.3);
        }}

        .engagement-low {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .video-date {{
            color: #9ca3af;
            font-size: 0.813rem;
        }}

        /* Tab Navigation */
        .tab-navigation {{
            display: flex;
            gap: 12px;
            margin-bottom: 40px;
            justify-content: center;
        }}

        .tab-button {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 14px 32px;
            color: #e8e8e8;
            font-weight: 600;
            font-size: 0.938rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .tab-button:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(168, 85, 247, 0.3);
        }}

        .tab-button.active {{
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(138, 43, 226, 0.3) 100%);
            border-color: rgba(168, 85, 247, 0.6);
            color: #ffffff;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Account Performance Indicator */
        .performance-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 8px;
        }}

        .performance-high {{
            background: #86efac;
            box-shadow: 0 0 8px rgba(134, 239, 172, 0.5);
        }}

        .performance-medium {{
            background: #fde047;
            box-shadow: 0 0 8px rgba(253, 224, 71, 0.5);
        }}

        .performance-low {{
            background: #fca5a5;
            box-shadow: 0 0 8px rgba(252, 165, 165, 0.5);
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}

            .sound-card {{
                padding: 24px;
            }}

            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .video-table {{
                font-size: 0.875rem;
            }}

            .tab-navigation {{
                flex-direction: column;
            }}

            .tab-button {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>In-House Network Tracker</h1>
            <p class="subtitle">Oct-Nov 2025 Performance Analysis • 41 Accounts</p>
        </div>

        <div class="tab-navigation">
            <button class="tab-button active" onclick="switchTab('sounds')">By Sound</button>
            <button class="tab-button" onclick="switchTab('accounts')">By Account</button>
        </div>

        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-label">Total Videos</div>
                <div class="stat-value">{total_videos}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique Sounds</div>
                <div class="stat-value">{len(sound_stats)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Accounts</div>
                <div class="stat-value">38</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Time Period</div>
                <div class="stat-value">Nov 2025</div>
            </div>
        </div>

        <!-- Sounds Tab -->
        <div id="sounds-tab" class="tab-content active">
'''

    # Generate sound cards
    for rank, (sound_key, stats) in enumerate(sorted_sounds, 1):
        accounts_list = ', '.join(stats['accounts'])

        html += f'''
            <div class="sound-card">
            <div class="sound-header">
                <div class="sound-title">#{rank} • {stats['song']}</div>
                <div class="sound-artist">{stats['artist']}</div>
                <div class="sound-meta">
                    <div class="sound-meta-item">
                        <span>Total Uses:</span>
                        <strong>{stats['total_uses']} videos</strong>
                    </div>
                    <div class="sound-meta-item">
                        <span>Accounts:</span>
                        <strong>{len(stats['accounts'])}</strong>
                    </div>
                    <div class="sound-meta-item">
                        <span>Avg Engagement:</span>
                        <strong>{stats['avg_engagement_rate']:.2f}%</strong>
                    </div>
                </div>
            </div>

            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-label">Avg Views</div>
                    <div class="metric-value">{format_number(stats['avg_views'])}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Likes</div>
                    <div class="metric-value">{format_number(stats['avg_likes'])}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Comments</div>
                    <div class="metric-value">{format_number(stats['avg_comments'])}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Avg Shares</div>
                    <div class="metric-value">{format_number(stats['avg_shares'])}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Total Views</div>
                    <div class="metric-value">{format_number(stats['total_views'])}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Total Likes</div>
                    <div class="metric-value">{format_number(stats['total_likes'])}</div>
                </div>
            </div>

            <div class="videos-section">
                <h3 class="videos-header">All Videos Using This Sound (Ranked by Views)</h3>
                <div class="table-wrapper">
                    <table class="video-table">
'''

        # Generate video rows
        for video in stats['videos']:
            engagement_class = get_engagement_class(video['engagement_rate'])

            html += f'''
                        <tr class="video-row">
                            <td>
                                <div class="video-account">{video['account']}</div>
                                <div class="video-date">{video['upload_date']}</div>
                            </td>
                            <td>
                                <a href="{video['url']}" target="_blank" class="video-link">View Video →</a>
                            </td>
                            <td>
                                <div class="video-stats">
                                    <span class="stat"><strong>{format_number(video['views'])}</strong> views</span>
                                    <span class="stat"><strong>{format_number(video['likes'])}</strong> likes</span>
                                    <span class="stat"><strong>{format_number(video['comments'])}</strong> comments</span>
                                </div>
                            </td>
                            <td>
                                <span class="engagement-badge {engagement_class}">
                                    {video['engagement_rate']:.2f}% Engagement
                                </span>
                            </td>
                        </tr>
'''

        html += '''
                    </table>
                </div>
            </div>
            </div>
'''

    # Close sounds tab and start accounts tab
    html += '''
        </div>
        <!-- End Sounds Tab -->

        <!-- Accounts Tab -->
        <div id="accounts-tab" class="tab-content">
'''

    # Generate account cards sorted by performance (worst to best to help identify laggards)
    for rank, (account, stats) in enumerate(sorted_accounts, 1):
        # Determine performance class based on engagement rate
        if stats['avg_engagement_rate'] >= 10:
            perf_class = 'performance-high'
            perf_text = 'High'
        elif stats['avg_engagement_rate'] >= 5:
            perf_class = 'performance-medium'
            perf_text = 'Medium'
        else:
            perf_class = 'performance-low'
            perf_text = 'Low'

        engagement_class = get_engagement_class(stats['avg_engagement_rate'])

        html += f'''
            <div class="sound-card">
                <div class="sound-header">
                    <div class="sound-title">#{rank} • {account} <span class="performance-indicator {perf_class}"></span></div>
                    <div class="sound-meta">
                        <div class="sound-meta-item">
                            <span>Performance:</span>
                            <strong>{perf_text}</strong>
                        </div>
                        <div class="sound-meta-item">
                            <span>Total Videos:</span>
                            <strong>{stats['total_videos']}</strong>
                        </div>
                        <div class="sound-meta-item">
                            <span>Unique Sounds:</span>
                            <strong>{stats['unique_sounds_count']}</strong>
                        </div>
                        <div class="sound-meta-item">
                            <span>Avg Engagement:</span>
                            <strong>{stats['avg_engagement_rate']:.2f}%</strong>
                        </div>
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Avg Views</div>
                        <div class="metric-value">{format_number(stats['avg_views'])}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Avg Likes</div>
                        <div class="metric-value">{format_number(stats['avg_likes'])}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Avg Comments</div>
                        <div class="metric-value">{format_number(stats['avg_comments'])}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Avg Shares</div>
                        <div class="metric-value">{format_number(stats['avg_shares'])}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Total Views</div>
                        <div class="metric-value">{format_number(stats['total_views'])}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Total Likes</div>
                        <div class="metric-value">{format_number(stats['total_likes'])}</div>
                    </div>
                </div>

                <div class="videos-section">
                    <h3 class="videos-header">Recent Videos from {account} (Ranked by Views)</h3>
                    <div class="table-wrapper">
                        <table class="video-table">
'''

        # Show top 10 videos for each account
        for video in stats['videos'][:10]:
            video_eng_class = get_engagement_class(video['engagement_rate'])
            song_display = f"{video['song_title'] or 'Unknown'}" if video['song_title'] else "Unknown"

            html += f'''
                            <tr class="video-row">
                                <td>
                                    <div class="video-date">{video['upload_date']}</div>
                                    <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 4px;">{song_display}</div>
                                </td>
                                <td>
                                    <a href="{video['url']}" target="_blank" class="video-link">View Video →</a>
                                </td>
                                <td>
                                    <div class="video-stats">
                                        <span class="stat"><strong>{format_number(video['views'])}</strong> views</span>
                                        <span class="stat"><strong>{format_number(video['likes'])}</strong> likes</span>
                                        <span class="stat"><strong>{format_number(video['comments'])}</strong> comments</span>
                                    </div>
                                </td>
                                <td>
                                    <span class="engagement-badge {video_eng_class}">
                                        {video['engagement_rate']:.2f}% Engagement
                                    </span>
                                </td>
                            </tr>
'''

        html += '''
                        </table>
                    </div>
                </div>
            </div>
'''

    html += '''
        </div>
        <!-- End Accounts Tab -->

    </div>

    <script>
        function switchTab(tabName) {
            // Hide all tab content
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {
                button.classList.remove('active');
            });

            // Show selected tab content
            const selectedTab = document.getElementById(tabName + '-tab');
            if (selectedTab) {
                selectedTab.classList.add('active');
            }

            // Add active class to clicked button
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
'''

    return html

def main():
    print("\n" + "="*80)
    print("IN-HOUSE NETWORK TRACKER - OCT-NOV 2025")
    print("="*80)
    print(f"\nScraping {len(ACCOUNTS)} accounts for posts from October 1st, 2025 onwards...\n")

    all_videos = []

    for account in ACCOUNTS:
        videos = scrape_account(account)  # No limit - scrape ALL videos
        all_videos.extend(videos)

    print(f"\n{'='*80}")
    print(f"Total videos collected from October 2025 onwards: {len(all_videos)}")
    print(f"{'='*80}\n")

    if not all_videos:
        print("⚠️  No videos found from October 2025 onwards. Exiting.")
        return

    print("Aggregating by sound...")
    sound_stats = aggregate_by_sound(all_videos)
    print(f"Found {len(sound_stats)} unique sounds (after filtering)\n")

    print("Aggregating by account...")
    account_stats = aggregate_by_account(all_videos)
    print(f"Analyzed {len(account_stats)} accounts\n")

    print("Generating HTML report...")
    html_content = generate_html(sound_stats, account_stats, len(all_videos))

    output_file = config.NETWORK_TRACKER_OUTPUT_FILE
    with open(str(output_file), 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {output_file}")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
