#!/usr/bin/env python3
"""
Generate HTML Report from CSV Data
Creates a self-contained, email-ready HTML report from CSV data
"""

import csv
import base64
from collections import defaultdict
from pathlib import Path
import sys
import re

# Import configuration and utilities
try:
    import config
    import fetch_album_art
except ImportError:
    print("ERROR: config.py not found. Please ensure config.py exists.")
    sys.exit(1)

def normalize_song_title(title):
    """Normalize song title to combine similar versions"""
    if not title or title == 'Unknown':
        return title
    
    # Remove common version indicators in parentheses
    title = re.sub(r'\s*\([^)]*version[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*remix[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*edit[^)]*\)', '', title, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    title = ' '.join(title.split())
    
    return title

def normalize_artist_name(artist):
    """Normalize artist name"""
    if not artist or artist == 'Unknown':
        return artist
    
    # Remove extra whitespace
    artist = ' '.join(artist.split())
    
    return artist

def image_to_base64(image_path):
    """Convert image file to base64 data URI"""
    if not image_path or not Path(image_path).exists():
        return None
    
    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            # Determine MIME type from file extension
            ext = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            return f"data:{mime_type};base64,{img_base64}"
    except Exception as e:
        print(f"  ⚠️  Error converting image to base64: {e}")
        return None

def read_csv_data(csv_path):
    """Read and parse CSV file into video data structure"""
    videos = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse numeric values
                views = int(row.get('Views', 0) or 0)
                likes = int(row.get('Likes', 0) or 0)
                comments = int(row.get('Comments', 0) or 0)
                shares = int(row.get('Shares', 0) or 0)
                engagement_rate = float(row.get('Engagement Rate (%)', 0) or 0)
                
                song = row.get('Song Name', 'Unknown').strip()
                artist = row.get('Artist', 'Unknown').strip()
                
                # Normalize song and artist
                normalized_song = normalize_song_title(song)
                normalized_artist = normalize_artist_name(artist)
                
                video = {
                    'account': row.get('Account', '').strip(),
                    'url': row.get('Video URL', '').strip(),
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'shares': shares,
                    'engagement_rate': engagement_rate,
                    'upload_date': row.get('Upload Date', '').strip(),
                    'song': song,
                    'artist': artist,
                    'original_song': song,
                    'original_artist': artist,
                    'music_id': row.get('Sound ID', '').strip(),
                    'sound_key': f"{normalized_song} - {normalized_artist}",
                    'caption': row.get('Video Caption', '').strip()
                }
                
                videos.append(video)
            except Exception as e:
                print(f"  ⚠️  Error parsing row: {e}")
                continue
    
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
        sound_stats[sound_key]['song'] = video.get('original_song', video['song'])
        sound_stats[sound_key]['artist'] = video.get('original_artist', video['artist'])

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

def aggregate_by_account(all_videos, sound_stats):
    """Aggregate videos by account for the account tab"""
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
    
    # Get all videos from sound_stats
    for stats in sound_stats.values():
        for video in stats['videos']:
            account = video['account']
            sound_key = video['sound_key']
            
            account_stats[account]['total_videos'] += 1
            account_stats[account]['total_views'] += video['views']
            account_stats[account]['total_likes'] += video['likes']
            account_stats[account]['total_comments'] += video['comments']
            account_stats[account]['total_shares'] += video['shares']
            account_stats[account]['total_engagement'] += video['engagement_rate']
            account_stats[account]['videos'].append(video)
            account_stats[account]['unique_sounds'].add(sound_key)
    
    # Calculate averages and sort videos
    for account, stats in account_stats.items():
        video_count = stats['total_videos']
        stats['avg_views'] = stats['total_views'] // video_count if video_count > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // video_count if video_count > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // video_count if video_count > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // video_count if video_count > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / video_count if video_count > 0 else 0
        
        # Sort videos by views (descending)
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)
        
        # Count unique sounds
        stats['unique_sounds_count'] = len(stats['unique_sounds'])
    
    return account_stats

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

