"""
Scraper service for integrating tiktok_analyzer.py with database
"""

import subprocess
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import PROJECT_ROOT
from services.database import (
    ensure_account_exists,
    insert_or_update_video,
    create_scrape_log,
    update_account_last_scraped
)
from fetch_album_art import get_album_art, get_relative_image_path


def parse_analyzer_output(output: str, username: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict]:
    """Parse tiktok_analyzer.py output into structured data."""
    videos = []

    # Parse dates
    start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    # Split by video sections
    video_sections = re.split(r'VIDEO #\d+', output)

    for section in video_sections[1:]:  # Skip first empty section
        video = {}

        # Extract URL
        url_match = re.search(r'URL: (https://www\.tiktok\.com/@[^/]+/video/\d+)', section)
        if url_match:
            video['url'] = url_match.group(1)
            video_id_match = re.search(r'/video/(\d+)', video['url'])
            if video_id_match:
                video['video_id'] = video_id_match.group(1)

        # Extract upload date
        date_match = re.search(r'Upload Date: (\d{4}-\d{2}-\d{2})', section)
        if date_match:
            video['upload_date'] = date_match.group(1)
            upload_dt = datetime.strptime(video['upload_date'], '%Y-%m-%d')

            # Filter by date range
            if start_dt and upload_dt < start_dt:
                continue
            if end_dt and upload_dt > end_dt:
                continue

        # Extract caption
        caption_match = re.search(r'Title/Caption: (.+?)(?:\n|URL:)', section, re.DOTALL)
        if caption_match:
            video['caption'] = caption_match.group(1).strip()

        # Extract metrics
        views_match = re.search(r'Views:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        likes_match = re.search(r'Likes:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        comments_match = re.search(r'Comments:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)
        shares_match = re.search(r'Shares:\s+[\d.KMB]+\s+\(([,\d]+)\)', section)

        if views_match:
            video['views'] = int(views_match.group(1).replace(',', ''))
        if likes_match:
            video['likes'] = int(likes_match.group(1).replace(',', ''))
        if comments_match:
            video['comments'] = int(comments_match.group(1).replace(',', ''))
        if shares_match:
            video['shares'] = int(shares_match.group(1).replace(',', ''))

        # Calculate engagement rate
        if 'views' in video and video['views'] > 0:
            total_engagement = (
                video.get('likes', 0) +
                video.get('comments', 0) +
                video.get('shares', 0)
            )
            video['engagement_rate'] = round((total_engagement / video['views']) * 100, 2)

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


def scrape_account(username: str, session_id: str, settings: Dict) -> Tuple[str, Dict]:
    """
    Scrape a single TikTok account and save to database.
    
    Returns:
        Tuple of (status, result_dict)
        status: 'success', 'failed', 'timeout'
        result_dict: Contains videos_found, new_videos, updated_videos, error_message
    """
    start_time = time.time()
    account_id = ensure_account_exists(username)
    
    result = {
        'videos_found': 0,
        'new_videos': 0,
        'updated_videos': 0,
        'error_message': None
    }
    
    try:
        # Build command
        cmd = [
            'python3',
            str(PROJECT_ROOT / 'tiktok_analyzer.py'),
            '--url', username,
            '--limit', str(settings.get('scrape_limit', 1000))
        ]
        
        # Run scraper with timeout
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per account
        )
        
        if process.returncode != 0:
            error_msg = process.stderr or "Unknown error"
            result['error_message'] = error_msg
            status = 'failed'
        else:
            # Parse output
            videos = parse_analyzer_output(
                process.stdout,
                username,
                settings.get('start_date'),
                settings.get('end_date')
            )
            
            # Filter by sound links if specified
            tracked_sound_links = settings.get('sound_links', [])
            if tracked_sound_links:
                filtered_videos = []
                for video in videos:
                    video_sound_link = video.get('sound_link', '')
                    is_tracked = any(
                        tracked_link in video_sound_link or video_sound_link in tracked_link
                        for tracked_link in tracked_sound_links
                    )
                    if is_tracked:
                        filtered_videos.append(video)
                videos = filtered_videos
            
            # Fetch album art for unique songs
            unique_songs = {}
            for video in videos:
                song_key = (video.get('song_title', ''), video.get('artist_name', ''))
                if song_key not in unique_songs and song_key[0] and song_key[1]:
                    unique_songs[song_key] = True
            
            # Fetch album art for each unique song
            for (song_title, artist_name) in unique_songs.keys():
                album_art_path = get_album_art(song_title, artist_name)
                if album_art_path:
                    unique_songs[(song_title, artist_name)] = str(get_relative_image_path(album_art_path))
            
            # Add album art paths to videos
            for video in videos:
                song_key = (video.get('song_title', ''), video.get('artist_name', ''))
                if song_key in unique_songs and unique_songs[song_key] != True:
                    video['album_art_path'] = unique_songs[song_key]
            
            # Save videos to database
            for video in videos:
                is_new, success = insert_or_update_video(video, account_id, session_id)
                if success:
                    result['videos_found'] += 1
                    if is_new:
                        result['new_videos'] += 1
                    else:
                        result['updated_videos'] += 1
            
            # Update account last scraped
            update_account_last_scraped(account_id)
            
            status = 'success'
    
    except subprocess.TimeoutExpired:
        error_msg = 'Scraping timed out after 10 minutes'
        result['error_message'] = error_msg
        status = 'failed'
    
    except Exception as e:
        error_msg = str(e)
        result['error_message'] = error_msg
        status = 'failed'
    
    # Log to database
    execution_time = time.time() - start_time
    create_scrape_log(
        session_id=session_id,
        account_id=account_id,
        status=status,
        videos_found=result['videos_found'],
        new_videos=result['new_videos'],
        updated_videos=result['updated_videos'],
        error_message=result['error_message'],
        execution_time=execution_time
    )
    
    return status, result

