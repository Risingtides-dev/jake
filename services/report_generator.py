"""
Report generation service that integrates generate_complete_html.py with database
"""

from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from config import OUTPUT_DIR
from services.database import get_videos_by_session, get_sounds_by_session, get_all_sessions


def format_number(num):
    """Format number with commas."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:,}"


def get_engagement_class(rate):
    """Get CSS class for engagement rate."""
    if rate >= 15:
        return 'engagement-high'
    elif rate >= 10:
        return 'engagement-medium'
    else:
        return 'engagement-low'


def generate_html_report(session_id: Optional[str] = None, sound_keys: Optional[List[str]] = None) -> str:
    """
    Generate HTML report from database data.
    
    Args:
        session_id: Session ID to generate report for (uses most recent if None)
        sound_keys: List of sound keys to include (includes all if None)
    
    Returns:
        HTML string
    """
    # Get session
    if not session_id:
        sessions = get_all_sessions(limit=1)
        if not sessions:
            return "<html><body><h1>No sessions found</h1></body></html>"
        session_id = sessions[0]['session_id']
    
    # Get videos
    filters = {}
    videos = get_videos_by_session(session_id, filters)
    
    # Filter by sound_keys if provided
    if sound_keys:
        sound_keys_set = set(sound_keys)
        videos = [v for v in videos if v.get('sound_key') in sound_keys_set]
    
    # Get sounds with aggregation
    sounds_data = get_sounds_by_session(session_id)
    
    # Build sound stats
    sound_stats = {}
    for sound in sounds_data:
        sound_key = sound['sound_key']
        if sound_keys and sound_key not in sound_keys:
            continue
        
        sound_stats[sound_key] = {
            'total_uses': sound['video_count'],
            'total_views': sound['total_views'] or 0,
            'total_likes': sound['total_likes'] or 0,
            'total_comments': sound['total_comments'] or 0,
            'total_shares': sound['total_shares'] or 0,
            'avg_views': sound['total_views'] // sound['video_count'] if sound['video_count'] > 0 else 0,
            'avg_likes': sound['total_likes'] // sound['video_count'] if sound['video_count'] > 0 else 0,
            'avg_comments': sound['total_comments'] // sound['video_count'] if sound['video_count'] > 0 else 0,
            'avg_shares': sound['total_shares'] // sound['video_count'] if sound['video_count'] > 0 else 0,
            'avg_engagement': sound['avg_engagement_rate'] or 0.0,
            'videos': [],
            'accounts': set(),
            'song': sound['song_title'],
            'artist': sound['artist_name']
        }
    
    # Add videos to sound stats
    for video in videos:
        sound_key = video.get('sound_key', 'Unknown Sound')
        if sound_key in sound_stats:
            sound_stats[sound_key]['videos'].append(video)
            sound_stats[sound_key]['accounts'].add(video.get('account', ''))
    
    # Convert accounts sets to lists
    for sound_key in sound_stats:
        sound_stats[sound_key]['accounts'] = sorted(list(sound_stats[sound_key]['accounts']))
        # Sort videos by engagement rate
        sound_stats[sound_key]['videos'].sort(key=lambda x: x.get('engagement_rate', 0), reverse=True)
    
    # Calculate totals
    total_views = sum(v.get('views', 0) for v in videos)
    total_likes = sum(v.get('likes', 0) for v in videos)
    total_comments = sum(v.get('comments', 0) for v in videos)
    total_shares = sum(v.get('shares', 0) for v in videos)
    
    # Sort sounds by total uses
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_uses'], reverse=True)
    
    # Generate HTML (using the same template structure as generate_complete_html.py)
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

        .sound-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .sound-stat {{
            display: flex;
            flex-direction: column;
        }}

        .sound-stat-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--charcoal);
        }}

        .sound-stat-label {{
            font-size: 0.75rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Video Table */
        .video-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
        }}

        .video-table th {{
            background: var(--gray-50);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.8125rem;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--gray-200);
        }}

        .video-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--gray-200);
        }}

        .video-table tr:hover {{
            background: var(--gray-50);
        }}

        .engagement-badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .engagement-high {{
            background: #dcfce7;
            color: #166534;
        }}

        .engagement-medium {{
            background: #fef3c7;
            color: #92400e;
        }}

        .engagement-low {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .video-link {{
            color: var(--accent);
            text-decoration: none;
        }}

        .video-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sound Analytics Dashboard</h1>
            <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-summary">
            <h2>Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{format_number(len(videos))}</div>
                    <div class="stat-label">Total Videos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(len(sorted_sounds))}</div>
                    <div class="stat-label">Unique Sounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_views)}</div>
                    <div class="stat-label">Total Views</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_likes)}</div>
                    <div class="stat-label">Total Likes</div>
                </div>
            </div>
        </div>
'''
    
    # Add sound sections
    for rank, (sound_key, stats) in enumerate(sorted_sounds, 1):
        html += f'''
        <div class="sound-section">
            <div class="sound-header">
                <div class="sound-title-row">
                    <span class="sound-rank">#{rank}</span>
                    <div>
                        <div class="sound-title">{stats['song']}</div>
                        <div class="sound-artist">{stats['artist']}</div>
                    </div>
                </div>
                <div class="sound-stats">
                    <div class="sound-stat">
                        <div class="sound-stat-value">{stats['total_uses']}</div>
                        <div class="sound-stat-label">Uses</div>
                    </div>
                    <div class="sound-stat">
                        <div class="sound-stat-value">{format_number(stats['total_views'])}</div>
                        <div class="sound-stat-label">Total Views</div>
                    </div>
                    <div class="sound-stat">
                        <div class="sound-stat-value">{format_number(stats['avg_views'])}</div>
                        <div class="sound-stat-label">Avg Views</div>
                    </div>
                    <div class="sound-stat">
                        <div class="sound-stat-value">{stats['avg_engagement']:.2f}%</div>
                        <div class="sound-stat-label">Avg Engagement</div>
                    </div>
                </div>
            </div>
            
            <table class="video-table">
                <thead>
                    <tr>
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
        
        # Add videos (top 10 per sound)
        for video in stats['videos'][:10]:
            engagement_rate = video.get('engagement_rate', 0)
            engagement_class = get_engagement_class(engagement_rate)
            html += f'''
                    <tr>
                        <td>{video.get('account', '')}</td>
                        <td>{format_number(video.get('views', 0))}</td>
                        <td>{format_number(video.get('likes', 0))}</td>
                        <td>{format_number(video.get('comments', 0))}</td>
                        <td>{format_number(video.get('shares', 0))}</td>
                        <td><span class="engagement-badge {engagement_class}">{engagement_rate:.2f}%</span></td>
                        <td><a href="{video.get('url', '#')}" target="_blank" class="video-link">View</a></td>
                    </tr>
'''
        
        html += '''
                </tbody>
            </table>
        </div>
'''
    
    html += '''
    </div>
</body>
</html>
'''
    
    return html


def save_html_report(session_id: Optional[str] = None, sound_keys: Optional[List[str]] = None, 
                    output_file: Optional[Path] = None) -> Path:
    """
    Generate and save HTML report to file.
    
    Returns:
        Path to saved HTML file
    """
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f'sound_usage_report_{timestamp}.html'
    
    html = generate_html_report(session_id, sound_keys)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file