def generate_combined_html(sound_stats, all_videos, csv_filename):
    """Generate single-page HTML report with collapsible sections and sidebar"""
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)
    
    # Calculate totals
    filtered_videos = []
    for stats in sound_stats.values():
        filtered_videos.extend(stats['videos'])
    
    total_views = sum(v['views'] for v in filtered_videos)
    total_likes = sum(v['likes'] for v in filtered_videos)
    total_comments = sum(v['comments'] for v in filtered_videos)
    total_shares = sum(v['shares'] for v in filtered_videos)
    total_video_count = len(filtered_videos)
    
    # Get unique accounts
    unique_accounts = set()
    for video in filtered_videos:
        unique_accounts.add(video['account'])
    
    # Aggregate by account
    account_stats = aggregate_by_account(all_videos, sound_stats)
    sorted_accounts = sorted(account_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)
    
    # Fetch and embed album art
    print("\n🎨 Fetching and embedding album art...")
    album_art_base64 = {}
    for sound_key, stats in sound_stats.items():
        song = stats['song']
        artist = stats['artist']
        
        if song and artist and song != 'Unknown' and artist != 'Unknown':
            try:
                art_path = fetch_album_art.get_album_art(song, artist)
                if art_path:
                    base64_data = image_to_base64(art_path)
                    if base64_data:
                        album_art_base64[sound_key] = base64_data
            except:
                pass

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics Dashboard - {Path(csv_filename).stem}</title>
    <style>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background: var(--light-sand);
            color: var(--charcoal);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            margin: 0;
            padding: 0;
        }}

        /* Mobile-first: Stack vertically by default */
        .app-container {{
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}

        /* Sidebar - Hidden on mobile, shown on desktop */
        .sidebar {{
            width: 100%;
            background: var(--white);
            border-bottom: 1px solid var(--gray-200);
            display: flex;
            flex-direction: column;
            max-height: 40vh;
            overflow-y: auto;
            flex-shrink: 0;
        }}

        .sidebar-header {{
            padding: 1rem;
            border-bottom: 1px solid var(--gray-200);
            position: sticky;
            top: 0;
            background: var(--white);
            z-index: 10;
        }}

        .sidebar-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
        }}

        .sidebar-subtitle {{
            font-size: 0.75rem;
            color: var(--gray-600);
        }}

        .nav-section {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--gray-200);
        }}
        
        .nav-section:last-child {{
            border-bottom: none;
        }}

        .nav-section-title {{
            font-size: 0.6875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--gray-500);
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}

        .nav-list {{
            list-style: none;
            max-height: 200px;
            overflow-y: auto;
        }}

        .nav-item {{
            margin-bottom: 0.375rem;
        }}

        .nav-link {{
            display: block;
            padding: 0.5rem;
            color: var(--gray-700);
            text-decoration: none;
            font-size: 0.8125rem;
            border-radius: 4px;
            transition: all 0.2s ease;
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .nav-link:hover {{
            background: var(--gray-100);
            color: var(--charcoal);
        }}

        .nav-link.active {{
            background: var(--accent);
            color: var(--white);
        }}

        /* Main Content */
        .main-content {{
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            min-width: 0;
            width: 100%;
        }}

        .header {{
            padding: 1rem;
            border-bottom: 1px solid var(--gray-200);
            background: var(--white);
            position: sticky;
            top: 0;
            z-index: 5;
        }}

        h1 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--charcoal);
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }}

        .subtitle {{
            font-size: 0.8125rem;
            color: var(--gray-600);
            font-weight: 400;
        }}

        .stats-summary {{
            background: var(--white);
            border-bottom: 1px solid var(--gray-200);
            padding: 1rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }}

        .stat-card {{
            background: var(--gray-50);
            border: 1px solid var(--gray-200);
            padding: 0.75rem;
        }}

        .stat-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
        }}

        .stat-label {{
            font-size: 0.6875rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .content-area {{
            padding: 1rem;
        }}
        
        .section-divider {{
            margin: 2rem 0;
            padding: 1rem 0;
            border-top: 2px solid var(--gray-300);
            border-bottom: 2px solid var(--gray-300);
        }}
        
        .section-divider h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
        }}
        
        .section-divider p {{
            font-size: 0.75rem;
            color: var(--gray-600);
        }}

        /* Collapsible Sections */
        .collapsible-section {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            margin-bottom: 1rem;
        }}

        .collapsible-header {{
            padding: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: background 0.2s ease;
            user-select: none;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .collapsible-header:hover {{
            background: var(--gray-50);
        }}

        .collapsible-header.active {{
            background: var(--gray-50);
            border-bottom: 1px solid var(--gray-200);
        }}

        .collapsible-title {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
            min-width: 0;
            overflow: hidden;
        }}

        .collapsible-icon {{
            width: 12px;
            height: 12px;
            transition: transform 0.3s ease;
        }}

        .collapsible-header.active .collapsible-icon {{
            transform: rotate(90deg);
        }}

        .collapsible-content {{
            display: none;
            overflow: hidden;
        }}

        .collapsible-content.active {{
            display: block;
            animation: slideDown 0.3s ease-out;
        }}
        
        @keyframes slideDown {{
            from {{
                opacity: 0;
                max-height: 0;
            }}
            to {{
                opacity: 1;
                max-height: 10000px;
            }}
        }}

        .collapsible-body {{
            padding: 1rem;
        }}

        /* Sound Section Styles */
        .sound-header-content {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
            min-width: 0;
        }}

        .sound-rank {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent);
            min-width: 1.5rem;
            flex-shrink: 0;
        }}

        .album-art-container {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex: 1;
            min-width: 0;
        }}

        .album-art {{
            width: 50px;
            height: 50px;
            object-fit: cover;
            border: 1px solid var(--gray-200);
            flex-shrink: 0;
        }}

        .sound-info {{
            flex: 1;
            min-width: 0;
        }}

        .sound-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.125rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .sound-artist {{
            font-size: 0.75rem;
            color: var(--gray-600);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .sound-meta {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}

        .meta-value {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--charcoal);
            white-space: nowrap;
        }}

        /* Account Section Styles */
        .account-name {{
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--charcoal);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Video Table */
        .table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-top: 1rem;
        }}

        .video-table {{
            width: 100%;
            min-width: 800px;
            border-collapse: collapse;
        }}

        .video-table th {{
            background: var(--gray-50);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--gray-200);
            white-space: nowrap;
        }}

        .video-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--gray-200);
            font-size: 0.9375rem;
            white-space: nowrap;
        }}

        .video-table tr:hover {{
            background: var(--gray-50);
        }}

        .video-link {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
        }}

        .video-link:hover {{
            text-decoration: underline;
        }}

        .engagement-high {{ color: #059669; }}
        .engagement-medium {{ color: #d97706; }}
        .engagement-low {{ color: #dc2626; }}

        /* Footer */
        .footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--gray-200);
            text-align: center;
            color: var(--gray-600);
            font-size: 0.875rem;
        }}

        /* Desktop - Side by side layout */
        @media (min-width: 769px) {{
            .app-container {{
                flex-direction: row;
            }}

            .sidebar {{
                width: 280px;
                max-height: 100vh;
                border-right: 1px solid var(--gray-200);
                border-bottom: none;
            }}

            .header {{
                padding: 2rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .subtitle {{
                font-size: 0.9375rem;
            }}

            .stats-summary {{
                padding: 1.5rem 2rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
            }}

            .stat-card {{
                padding: 1rem;
            }}

            .stat-value {{
                font-size: 1.5rem;
            }}

            .stat-label {{
                font-size: 0.75rem;
            }}

            .content-area {{
                padding: 2rem;
            }}

            .sidebar-header {{
                padding: 1.5rem;
            }}

            .sidebar-title {{
                font-size: 1.25rem;
            }}

            .sidebar-subtitle {{
                font-size: 0.875rem;
            }}

            .nav-section {{
                padding: 1rem 1.5rem;
            }}

            .nav-section-title {{
                font-size: 0.75rem;
            }}

            .nav-link {{
                font-size: 0.875rem;
                padding: 0.5rem 0.75rem;
            }}

            .nav-list {{
                max-height: none;
            }}

            .collapsible-header {{
                padding: 1.25rem 1.5rem;
                flex-wrap: nowrap;
            }}

            .collapsible-body {{
                padding: 1.5rem;
            }}

            .sound-rank {{
                font-size: 1.25rem;
                min-width: 2rem;
            }}

            .album-art {{
                width: 60px;
                height: 60px;
            }}

            .sound-title {{
                font-size: 1.25rem;
            }}

            .sound-artist {{
                font-size: 0.875rem;
            }}

            .sound-meta {{
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 1rem;
            }}

            .meta-value {{
                font-size: 1.125rem;
            }}

            .account-name {{
                font-size: 1.5rem;
            }}

            .video-table {{
                min-width: 800px;
                font-size: 0.9375rem;
            }}

            .video-table th {{
                padding: 0.75rem;
                font-size: 0.875rem;
            }}

            .video-table td {{
                padding: 0.75rem;
                font-size: 0.9375rem;
            }}

            .section-divider {{
                margin: 3rem 0;
                padding: 1.5rem 0;
            }}

            .section-divider h2 {{
                font-size: 1.75rem;
            }}

            .section-divider p {{
                font-size: 0.875rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="app-container">
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">Navigation</div>
            <div class="sidebar-subtitle">{len(unique_accounts)} accounts</div>
        </div>
        
        <div class="nav-section">
            <div class="nav-section-title">Sounds ({len(sorted_sounds)})</div>
            <ul class="nav-list">
'''
    
    # Add sound navigation items
    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        song = stats['song']
        artist = stats['artist']
        safe_id = f"sound-{i}"
        html += f'''                <li class="nav-item">
                    <a class="nav-link" href="#{safe_id}" onclick="scrollToSection('{safe_id}'); return false;">{i}. {song}</a>
                </li>
'''
    
    html += '''            </ul>
        </div>

        <div class="nav-section">
            <div class="nav-section-title">Accounts (''' + str(len(sorted_accounts)) + ''')</div>
            <ul class="nav-list">
'''
    
    # Add account navigation items
    for i, (account, stats) in enumerate(sorted_accounts, 1):
        safe_id = f"account-{i}"
        html += f'''                <li class="nav-item">
                    <a class="nav-link" href="#{safe_id}" onclick="scrollToSection('{safe_id}'); return false;">{account}</a>
                </li>
'''
    
    html += f'''            </ul>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
            <h1>Analytics Dashboard</h1>
            <div class="subtitle">Performance metrics from {len(unique_accounts)} TikTok accounts | Generated from {Path(csv_filename).name}</div>
        </div>

        <div class="stats-summary">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(unique_accounts)}</div>
                    <div class="stat-label">Accounts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sound_stats)}</div>
                    <div class="stat-label">Unique Sounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_video_count)}</div>
                    <div class="stat-label">Total Videos</div>
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

        <div class="content-area">
            <!-- Sounds Section -->
            <div class="section-divider">
                <h2>Sounds</h2>
                <p>{len(sorted_sounds)} unique sounds sorted by total views</p>
            </div>
'''
    
    # Add sound sections (collapsible)
    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        engagement_class = get_engagement_class(stats['avg_engagement_rate'])
        safe_id = f"sound-{i}"
        
        # Get album art
        album_art_html = ''
        if sound_key in album_art_base64:
            album_art_html = f'<img src="{album_art_base64[sound_key]}" alt="{stats["song"]} - {stats["artist"]}" class="album-art">'
        
        html += f'''
                <div class="collapsible-section" id="{safe_id}">
                    <div class="collapsible-header" onclick="toggleSection('{safe_id}')">
                        <div class="collapsible-title">
                            <svg class="collapsible-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                            </svg>
                            <div class="sound-header-content">
                                <span class="sound-rank">{i}</span>
                                <div class="album-art-container">
                                    {album_art_html}
                                    <div class="sound-info">
                                        <div class="sound-title">{stats['song']}</div>
                                        <div class="sound-artist">{stats['artist']}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="meta-value">{format_number(stats['total_views'])} views</div>
                    </div>
                    <div class="collapsible-content" id="{safe_id}-content">
                        <div class="collapsible-body">
                            <div class="sound-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Total Uses</span>
                                    <span class="meta-value">{stats['total_uses']}</span>
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
                                    <span class="meta-label">Avg Views</span>
                                    <span class="meta-value">{format_number(stats['avg_views'])}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Avg Engagement</span>
                                    <span class="meta-value {engagement_class}">{stats['avg_engagement_rate']:.2f}%</span>
                                </div>
                            </div>
                            <div class="table-wrapper">
                                <table class="video-table">
                                    <thead>
                                        <tr>
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
        
        # Sort videos by views
        sorted_videos = sorted(stats['videos'], key=lambda x: x['views'], reverse=True)
        for video in sorted_videos:
            engagement_class_vid = get_engagement_class(video['engagement_rate'])
            html += f'''
                                        <tr>
                                            <td>{video['account']}</td>
                                            <td>{format_number(video['views'])}</td>
                                            <td>{format_number(video['likes'])}</td>
                                            <td>{format_number(video['comments'])}</td>
                                            <td>{format_number(video['shares'])}</td>
                                            <td class="{engagement_class_vid}">{video['engagement_rate']:.2f}%</td>
                                            <td>{video['upload_date']}</td>
                                            <td><a href="{video['url']}" class="video-link" target="_blank">View</a></td>
                                        </tr>
'''
        
        html += '''                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
'''
    
    html += f'''
            <!-- Accounts Section -->
            <div class="section-divider">
                <h2>Accounts</h2>
                <p>{len(sorted_accounts)} accounts sorted by total views</p>
            </div>
'''
    
    # Add account sections (collapsible)
    for i, (account, stats) in enumerate(sorted_accounts, 1):
        safe_id = f"account-{i}"
        html += f'''
                <div class="collapsible-section" id="{safe_id}">
                    <div class="collapsible-header" onclick="toggleSection('{safe_id}')">
                        <div class="collapsible-title">
                            <svg class="collapsible-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                            </svg>
                            <div class="account-name">{account}</div>
                        </div>
                        <div class="meta-value">{format_number(stats['total_views'])} views</div>
                    </div>
                    <div class="collapsible-content" id="{safe_id}-content">
                        <div class="collapsible-body">
                            <div class="sound-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Total Videos</span>
                                    <span class="meta-value">{stats['total_videos']}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Unique Sounds</span>
                                    <span class="meta-value">{stats['unique_sounds_count']}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Total Views</span>
                                    <span class="meta-value">{format_number(stats['total_views'])}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Avg Views</span>
                                    <span class="meta-value">{format_number(stats['avg_views'])}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Avg Engagement</span>
                                    <span class="meta-value {get_engagement_class(stats['avg_engagement_rate'])}">{stats['avg_engagement_rate']:.2f}%</span>
                                </div>
                            </div>
                            <div class="table-wrapper">
                                <table class="video-table">
                                    <thead>
                                        <tr>
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
        for video in stats['videos']:
            engagement_class_vid = get_engagement_class(video['engagement_rate'])
            html += f'''
                                        <tr>
                                            <td>{video['song']}</td>
                                            <td>{video['artist']}</td>
                                            <td>{format_number(video['views'])}</td>
                                            <td>{format_number(video['likes'])}</td>
                                            <td>{format_number(video['comments'])}</td>
                                            <td>{format_number(video['shares'])}</td>
                                            <td class="{engagement_class_vid}">{video['engagement_rate']:.2f}%</td>
                                            <td>{video['upload_date']}</td>
                                            <td><a href="{video['url']}" class="video-link" target="_blank">View</a></td>
                                        </tr>
'''
        html += '''                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
'''
    
    html += f'''            </div>

            <div class="footer">
                <p>Report generated from {Path(csv_filename).name}</p>
                <p>Total: {total_video_count} videos | {format_number(total_views)} views | {len(sound_stats)} unique sounds</p>
            </div>
        </div>
    </div>

    <script>
        function toggleSection(sectionId) {{
            const section = document.getElementById(sectionId);
            if (!section) {{
                console.error('Section not found:', sectionId);
                return false;
            }}
            
            const header = section.querySelector('.collapsible-header');
            const content = document.getElementById(sectionId + '-content');
            
            if (!header || !content) {{
                console.error('Header or content not found for:', sectionId);
                return false;
            }}
            
            const isActive = header.classList.contains('active');
            
            if (isActive) {{
                header.classList.remove('active');
                content.classList.remove('active');
            }} else {{
                header.classList.add('active');
                content.classList.add('active');
            }}
            
            return false;
        }}

        function scrollToSection(sectionId) {{
            const section = document.getElementById(sectionId);
            if (section) {{
                section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                // Expand the section
                const header = section.querySelector('.collapsible-header');
                const content = document.getElementById(sectionId + '-content');
                if (header && content && !header.classList.contains('active')) {{
                    header.classList.add('active');
                    content.classList.add('active');
                }}
            }}
            return false;
        }}
        
        // Ensure DOM is loaded
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('Report loaded successfully');
            }});
        }} else {{
            console.log('Report already loaded');
        }}
    </script>
    </div>
