#!/usr/bin/env python3
"""
CSV Generator Utility Module
Reusable functions for generating CSV files from video data
"""

import csv
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime


def sanitize_filename(filename):
    """Sanitize filename for filesystem"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def group_videos_by_song(videos):
    """
    Group videos by song/sound key.
    
    Args:
        videos: List of video dictionaries with 'sound_key', 'song_title', 'artist_name' keys
    
    Returns:
        Dictionary mapping sound_key to list of videos and metadata
    """
    sound_stats = defaultdict(lambda: {
        'videos': [],
        'song': '',
        'artist': ''
    })
    
    for video in videos:
        # Get song information from video
        sound_key = video.get('sound_key', 'Unknown Sound')
        song_title = video.get('song_title') or video.get('song', '')
        artist_name = video.get('artist_name') or video.get('artist', '')
        
        # Use original values if available, otherwise use normalized
        sound_stats[sound_key]['videos'].append(video)
        sound_stats[sound_key]['song'] = song_title or 'Unknown'
        sound_stats[sound_key]['artist'] = artist_name or 'Unknown'
    
    # Sort videos within each song by views (highest first)
    for sound_key, stats in sound_stats.items():
        stats['videos'].sort(key=lambda x: x.get('views', 0), reverse=True)
    
    return sound_stats


def generate_csv_files_from_videos(videos, output_dir):
    """
    Generate CSV file for each song from video data.
    
    Args:
        videos: List of video dictionaries with song and engagement data
        output_dir: Path to output directory for CSV files
    
    Returns:
        Tuple of (csv_files_created, total_rows, file_list)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group videos by song
    sound_stats = group_videos_by_song(videos)
    
    csv_files_created = 0
    total_rows = 0
    file_list = []
    
    for sound_key, stats in sorted(sound_stats.items()):
        if not stats['videos']:
            continue
        
        # Create filename from song and artist
        song_name = stats['song'] or 'Unknown'
        artist_name = stats['artist'] or 'Unknown'
        filename = f"{song_name} - {artist_name}.csv"
        filename = sanitize_filename(filename)
        filepath = output_dir / filename
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Account',
                'Video URL',
                'Upload Date',
                'Views',
                'Likes',
                'Comments',
                'Shares',
                'Engagement Rate (%)',
                'Song Title',
                'Artist Name'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for video in stats['videos']:
                # Extract song and artist from video data
                song_title = video.get('song_title') or video.get('song', 'Unknown')
                artist_name = video.get('artist_name') or video.get('artist', 'Unknown')
                
                # Get engagement rate
                engagement_rate = video.get('engagement_rate', 0)
                if engagement_rate == 0 and video.get('views', 0) > 0:
                    engagement_rate = (
                        (video.get('likes', 0) + video.get('comments', 0) + video.get('shares', 0)) /
                        video.get('views', 1)
                    ) * 100
                
                # Format upload date
                upload_date = video.get('upload_date', 'Unknown')
                if upload_date and upload_date != 'Unknown':
                    try:
                        # Try to parse different date formats
                        if len(upload_date) == 8 and upload_date.isdigit():
                            # Format: YYYYMMDD
                            upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                            upload_date = upload_datetime.strftime('%Y-%m-%d')
                        elif '-' in upload_date:
                            # Already in YYYY-MM-DD format
                            pass
                    except:
                        pass
                
                writer.writerow({
                    'Account': video.get('account', 'Unknown'),
                    'Video URL': video.get('url', ''),
                    'Upload Date': upload_date,
                    'Views': video.get('views', 0),
                    'Likes': video.get('likes', 0),
                    'Comments': video.get('comments', 0),
                    'Shares': video.get('shares', 0),
                    'Engagement Rate (%)': f"{engagement_rate:.2f}",
                    'Song Title': song_title,
                    'Artist Name': artist_name
                })
                total_rows += 1
        
        csv_files_created += 1
        file_list.append({
            'filename': filename,
            'song': song_name,
            'artist': artist_name,
            'video_count': len(stats['videos'])
        })
    
    return csv_files_created, total_rows, file_list

