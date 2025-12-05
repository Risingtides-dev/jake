#!/usr/bin/env python3
"""
Generate Modern Glassmorphism HTML Sound Usage Report
Creates a clean, modern HTML report with earth tones and sleek design
"""

import subprocess
import re
from collections import defaultdict
import os
import sys
import json

# Import configuration
try:
    import config
    import fetch_album_art
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Use accounts from config
ACCOUNTS = config.ACCOUNTS

def normalize_song_title(title):
    """Normalize song title to combine similar versions"""
    if not title or title == 'Unknown':
        return title
    
    # Remove common version indicators in parentheses
    # e.g., "Rollin' Stone (Full Band Version)" -> "Rollin' Stone"
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

def extract_music_id_from_link(music_link):
    """Extract music ID from a TikTok music link"""
    if not music_link:
        return None
    match = re.search(r'-(\d+)(?:\?|$|&)', music_link)
    if not match:
        match = re.search(r'-(\d+)$', music_link.split('?')[0])
    return match.group(1) if match else None

def get_music_link_from_video_fast(video_url, track_name):
    """Try to get music link - optimized version that constructs from track name when possible"""
    # First, try to get from full video details (but with shorter timeout)
    try:
        cmd = [config.YT_DLP_CMD, '--dump-json', '--no-playlist', '--quiet', video_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            full_json_str = json.dumps(data)
            
            # Search for music URL in JSON
            music_urls = re.findall(r'https://www\.tiktok\.com/music/[^\"]+', full_json_str)
            if music_urls:
                return music_urls[0].split('?')[0]
    except:
        pass
    
    return None

def parse_video_data_from_json(json_data, account):
    """Parse video data directly from yt-dlp JSON output"""
    videos = []
    
    for line in json_data.strip().split('\n'):
        if not line:
            continue
        try:
            video_data = json.loads(line)
            
            track = video_data.get('track', '')
            artist = video_data.get('artist', '') or (video_data.get('artists', [])[0] if video_data.get('artists') else '')
            
            video_url = video_data.get('webpage_url') or video_data.get('url', '')
            
            # Try to get music ID from video (this is the accurate way)
            # We'll do this in batches to avoid being too slow
            music_link = None
            music_id = None
            
            # We'll fetch music IDs for videos that might match our CSV songs
            # This will be done during filtering to avoid fetching for all videos
            
            video = {
                'account': account,
                'url': video_url,
                'views': video_data.get('view_count', 0),
                'likes': video_data.get('like_count', 0),
                'comments': video_data.get('comment_count', 0),
                'shares': video_data.get('repost_count', 0),
                'upload_date': video_data.get('upload_date', ''),
                'song': track or 'Unknown',
                'artist': artist or 'Unknown',
                'original_song': track or 'Unknown',
                'original_artist': artist or 'Unknown',
                'music_link': music_link,
                'music_id': music_id,
            }
            
            # Calculate engagement rate
            if video['views'] > 0:
                video['engagement_rate'] = ((video['likes'] + video['comments'] + video['shares']) / video['views']) * 100
            else:
                video['engagement_rate'] = 0
            
            # Create sound key
            normalized_song = normalize_song_title(video['song'])
            normalized_artist = normalize_artist_name(video['artist'])
            video['sound_key'] = f"{normalized_song} - {normalized_artist}"
            
            videos.append(video)
            
        except json.JSONDecodeError:
            continue
    
    return videos

def parse_video_data(text, account):
    """Parse video data from analyzer output (text format)"""
    videos = []
    video_blocks = re.split(r'VIDEO #\d+', text)

    for block in video_blocks[1:]:
        video = {'account': account}
        url_match = re.search(r'URL: (https://[^\s]+)', block)
        if url_match:
            video['url'] = url_match.group(1)
        else:
            continue

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

        song_match = re.search(r'Song: (.+)', block)
        artist_match = re.search(r'Artist: (.+)', block)

        # Store original values
        original_song = song_match.group(1).strip() if song_match else 'Unknown'
        original_artist = artist_match.group(1).strip() if artist_match else 'Unknown'
        
        # Normalize for grouping (but keep original for display)
        normalized_song = normalize_song_title(original_song)
        normalized_artist = normalize_artist_name(original_artist)
        
        video['song'] = normalized_song
        video['artist'] = normalized_artist
        video['original_song'] = original_song  # Keep original for display
        video['original_artist'] = original_artist  # Keep original for display
        video['sound_key'] = f"{normalized_song} - {normalized_artist}"
        video['music_link'] = None  # Will be populated if we can get it
        video['music_id'] = None

        videos.append(video)

    return videos

def load_music_links_from_csv():
    """Load music links and IDs from CSV file"""
    music_links = {}  # music_id -> {link, song, artist}
    
    csv_path = config.SONG_TRACKER_CSV
    if not csv_path.exists():
        return None
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 9:
                    artist = parts[0].strip()
                    song = parts[7].strip()
                    song_link = parts[8].strip()
                    
                    if artist and song and song_link and 'tiktok.com/music/' in song_link:
                        # Extract music ID from link - it's the number at the end
                        match = re.search(r'-(\d+)(?:\?|$|&)', song_link)
                        if not match:
                            match = re.search(r'-(\d+)$', song_link.split('?')[0])
                        
                        if match:
                            music_id = match.group(1)
                            # Normalize the link (remove query params)
                            clean_link = song_link.split('?')[0]
                            music_links[music_id] = {
                                'link': clean_link,
                                'song': song,
                                'artist': artist
                            }
    except Exception as e:
        print(f"  ⚠️  Could not load music links from CSV: {e}")
        return None
    
    return music_links if music_links else None

def get_music_id_from_video_url(video_url):
    """Fetch full video details to get the actual music ID"""
    try:
        cmd = [config.YT_DLP_CMD, '--dump-json', '--no-playlist', '--quiet', video_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            full_json_str = json.dumps(data)
            
            # Search for music URL in JSON
            music_urls = re.findall(r'https://www\.tiktok\.com/music/[^\"]+', full_json_str)
            if music_urls:
                music_link = music_urls[0].split('?')[0]
                music_id = extract_music_id_from_link(music_link)
                if music_id:
                    return music_id, music_link
            
            # Try to find music_id directly
            music_id_match = re.search(r'\"music[_\-]?id\"\s*:\s*\"?(\d+)\"?', full_json_str, re.IGNORECASE)
            if music_id_match:
                music_id = music_id_match.group(1)
                track = data.get('track', '')
                if track:
                    track_slug = re.sub(r'[^\w\s-]', '', track).strip().replace(' ', '-')
                    music_link = f"https://www.tiktok.com/music/{track_slug}-{music_id}"
                else:
                    music_link = f"https://www.tiktok.com/music/original-sound-{music_id}"
                return music_id, music_link
    except:
        pass
    
    return None, None

def construct_possible_music_links(track_name, artist_name, music_links_dict):
    """Match by song name and artist to find the music ID from CSV"""
    if not track_name or track_name == 'Unknown':
        return []
    
    # Normalize for matching
    track_normalized = normalize_song_title(track_name).lower()
    artist_normalized = normalize_artist_name(artist_name).lower()
    
    possible_matches = []
    for music_id, info in music_links_dict.items():
        csv_song = normalize_song_title(info['song']).lower()
        csv_artist = normalize_artist_name(info['artist']).lower()
        
        # Check if song and artist match
        if track_normalized == csv_song and artist_normalized == csv_artist:
            possible_matches.append((music_id, info['link']))
        # Also try matching just the base song name (without version info)
        elif track_normalized.startswith(csv_song) or csv_song.startswith(track_normalized):
            if artist_normalized == csv_artist:
                possible_matches.append((music_id, info['link']))
    
    return possible_matches

def should_filter_song(video, music_links=None):
    """Check if a song should be filtered out based on music link matching"""
    artist = video.get('original_artist', video.get('artist', ''))
    song = video.get('original_song', video.get('song', ''))
    sound_key = video.get('sound_key', f"{song} - {artist}")
    
    # Check filtered artists
    if artist in config.FILTERED_ARTISTS:
        return True
    
    # Check filtered songs (by exact match or sound_key)
    if sound_key in config.FILTERED_SONGS:
        return True
    if song in config.FILTERED_SONGS:
        return True
    
    # Check music links whitelist if enabled
    if music_links is not None:
        music_id = video.get('music_id')
        music_link = video.get('music_link')
        
        # If we have music_id, check if it's in our whitelist
        if music_id and music_id in music_links:
            return False
        
        # If we have music_link, try to match it
        if music_link:
            clean_link = music_link.split('?')[0]
            for mid, info in music_links.items():
                if info['link'] == clean_link:
                    return False
        
        # Try to match by song name and artist (fallback when we don't have music_id yet)
        possible_matches = construct_possible_music_links(song, artist, music_links)
        if possible_matches:
            # Found a possible match - include it
            # Store the matched music_id for later use
            matched_id, matched_link = possible_matches[0]
            video['music_id'] = matched_id
            video['music_link'] = matched_link
            return False
        
        # No match found - exclude it
        return True
    
    return False

def aggregate_by_sound(all_videos):
    """Aggregate videos by sound/song"""
    # Load music links from CSV
    music_links = load_music_links_from_csv()
    if music_links:
        print(f"  📋 Using music link whitelist: {len(music_links)} songs from CSV")
    
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

    # First pass: Try to get music IDs for videos that might match
    print(f"  🔍 Extracting music IDs from videos (this may take a moment)...")
    videos_to_check = []
    for video in all_videos:
        # Quick check: if song/artist might match CSV, fetch music ID
        song = video.get('original_song', video.get('song', ''))
        artist = video.get('original_artist', video.get('artist', ''))
        
        # Check if this might match any CSV song
        might_match = False
        if music_links:
            for mid, info in music_links.items():
                csv_song = normalize_song_title(info['song']).lower()
                csv_artist = normalize_artist_name(info['artist']).lower()
                song_norm = normalize_song_title(song).lower()
                artist_norm = normalize_artist_name(artist).lower()
                
                if (song_norm == csv_song or song_norm.startswith(csv_song) or csv_song.startswith(song_norm)):
                    if artist_norm == csv_artist:
                        might_match = True
                        break
        
        if might_match and not video.get('music_id'):
            videos_to_check.append(video)
    
    # Fetch music IDs for potential matches (limit to avoid being too slow)
    print(f"  📥 Fetching music IDs for {min(len(videos_to_check), 200)} potential matches...")
    for i, video in enumerate(videos_to_check[:200]):  # Limit to 200 to avoid timeout
        if i % 50 == 0 and i > 0:
            print(f"    Progress: {i}/{min(len(videos_to_check), 200)} videos checked...")
        music_id, music_link = get_music_id_from_video_url(video['url'])
        if music_id:
            video['music_id'] = music_id
            video['music_link'] = music_link
    
    # Second pass: Filter videos based on music links
    for video in all_videos:
        # Skip filtered songs
        if should_filter_song(video, music_links):
            continue
            
        sound_key = video['sound_key']
        sound_stats[sound_key]['total_uses'] += 1
        sound_stats[sound_key]['total_views'] += video['views']
        sound_stats[sound_key]['total_likes'] += video['likes']
        sound_stats[sound_key]['total_comments'] += video['comments']
        sound_stats[sound_key]['total_shares'] += video['shares']
        sound_stats[sound_key]['total_engagement'] += video['engagement_rate']
        sound_stats[sound_key]['videos'].append(video)
        sound_stats[sound_key]['accounts'].add(video['account'])
        # Use normalized values for grouping, but prefer original for display if available
        sound_stats[sound_key]['song'] = video.get('original_song', video['song'])
        sound_stats[sound_key]['artist'] = video.get('original_artist', video['artist'])

    for sound_key, stats in sound_stats.items():
        uses = stats['total_uses']
        stats['avg_views'] = stats['total_views'] // uses if uses > 0 else 0
        stats['avg_likes'] = stats['total_likes'] // uses if uses > 0 else 0
        stats['avg_comments'] = stats['total_comments'] // uses if uses > 0 else 0
        stats['avg_shares'] = stats['total_shares'] // uses if uses > 0 else 0
        stats['avg_engagement_rate'] = stats['total_engagement'] / uses if uses > 0 else 0
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)  # Sort by views, not engagement
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
    
    # Get all filtered videos from sound_stats
    for stats in sound_stats.values():
        for video in stats['videos']:
            account = video['account']
            sound_key = f"{video.get('original_song', video.get('song', ''))} - {video.get('original_artist', video.get('artist', ''))}"
            
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

def generate_html(sound_stats, all_videos):
    """Generate modern, clean HTML report with earth tones and tabs"""
    sorted_sounds = sorted(sound_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)  # Sort by total views
    
    # Calculate totals from the actual filtered videos in sound_stats (not all_videos)
    # This ensures we only count videos that match the CSV whitelist
    filtered_videos = []
    for stats in sound_stats.values():
        filtered_videos.extend(stats['videos'])
    
    total_views = sum(v['views'] for v in filtered_videos)
    total_likes = sum(v['likes'] for v in filtered_videos)
    total_comments = sum(v['comments'] for v in filtered_videos)
    total_shares = sum(v['shares'] for v in filtered_videos)
    total_video_count = len(filtered_videos)
    
    # Aggregate by account for the account tab
    account_stats = aggregate_by_account(all_videos, sound_stats)
    sorted_accounts = sorted(account_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)

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

        .album-art-container {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .album-art {{
            width: 80px;
            height: 80px;
            object-fit: cover;
            border: 1px solid var(--gray-200);
            background: var(--gray-100);
            flex-shrink: 0;
        }}

        .sound-info {{
            flex: 1;
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
            flex-shrink: 0;
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

        /* Tab Navigation */
        .tab-navigation {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            justify-content: center;
            border-bottom: 1px solid var(--gray-200);
            padding-bottom: 1rem;
        }}

        .tab-button {{
            background: var(--white);
            border: 1px solid var(--gray-200);
            padding: 0.75rem 2rem;
            color: var(--gray-600);
            font-weight: 600;
            font-size: 0.9375rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .tab-button:hover {{
            background: var(--gray-50);
            border-color: var(--accent);
            color: var(--charcoal);
        }}

        .tab-button.active {{
            background: var(--accent);
            border-color: var(--accent);
            color: var(--white);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
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
                    <div class="stat-value">{format_number(total_video_count)}</div>
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
        engagement_class = get_engagement_class(stats['avg_engagement_rate'])
        
        # Get album art path
        album_art_path = None
        try:
            art_path = fetch_album_art.get_album_art(stats['song'], stats['artist'])
            if art_path:
                album_art_path = fetch_album_art.get_relative_image_path(art_path)
        except:
            pass
        
        # Build album art HTML
        album_art_html = ''
        if album_art_path:
            album_art_html = f'<img src="{album_art_path}" alt="{stats["song"]} - {stats["artist"]}" class="album-art">'
        
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
                        <span class="meta-value">{stats['avg_engagement_rate']:.2f}%</span>
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

        for j, video in enumerate(stats['videos'][:10], 1):
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

    # Close sounds tab and start accounts tab
    html += '''
        </div>
        <!-- End Sounds Tab -->

        <!-- Accounts Tab -->
        <div id="accounts-tab" class="tab-content">
'''
    
    # Generate account sections
    for account, stats in sorted_accounts:
        html += f'''
        <div class="sound-section">
            <div class="sound-header">
                <div class="sound-title-row">
                    <div class="sound-info">
                        <div class="sound-title">{account}</div>
                        <div class="sound-artist">Account Performance</div>
                    </div>
                </div>
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
                        <span class="meta-label">Avg Views</span>
                        <span class="meta-value">{format_number(stats['avg_views'])}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Avg Engagement</span>
                        <span class="meta-value">{stats['avg_engagement_rate']:.2f}%</span>
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
            </div>
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
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        # Show all videos for this account
        for j, video in enumerate(stats['videos'], 1):
            engagement_class_video = get_engagement_class(video['engagement_rate'])
            song_title = video.get('original_song', video.get('song', 'Unknown'))
            song_artist = video.get('original_artist', video.get('artist', 'Unknown'))
            
            html += f'''                    <tr>
                        <td class="video-rank">#{j}</td>
                        <td class="account-name">{song_title}</td>
                        <td class="account-name">{song_artist}</td>
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
    
    html += '''
        </div>
        <!-- End Accounts Tab -->
'''
    
    html += f'''
        <div class="footer">
            <p>{total_video_count} videos analyzed across {len(ACCOUNTS)} accounts</p>
            <p style="margin-top: 0.5rem; color: var(--gray-500);">Data sourced via yt-dlp</p>
        </div>
    </div>

    <script>
        function switchTab(tabName) {{
            // Hide all tab content
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {{
                content.classList.remove('active');
            }});

            // Remove active class from all buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {{
                button.classList.remove('active');
            }});

            // Show selected tab content
            const selectedTab = document.getElementById(tabName + '-tab');
            if (selectedTab) {{
                selectedTab.classList.add('active');
            }}

            // Add active class to clicked button
            event.target.classList.add('active');
        }}
    </script>
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
        
        # Get video data directly from yt-dlp JSON for better music link extraction
        profile_url = f"https://www.tiktok.com/{account}"
        cmd = [
            config.YT_DLP_CMD,
            '--flat-playlist',
            '--dump-json',
            '--playlist-end', str(config.DEFAULT_VIDEO_LIMIT * 3),
            profile_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=base_dir, timeout=300)
        
        if result.returncode == 0:
            videos = parse_video_data_from_json(result.stdout, account)
            all_videos.extend(videos)
            print(f"  Found {len(videos)} videos")
        else:
            print(f"  ⚠️  Error scraping {account}: {result.stderr[:200]}")

    print(f"\nTotal videos scraped: {len(all_videos)}")

    sound_stats = aggregate_by_sound(all_videos)
    
    # Calculate actual totals from filtered videos for verification
    filtered_video_count = sum(len(stats['videos']) for stats in sound_stats.values())
    filtered_total_views = sum(sum(v['views'] for v in stats['videos']) for stats in sound_stats.values())
    
    print(f"\n📊 DATA VERIFICATION - All numbers are from actual video data:")
    print(f"  Total videos scraped: {len(all_videos)}")
    print(f"  Videos matching CSV songs: {filtered_video_count}")
    print(f"  Total views (from filtered videos only): {filtered_total_views:,}")
    print(f"  Unique songs found: {len(sound_stats)}")
    if filtered_video_count > 0:
        print(f"  Average views per video: {filtered_total_views // filtered_video_count:,}")
    
    # Fetch album art for all unique songs
    print("\n🎨 Fetching album art...")
    songs_list = [{'song': stats['song'], 'artist': stats['artist']} for stats in sound_stats.values()]
    fetch_album_art.batch_fetch_album_art(songs_list)
    
    html_content = generate_html(sound_stats, all_videos)

    output_file = config.HTML_OUTPUT_FILE
    with open(str(output_file), 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ Modern report generated: {output_file}")
    print(f"   Sounds: {len(sound_stats)} | Videos (filtered): {filtered_video_count} | Accounts: {len(ACCOUNTS)}")

if __name__ == '__main__':
    main()