</body>
</html>
'''
    
    return html

def generate_sounds_html(sound_stats, all_videos, csv_filename):
    """Generate self-contained HTML report for sounds"""
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)
    
    # Calculate totals
    filtered_videos = []
    for stats in sound_stats.values():
        filtered_videos.extend(stats['videos'])
    
    total_views = sum(v['views'] for v in filtered_videos)
    total_likes = sum(v['likes'] for v in filtered_videos)
    total_comments = sum(v['comments'] for v in filtered_videos)
    total_shares = sum(v['shares'] for v in filtered_videos)
    total_video_count = len(filtered_videos)
    
    # Get unique accounts
    unique_accounts = set()
    for video in filtered_videos:
        unique_accounts.add(video['account'])
    
    # Fetch and embed album art
    print("\n🎨 Fetching and embedding album art...")
    album_art_base64 = {}
    for sound_key, stats in sound_stats.items():
        song = stats['song']
        artist = stats['artist']
        
        if song and artist and song != 'Unknown' and artist != 'Unknown':
            try:
                art_path = fetch_album_art.get_album_art(song, artist)
                if art_path:
                    base64_data = image_to_base64(art_path)
                    if base64_data:
                        album_art_base64[sound_key] = base64_data
            except:
                pass

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sounds Report - {Path(csv_filename).stem}</title>
    <style>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
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
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.5rem;
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Sound Sections */
        .sound-section {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            margin-bottom: 2rem;
            padding: 2rem;
        }}

        .sound-header {{
            margin-bottom: 1.5rem;
        }}

        .sound-title-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .sound-rank {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent);
            min-width: 3rem;
        }}

        .album-art-container {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
        }}

        .album-art {{
            width: 80px;
            height: 80px;
            object-fit: cover;
            border: 1px solid var(--gray-200);
        }}

        .sound-info {{
            flex: 1;
        }}

        .sound-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.25rem;
        }}

        .sound-artist {{
            font-size: 1rem;
            color: var(--gray-600);
        }}

        .sound-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}

        .meta-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--charcoal);
        }}

        /* Video Table */
        .table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-top: 1.5rem;
        }}

        .video-table {{
            width: 100%;
            min-width: 800px;
            border-collapse: collapse;
        }}

        .video-table th {{
            background: var(--gray-50);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--gray-200);
            white-space: nowrap;
        }}

        .video-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--gray-200);
            font-size: 0.9375rem;
            white-space: nowrap;
        }}

        .video-table tr:hover {{
            background: var(--gray-50);
        }}

        .video-link {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
        }}

        .video-link:hover {{
            text-decoration: underline;
        }}

        .engagement-high {{ color: #059669; }}
        .engagement-medium {{ color: #d97706; }}
        .engagement-low {{ color: #dc2626; }}

        /* Account Section */
        .account-section {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            margin-bottom: 2rem;
            padding: 2rem;
        }}

        .account-header {{
            margin-bottom: 1.5rem;
        }}

        .account-name {{
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 1rem;
        }}

        /* Footer */
        .footer {{
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--gray-200);
            text-align: center;
            color: var(--gray-600);
            font-size: 0.875rem;
        }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 1.75rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }}

            .stat-card {{
                padding: 1rem;
            }}

            .stat-value {{
                font-size: 1.5rem;
            }}

            .sound-section, .account-section {{
                padding: 1rem;
            }}

            .sound-title {{
                font-size: 1.25rem;
            }}

            .sound-meta {{
                grid-template-columns: repeat(2, 1fr);
                gap: 0.75rem;
            }}

            .video-table {{
                font-size: 0.8125rem;
            }}

            .video-table th,
            .video-table td {{
                padding: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sound Analytics Dashboard</h1>
            <div class="subtitle">Performance metrics from {len(unique_accounts)} TikTok accounts | Generated from {Path(csv_filename).name}</div>
        </div>

        <div class="stats-summary">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(unique_accounts)}</div>
                    <div class="stat-label">Accounts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sound_stats)}</div>
                    <div class="stat-label">Unique Sounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_video_count)}</div>
                    <div class="stat-label">Total Videos</div>
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

        <div style="margin-bottom: 2rem; padding: 1rem; background: var(--white); border: 1px solid var(--gray-200);">
            <a href="{Path(csv_filename).stem}_accounts_report.html" style="color: var(--accent); text-decoration: none; font-weight: 500;">← View Accounts Report</a>
        </div>
'''

    # Add sound sections
    for i, (sound_key, stats) in enumerate(sorted_sounds, 1):
        engagement_class = get_engagement_class(stats['avg_engagement_rate'])
        
        # Get album art (base64 embedded)
        album_art_html = ''
        if sound_key in album_art_base64:
            album_art_html = f'<img src="{album_art_base64[sound_key]}" alt="{stats["song"]} - {stats["artist"]}" class="album-art">'
        
        html += f'''
            <div class="sound-section">
                <div class="sound-header">
                    <div class="sound-title-row">
                        <span class="sound-rank">{i}</span>
                        <div class="album-art-container">
                            {album_art_html}
                            <div class="sound-info">
                                <div class="sound-title">{stats['song']}</div>
                                <div class="sound-artist">{stats['artist']}</div>
                            </div>
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
                            <span class="meta-value {engagement_class}">{stats['avg_engagement_rate']:.2f}%</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Total Views</span>
                            <span class="meta-value">{format_number(stats['total_views'])}</span>
                        </div>
                    </div>
                </div>
                <div class="table-wrapper">
                    <table class="video-table">
                        <thead>
                            <tr>
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
        for video in stats['videos'][:10]:  # Show top 10 videos per sound
            engagement_class = get_engagement_class(video['engagement_rate'])
            html += f'''
                            <tr>
                                <td>{video['account']}</td>
                                <td>{format_number(video['views'])}</td>
                                <td>{format_number(video['likes'])}</td>
                                <td>{format_number(video['comments'])}</td>
                                <td>{format_number(video['shares'])}</td>
                                <td class="{engagement_class}">{video['engagement_rate']:.2f}%</td>
                                <td>{video['upload_date']}</td>
                                <td><a href="{video['url']}" class="video-link" target="_blank">View</a></td>
                            </tr>
