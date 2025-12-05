#!/usr/bin/env python3
"""
Generate HTML Preview from CSV Report
Reads warner_song_usage_report_COMPLETE.csv and generates a beautiful HTML preview
"""

import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).parent.absolute()
CSV_FILE = PROJECT_ROOT / 'warner_song_usage_report_COMPLETE.csv'
OUTPUT_DIR = PROJECT_ROOT / 'output'
OUTPUT_FILE = OUTPUT_DIR / 'warner_report_preview.html'


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


def load_csv_data():
    """Load and parse CSV data"""
    videos = []
    
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                views = int(row.get('Views', 0) or 0)
                likes = int(row.get('Likes', 0) or 0)
                comments = int(row.get('Comments', 0) or 0)
                shares = int(row.get('Shares', 0) or 0)
                engagement = float(row.get('Engagement Rate (%)', 0) or 0)
            except (ValueError, TypeError):
                views = likes = comments = shares = engagement = 0
            
            video = {
                'account': row.get('Account', ''),
                'song': row.get('Song Name', ''),
                'artist': row.get('Artist', ''),
                'upload_date': row.get('Upload Date', ''),
                'views': views,
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'engagement_rate': engagement,
                'url': row.get('Video URL', ''),
                'sound_id': row.get('Sound ID', ''),
                'caption': row.get('Video Caption', '')
            }
            
            videos.append(video)
    
    return videos


def aggregate_by_sound(videos):
    """Aggregate videos by song/artist"""
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
    
    for video in videos:
        song = video['song']
        artist = video['artist']
        sound_key = f"{song} - {artist}"
        
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
    
    # Calculate averages
    for sound_key, stats in sound_stats.items():
        uses = stats['total_uses']
        stats['avg_views'] = stats['total_views'] // uses if uses > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // uses if uses > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // uses if uses > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // uses if uses > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / uses if uses > 0 else 0
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)
        stats['accounts'] = sorted(list(stats['accounts']))
    
    return sound_stats


def aggregate_by_account(videos):
    """Aggregate videos by account/page"""
    account_stats = defaultdict(lambda: {
        'total_videos': 0,
        'total_views': 0,
        'total_likes': 0,
        'total_comments': 0,
        'total_shares': 0,
        'total_engagement': 0,
        'videos': [],
        'songs': defaultdict(lambda: {'count': 0, 'views': 0, 'likes': 0})
    })
    
    for video in videos:
        account = video['account']
        song_key = f"{video['song']} - {video['artist']}"
        
        account_stats[account]['total_videos'] += 1
        account_stats[account]['total_views'] += video['views']
        account_stats[account]['total_likes'] += video['likes']
        account_stats[account]['total_comments'] += video['comments']
        account_stats[account]['total_shares'] += video['shares']
        account_stats[account]['total_engagement'] += video['engagement_rate']
        account_stats[account]['videos'].append(video)
        account_stats[account]['songs'][song_key]['count'] += 1
        account_stats[account]['songs'][song_key]['views'] += video['views']
        account_stats[account]['songs'][song_key]['likes'] += video['likes']
    
    # Calculate averages and sort
    for account, stats in account_stats.items():
        video_count = stats['total_videos']
        stats['avg_views'] = stats['total_views'] // video_count if video_count > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // video_count if video_count > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / video_count if video_count > 0 else 0
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)
        # Convert songs dict to sorted list
        stats['songs_list'] = sorted(
            [{'song': k, **v} for k, v in stats['songs'].items()],
            key=lambda x: x['count'],
            reverse=True
        )
    
    return account_stats


