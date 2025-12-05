#!/usr/bin/env python3
"""
Generate CSV files for each song with usage instances and links
Creates a separate CSV file for each song containing all video instances where it was used
"""

import subprocess
import re
from collections import defaultdict
import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found. Please create config.py with your account configuration.")
    sys.exit(1)

# Import CSV generator utility
from utils.csv_generator import generate_csv_files_from_videos, sanitize_filename

# Use accounts from config
ACCOUNTS = config.ACCOUNTS

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

def extract_music_id_from_link(music_link):
    """Extract music ID from a TikTok music link"""
    if not music_link:
        return None
    match = re.search(r'-(\d+)(?:\?|$|&)', music_link)
    if not match:
        match = re.search(r'-(\d+)$', music_link.split('?')[0])
    return match.group(1) if match else None

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
                        # Extract music ID from link
                        match = re.search(r'-(\d+)(?:\?|$|&)', song_link)
                        if not match:
                            match = re.search(r'-(\d+)$', song_link.split('?')[0])
                        
                        if match:
                            music_id = match.group(1)
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

def construct_possible_music_links(track_name, artist_name, music_links_dict):
    """Match by song name and artist to find the music ID from CSV"""
    if not track_name or track_name == 'Unknown':
        return []
    
    track_normalized = normalize_song_title(track_name).lower()
    artist_normalized = normalize_artist_name(artist_name).lower()
    
    possible_matches = []
    for music_id, info in music_links_dict.items():
        csv_song = normalize_song_title(info['song']).lower()
        csv_artist = normalize_artist_name(info['artist']).lower()
        
        if track_normalized == csv_song and artist_normalized == csv_artist:
            possible_matches.append((music_id, info['link']))
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
    
    # Check filtered songs
    if sound_key in config.FILTERED_SONGS:
        return True
    if song in config.FILTERED_SONGS:
        return True
    
    # Check music links whitelist if enabled
    if music_links is not None:
        music_id = video.get('music_id')
        music_link = video.get('music_link')
        
        if music_id and music_id in music_links:
            return False
        
        if music_link:
            clean_link = music_link.split('?')[0]
            for mid, info in music_links.items():
                if info['link'] == clean_link:
                    return False
        
        # Try to match by song name and artist
        possible_matches = construct_possible_music_links(song, artist, music_links)
        if possible_matches:
            matched_id, matched_link = possible_matches[0]
            video['music_id'] = matched_id
            video['music_link'] = matched_link
            return False
        
        return True
    
    return False

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
                'music_link': None,
                'music_id': None,
            }
            
            # Calculate engagement rate
            if video['views'] > 0:
                video['engagement_rate'] = ((video['likes'] + video['comments'] + video['shares']) / video['views']) * 100
            else:
                video['engagement_rate'] = 0
            
            # Format upload date
            upload_date = video['upload_date']
            if upload_date:
                try:
                    upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                    video['upload_date'] = upload_datetime.strftime('%Y-%m-%d')
                except:
                    video['upload_date'] = upload_date
            else:
                video['upload_date'] = 'Unknown'
            
            # Create sound key
            normalized_song = normalize_song_title(video['song'])
            normalized_artist = normalize_artist_name(video['artist'])
            video['sound_key'] = f"{normalized_song} - {normalized_artist}"
            
            videos.append(video)
            
        except json.JSONDecodeError:
            continue
    
    return videos

def aggregate_by_sound(all_videos):
    """Aggregate videos by sound/song"""
    # Load music links from CSV
    music_links = load_music_links_from_csv()
    if music_links:
        print(f"  📋 Using music link whitelist: {len(music_links)} songs from CSV")
    
    sound_stats = defaultdict(lambda: {
        'videos': [],
        'song': '',
        'artist': ''
    })

    # First pass: Try to get music IDs for videos that might match
    print(f"  🔍 Extracting music IDs from videos (this may take a moment)...")
    videos_to_check = []
    for video in all_videos:
        song = video.get('original_song', video.get('song', ''))
        artist = video.get('original_artist', video.get('artist', ''))
        
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
    
    # Fetch music IDs for potential matches
    print(f"  📥 Fetching music IDs for {min(len(videos_to_check), 200)} potential matches...")
    for i, video in enumerate(videos_to_check[:200]):
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
        sound_stats[sound_key]['videos'].append(video)
        sound_stats[sound_key]['song'] = video.get('original_song', video['song'])
        sound_stats[sound_key]['artist'] = video.get('original_artist', video['artist'])

    # Sort videos within each song by views (highest first)
    for sound_key, stats in sound_stats.items():
        stats['videos'].sort(key=lambda x: x['views'], reverse=True)

    return sound_stats

# Note: sanitize_filename and generate_csv_files are now imported from utils.csv_generator
# This function is kept for backward compatibility but uses the utility module
def generate_csv_files(sound_stats, output_dir):
    """Generate CSV file for each song - uses utility module"""
    # Convert sound_stats format to list of videos
    all_videos = []
    for sound_key, stats in sound_stats.items():
        for video in stats['videos']:
            # Ensure video has song_title and artist_name for compatibility
            if 'song_title' not in video:
                video['song_title'] = video.get('song', '')
            if 'artist_name' not in video:
                video['artist_name'] = video.get('artist', '')
            all_videos.append(video)
    
    # Use utility function
    csv_files_created, total_rows, file_list = generate_csv_files_from_videos(all_videos, output_dir)
    
    # Print individual file creation messages
    for file_info in file_list:
        print(f"  ✓ Created: {file_info['filename']} ({file_info['video_count']} videos)")
    
    return csv_files_created, total_rows

def main():
    if not ACCOUNTS:
        print("ERROR: No accounts configured. Please add accounts to config.ACCOUNTS")
        return

    print(f"\n{'='*80}")
    print("GENERATING CSV FILES - SONG USAGE INSTANCES")
    print("="*80)
    print(f"\nCollecting video data from {len(ACCOUNTS)} accounts...")

    all_videos = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = script_dir

    for account in ACCOUNTS:
        print(f"Processing {account}...")
        
        # Get video data directly from yt-dlp JSON
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
    
    # Calculate totals from filtered videos
    filtered_video_count = sum(len(stats['videos']) for stats in sound_stats.values())
    
    print(f"\n📊 DATA SUMMARY:")
    print(f"  Total videos scraped: {len(all_videos)}")
    print(f"  Videos matching CSV songs: {filtered_video_count}")
    print(f"  Unique songs found: {len(sound_stats)}")
    
    # Generate CSV files
    output_dir = config.OUTPUT_DIR / 'song_csvs'
    print(f"\n📁 Generating CSV files in: {output_dir}")
    print(f"   Creating CSV file for each song...")
    
    csv_files_created, total_rows = generate_csv_files(sound_stats, output_dir)
    
    print(f"\n{'='*80}")
    print(f"✅ CSV GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"  CSV files created: {csv_files_created}")
    print(f"  Total video rows: {total_rows}")
    print(f"  Output directory: {output_dir}")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()