'''
        html += '''
                        </tbody>
                    </table>
                </div>
            </div>
'''
    
    html += f'''
        <div class="footer">
            <p>Report generated from {Path(csv_filename).name}</p>
            <p>Total: {total_video_count} videos | {format_number(total_views)} views | {len(sound_stats)} unique sounds</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html

def generate_accounts_html(sound_stats, all_videos, csv_filename):
    """Generate self-contained HTML report for accounts"""
    # Calculate totals
    filtered_videos = []
    for stats in sound_stats.values():
        filtered_videos.extend(stats['videos'])
    
    total_views = sum(v['views'] for v in filtered_videos)
    total_likes = sum(v['likes'] for v in filtered_videos)
    total_comments = sum(v['comments'] for v in filtered_videos)
    total_shares = sum(v['shares'] for v in filtered_videos)
    total_video_count = len(filtered_videos)
    
    # Get unique accounts
    unique_accounts = set()
    for video in filtered_videos:
        unique_accounts.add(video['account'])
    
    # Aggregate by account
    account_stats = aggregate_by_account(all_videos, sound_stats)
    sorted_accounts = sorted(account_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accounts Report - {Path(csv_filename).stem}</title>
    <style>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
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
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 0.5rem;
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Account Section */
        .account-section {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            margin-bottom: 2rem;
            padding: 2rem;
        }}

        .account-header {{
            margin-bottom: 1.5rem;
        }}

        .account-name {{
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 1rem;
        }}

        .sound-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}

        .meta-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--charcoal);
        }}

        /* Video Table */
        .table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-top: 1.5rem;
        }}

        .video-table {{
            width: 100%;
            min-width: 800px;
            border-collapse: collapse;
        }}

        .video-table th {{
            background: var(--gray-50);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--gray-200);
            white-space: nowrap;
        }}

        .video-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--gray-200);
            font-size: 0.9375rem;
            white-space: nowrap;
        }}

        .video-table tr:hover {{
            background: var(--gray-50);
        }}

        .video-link {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
        }}

        .video-link:hover {{
            text-decoration: underline;
        }}

        .engagement-high {{ color: #059669; }}
        .engagement-medium {{ color: #d97706; }}
        .engagement-low {{ color: #dc2626; }}

        /* Footer */
        .footer {{
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--gray-200);
            text-align: center;
            color: var(--gray-600);
            font-size: 0.875rem;
        }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 1.75rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }}

            .stat-card {{
                padding: 1rem;
            }}

            .stat-value {{
                font-size: 1.5rem;
            }}

            .account-section {{
                padding: 1rem;
            }}

            .sound-meta {{
                grid-template-columns: repeat(2, 1fr);
                gap: 0.75rem;
            }}

            .video-table {{
                font-size: 0.8125rem;
            }}

            .video-table th,
            .video-table td {{
                padding: 0.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Accounts Performance Report</h1>
            <div class="subtitle">Performance metrics from {len(unique_accounts)} TikTok accounts | Generated from {Path(csv_filename).name}</div>
        </div>

        <div class="stats-summary">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(unique_accounts)}</div>
                    <div class="stat-label">Accounts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sound_stats)}</div>
                    <div class="stat-label">Unique Sounds</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{format_number(total_video_count)}</div>
                    <div class="stat-label">Total Videos</div>
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

        <div style="margin-bottom: 2rem; padding: 1rem; background: var(--white); border: 1px solid var(--gray-200);">
            <a href="{Path(csv_filename).stem}_sounds_report.html" style="color: var(--accent); text-decoration: none; font-weight: 500;">← View Sounds Report</a>
        </div>
'''
    
    # Add account sections
    for account, stats in sorted_accounts:
        html += f'''
            <div class="account-section">
                <div class="account-header">
                    <div class="account-name">{account}</div>
                    <div class="sound-meta">
                        <div class="meta-item">
                            <span class="meta-label">Total Videos</span>
                            <span class="meta-value">{stats['total_videos']}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Unique Sounds</span>
                            <span class="meta-value">{stats['unique_sounds_count']}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Total Views</span>
                            <span class="meta-value">{format_number(stats['total_views'])}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Avg Views</span>
                            <span class="meta-value">{format_number(stats['avg_views'])}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Avg Engagement</span>
                            <span class="meta-value {get_engagement_class(stats['avg_engagement_rate'])}">{stats['avg_engagement_rate']:.2f}%</span>
                        </div>
                    </div>
                </div>
                <div class="table-wrapper">
                    <table class="video-table">
                        <thead>
                            <tr>
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
        for video in stats['videos']:  # Show all videos per account
            engagement_class = get_engagement_class(video['engagement_rate'])
            html += f'''
                            <tr>
                                <td>{video['song']}</td>
                                <td>{video['artist']}</td>
                                <td>{format_number(video['views'])}</td>
                                <td>{format_number(video['likes'])}</td>
                                <td>{format_number(video['comments'])}</td>
                                <td>{format_number(video['shares'])}</td>
                                <td class="{engagement_class}">{video['engagement_rate']:.2f}%</td>
                                <td>{video['upload_date']}</td>
                                <td><a href="{video['url']}" class="video-link" target="_blank">View</a></td>
                            </tr>
'''
        html += '''
                        </tbody>
                    </table>
                </div>
            </div>
'''
    
    html += f'''
        <div class="footer">
            <p>Report generated from {Path(csv_filename).name}</p>
            <p>Total: {total_video_count} videos | {format_number(total_views)} views | {len(unique_accounts)} accounts</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate HTML report from CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('-o', '--output', help='Output HTML file path', default=None)
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        return
    
    print(f"Reading CSV data from: {csv_path}")
    videos = read_csv_data(csv_path)
    print(f"  Found {len(videos)} videos")
    
    print("\nAggregating data by sound...")
    sound_stats = aggregate_by_sound(videos)
    print(f"  Found {len(sound_stats)} unique sounds")
    
    # Determine output path
    base_name = csv_path.stem
    output_path = config.OUTPUT_DIR / f"{base_name}_report.html"
    
    print(f"\nGenerating Combined Report with Sidebar...")
    html_content = generate_combined_html(sound_stats, videos, str(csv_path))
    
    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n✅ Report generated:")
    print(f"   📊 Combined Report: {output_path}")
    print(f"      File size: {file_size:.2f} MB")
    print(f"\n   Summary: {len(sound_stats)} sounds | {len(videos)} videos | {len(set(v['account'] for v in videos))} accounts")

if __name__ == '__main__':
    main()