def generate_html(sound_stats, account_stats, all_videos):
    """Generate HTML report"""
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_uses'], reverse=True)
    sorted_accounts = sorted(account_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)
    total_views = sum(v['views'] for v in all_videos)
    total_likes = sum(v['likes'] for v in all_videos)
    total_comments = sum(v['comments'] for v in all_videos)
    total_shares = sum(v['shares'] for v in all_videos)
    unique_accounts = len(set(v['account'] for v in all_videos))
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Warner Sound Usage Report</title>
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

        /* Table Container with Scrollbar */
        .table-container {{
            max-height: 500px;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid var(--gray-200);
            margin-top: 1.5rem;
            position: relative;
        }}

        .table-container table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .table-container thead {{
            position: sticky;
            top: 0;
            z-index: 10;
            background: var(--gray-50);
        }}

        .table-container::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        .table-container::-webkit-scrollbar-track {{
            background: var(--gray-100);
        }}

        .table-container::-webkit-scrollbar-thumb {{
            background: var(--gray-400);
            border-radius: 4px;
        }}

        .table-container::-webkit-scrollbar-thumb:hover {{
            background: var(--gray-500);
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--gray-200);
        }}

        .tab-button {{
            background: none;
            border: none;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 500;
            color: var(--gray-600);
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s ease;
            font-family: 'Inter', sans-serif;
        }}

        .tab-button:hover {{
            color: var(--charcoal);
            background: var(--gray-50);
        }}

        .tab-button.active {{
            color: var(--accent);
            border-bottom-color: var(--accent);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Warner Sound Usage Report</h1>
            <p class="subtitle">Complete analytics dashboard for Warner Music Group songs on TikTok</p>
        </div>

        <div class="tabs">
            <button type="button" class="tab-button active" data-tab="sounds">Sounds</button>
            <button type="button" class="tab-button" data-tab="pages">Pages</button>
        </div>

        <div class="stats-summary">
            <h2 style="font-size: 1.5rem; font-weight: 600; color: var(--charcoal); margin-bottom: 1rem;">Summary</h2>
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
                    <div class="stat-value">{unique_accounts}</div>
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

        <!-- Sounds Tab -->
        <div id="sounds-tab" class="tab-content active">
'''

    # Generate sound sections
    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        engagement_class = get_engagement_class(stats['avg_engagement_rate'])
        
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
                        <span class="meta-value">
                            <span class="engagement-badge {engagement_class}">{stats['avg_engagement_rate']:.2f}%</span>
                        </span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Views</span>
                        <span class="meta-value">{format_number(stats['total_views'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Likes</span>
                        <span class="meta-value">{format_number(stats['total_likes'])}</span>
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
            <div class="table-container">
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
                            <th>Date</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
'''
        
        for j, video in enumerate(stats['videos'], 1):
            engagement_class_video = get_engagement_class(video['engagement_rate'])
            html += f'''                        <tr>
                            <td class="video-rank">#{j}</td>
                            <td class="account-name">{video['account']}</td>
                            <td class="metric-value">{format_number(video['views'])}</td>
                            <td class="metric-value">{format_number(video['likes'])}</td>
                            <td class="metric-value">{format_number(video['comments'])}</td>
                            <td class="metric-value">{format_number(video['shares'])}</td>
                            <td><span class="engagement-badge {engagement_class_video}">{video['engagement_rate']:.2f}%</span></td>
                            <td>{video['upload_date']}</td>
                            <td><a href="{video['url']}" class="video-link" target="_blank">View →</a></td>
                        </tr>
'''
        
        html += '''                    </tbody>
                </table>
            </div>
        </div>
'''
    
    html += '''
        </div>
        <!-- End Sounds Tab -->

        <!-- Pages Tab -->
        <div id="pages-tab" class="tab-content">
'''
    
    # Generate account sections
    for i, (account, stats) in enumerate(sorted_accounts, 1):
        engagement_class = get_engagement_class(stats['avg_engagement_rate'])
        
        html += f'''
        <div class="sound-section">
            <div class="sound-header">
                <div class="sound-title-row">
                    <span class="sound-rank">{i}</span>
                    <div>
                        <div class="sound-title">{account}</div>
                        <div class="sound-artist">{len(stats['songs_list'])} unique songs</div>
                    </div>
                </div>
                <div class="sound-meta">
                    <div class="meta-item">
                        <span class="meta-label">Total Videos</span>
                        <span class="meta-value">{stats['total_videos']}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Views</span>
                        <span class="meta-value">{format_number(stats['total_views'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Likes</span>
                        <span class="meta-value">{format_number(stats['total_likes'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Comments</span>
                        <span class="meta-value">{format_number(stats['total_comments'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Total Shares</span>
                        <span class="meta-value">{format_number(stats['total_shares'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Avg Engagement</span>
                        <span class="meta-value">
                            <span class="engagement-badge {engagement_class}">{stats['avg_engagement_rate']:.2f}%</span>
                        </span>
                    </div>
                </div>
                <div class="accounts-used">
                    <div class="accounts-label">Songs used ({len(stats['songs_list'])}):</div>
                    <div class="account-tags">
'''
        
        for song_info in stats['songs_list']:
            html += f'                        <span class="account-tag">{song_info["song"]} ({song_info["count"]}x)</span>\n'
        
        html += '''                    </div>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Song</th>
                            <th>Artist</th>
                            <th>Views</th>
                            <th>Likes</th>
                            <th>Comments</th>
                            <th>Shares</th>
                            <th>Engagement</th>
                            <th>Date</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
'''
        
        for j, video in enumerate(stats['videos'], 1):
            engagement_class_video = get_engagement_class(video['engagement_rate'])
            html += f'''                        <tr>
                            <td class="video-rank">#{j}</td>
                            <td>{video['song']}</td>
                            <td>{video['artist']}</td>
                            <td class="metric-value">{format_number(video['views'])}</td>
                            <td class="metric-value">{format_number(video['likes'])}</td>
                            <td class="metric-value">{format_number(video['comments'])}</td>
                            <td class="metric-value">{format_number(video['shares'])}</td>
                            <td><span class="engagement-badge {engagement_class_video}">{video['engagement_rate']:.2f}%</span></td>
                            <td>{video['upload_date']}</td>
                            <td><a href="{video['url']}" class="video-link" target="_blank">View →</a></td>
                        </tr>
'''
        
        html += '''                    </tbody>
                </table>
            </div>
        </div>
'''
    
    html += '''
        </div>
        <!-- End Pages Tab -->
'''
    
    html += f'''
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p style="margin-top: 0.5rem;">Warner Sound Tracker - Complete Usage Report</p>
        </div>
    </div>

    <script>
        function switchToTab(tabName) {{
            // Hide all tab contents
            const allTabs = document.querySelectorAll('.tab-content');
            allTabs.forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Remove active class from all buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {{
                targetTab.classList.add('active');
            }}
            
            // Add active class to corresponding button
            const targetButton = document.querySelector(`.tab-button[data-tab="${{tabName}}"]`);
            if (targetButton) {{
                targetButton.classList.add('active');
            }}
            
            // Save to sessionStorage
            sessionStorage.setItem('activeTab', tabName);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            // Restore active tab from sessionStorage
            const savedTab = sessionStorage.getItem('activeTab');
            if (savedTab) {{
                switchToTab(savedTab);
            }}
            
            // Get all tab buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            
            // Add click event listeners to each button
            tabButtons.forEach(button => {{
                button.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const tabName = this.getAttribute('data-tab');
                    switchToTab(tabName);
                }});
            }});
        }});
    </script>
</body>
</html>
'''
    
    return html


def main():
    """Main function"""
    print("=" * 60)
    print("Warner Sound Usage Report - HTML Generator")
    print("=" * 60)
    print(f"📂 Reading CSV: {CSV_FILE}")
    
    # Load data
    videos = load_csv_data()
    print(f"✅ Loaded {len(videos)} videos")
    
    # Aggregate by sound
    print("📊 Aggregating data by song...")
    sound_stats = aggregate_by_sound(videos)
    print(f"✅ Found {len(sound_stats)} unique songs")
    
    # Aggregate by account
    print("📊 Aggregating data by account...")
    account_stats = aggregate_by_account(videos)
    print(f"✅ Found {len(account_stats)} accounts")
    
    # Generate HTML
    print("🎨 Generating HTML...")
    html = generate_html(sound_stats, account_stats, videos)
    
    # Save to file
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML generated: {OUTPUT_FILE}")
    print(f"\n🌐 View at: http://localhost:8000/output/{OUTPUT_FILE.name}")
    print(f"💡 Run: python3 preview_server.py")
    print("=" * 60)


if __name__ == '__main__':
    main()

