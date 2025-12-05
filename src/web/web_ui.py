#!/usr/bin/env python3
"""
Warner Sound Tracker - Interactive Web UI

A Flask-based web interface for managing the Warner Sound tracking workflow:
1. Settings: Configure date ranges and scraping parameters
2. Scrape: Run scraping jobs with status monitoring
3. Edit: Manually review and filter songs
4. Report: Generate analytics and live reports

Usage:
    python3 web_ui.py
    Then open http://localhost:5000 in your browser
"""

import csv
import json
import subprocess
import threading
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from config import ACCOUNTS, PROJECT_ROOT, OUTPUT_DIR, DATA_DIR
import zipfile
import io

# Import album art fetcher
from fetch_album_art import get_album_art, get_relative_image_path

# Import sound ID extraction
from extract_sound_id import extract_sound_id_from_music_link

# Import CSV generator
from utils.csv_generator import generate_csv_files_from_videos

# Import database functions
from services.database import (
    ensure_account_exists,
    insert_or_update_video,
    create_scrape_session,
    update_scrape_session,
    create_scrape_log,
    get_session,
    get_videos_by_session,
    get_sounds_by_session,
    get_all_sessions,
    get_accounts,
    update_account_last_scraped
)
import time

app = Flask(__name__)

# Load configuration from environment variables
import os
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'warner-tracker-secret-key')

# Enable CORS for all routes (for frontend access)
# Allow all origins in development, restrict in production
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={r"/api/*": {"origins": cors_origins}})

# Global state for scraping sessions
scrape_sessions = {}
current_session_id = None

# Paths
WARNER_CSV = DATA_DIR / 'warner_songs_clean.csv'
SCRAPED_DATA_FILE = OUTPUT_DIR / 'scraped_data.json'
FILTERED_DATA_FILE = OUTPUT_DIR / 'filtered_data.json'
SETTINGS_FILE = OUTPUT_DIR / 'settings.json'
SONG_CSVS_DIR = OUTPUT_DIR / 'song_csvs'
MUSIC_LINKS_WHITELIST_FILE = OUTPUT_DIR / 'music_links_whitelist.json'
ACCOUNTS_WHITELIST_FILE = OUTPUT_DIR / 'accounts_whitelist.json'
CSV_REPORT_FILE = PROJECT_ROOT / 'warner_song_usage_report_COMPLETE.csv'


# ============================================================================
# SETTINGS MANAGEMENT
# ============================================================================

def load_settings():
    """Load settings from file or return defaults."""
    default_settings = {
        'start_date': '2025-10-14',
        'end_date': datetime.now().strftime('%Y-%m-%d'),
        'scrape_limit': 1000,
        'accounts': ACCOUNTS,
        'sound_links': []
    }

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings

    return default_settings


def save_settings(settings):
    """Save settings to file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


# ============================================================================
# SCRAPING LOGIC
# ============================================================================

def load_warner_songs():
    """Load Warner song list from CSV."""
    warner_songs = []
    try:
        with open(WARNER_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                warner_songs.append({
                    'sound_key': row.get('sound_key', '').strip(),
                    'song': row.get('song', '').strip(),
                    'artist': row.get('artist', '').strip(),
                    'song_link': row.get('song_link', '').strip()
                })
    except Exception as e:
        print(f"Error loading Warner songs: {e}")

    return warner_songs


def scrape_account_background(session_id, username, settings):
    """
    Scrape a single account in the background.
    Updates the global scrape_sessions dict with status and saves to database.
    """
    session = scrape_sessions[session_id]
    account_data = {
        'username': username,
        'status': 'scraping',
        'start_time': datetime.now().isoformat(),
        'videos': [],
        'error': None,
        'timeout': False
    }

    session['accounts'][username] = account_data
    
    # Ensure account exists in database
    account_id = ensure_account_exists(username)
    start_time = time.time()

    try:
        # Build command
        cmd = [
            'python3',
            str(PROJECT_ROOT / 'tiktok_analyzer.py'),
            '--url', username,
            '--limit', str(settings.get('scrape_limit', 1000))
        ]

        # Run scraper with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per account
        )

        if result.returncode != 0:
            account_data['status'] = 'error'
            account_data['error'] = result.stderr
            # Log error to database
            execution_time = time.time() - start_time
            create_scrape_log(
                session_id=session_id,
                account_id=account_id,
                status='failed',
                error_message=result.stderr,
                execution_time=execution_time
            )
        else:
            # Parse output
            videos = parse_analyzer_output(
                result.stdout,
                username,
                settings.get('start_date'),
                settings.get('end_date')
            )

            # Filter by sound IDs if specified
            tracked_sound_links = settings.get('sound_links', [])
            if tracked_sound_links:
                # Load the sound IDs mapping from whitelist file
                tracked_sound_ids = set()
                try:
                    if MUSIC_LINKS_WHITELIST_FILE.exists():
                        with open(MUSIC_LINKS_WHITELIST_FILE, 'r') as f:
                            whitelist_data = json.load(f)
                            sound_ids_map = whitelist_data.get('sound_ids_map', {})
                            tracked_sound_ids = set(sound_ids_map.keys())
                            print(f"🔍 Filtering against {len(tracked_sound_ids)} tracked sound IDs...")
                except Exception as e:
                    print(f"⚠️  Error loading sound IDs whitelist: {e}")
                    # Fallback: just skip filtering
                    tracked_sound_ids = set()

                if tracked_sound_ids:
                    filtered_videos = []
                    for video in videos:
                        video_music_id = video.get('music_id')
                        if video_music_id and video_music_id in tracked_sound_ids:
                            filtered_videos.append(video)
                            print(f"  ✅ Matched: {video.get('song_title')} (ID: {video_music_id})")
                        else:
                            print(f"  ❌ Skipped: {video.get('song_title')} (ID: {video_music_id})")

                    print(f"🎯 Kept {len(filtered_videos)}/{len(videos)} videos matching tracked sounds")
                    videos = filtered_videos
                else:
                    print("⚠️  No sound IDs available for filtering - keeping all videos")

            # Fetch album art for unique songs
            print(f"  🎨 Fetching album art for {username}...")
            unique_songs = {}
            for video in videos:
                song_key = (video.get('song_title', ''), video.get('artist_name', ''))
                if song_key not in unique_songs and song_key[0] and song_key[1]:
                    unique_songs[song_key] = True

            # Fetch album art for each unique song
            for (song_title, artist_name) in unique_songs.keys():
                album_art_path = get_album_art(song_title, artist_name)
                # Store in cache for quick lookup
                if album_art_path:
                    unique_songs[(song_title, artist_name)] = str(get_relative_image_path(album_art_path))

            # Add album art paths to videos
            for video in videos:
                song_key = (video.get('song_title', ''), video.get('artist_name', ''))
                if song_key in unique_songs and unique_songs[song_key] != True:
                    video['album_art_path'] = unique_songs[song_key]

            # Save videos to database
            new_videos = 0
            updated_videos = 0
            for video in videos:
                is_new, success = insert_or_update_video(video, account_id, session_id)
                if success:
                    if is_new:
                        new_videos += 1
                    else:
                        updated_videos += 1

            # Update account last scraped
            update_account_last_scraped(account_id)

            # Log to database
            execution_time = time.time() - start_time
            create_scrape_log(
                session_id=session_id,
                account_id=account_id,
                status='success',
                videos_found=len(videos),
                new_videos=new_videos,
                updated_videos=updated_videos,
                execution_time=execution_time
            )

            account_data['videos'] = videos
            account_data['status'] = 'completed'
            account_data['video_count'] = len(videos)
            account_data['new_videos'] = new_videos
            account_data['updated_videos'] = updated_videos

    except subprocess.TimeoutExpired:
        account_data['status'] = 'timeout'
        account_data['timeout'] = True
        account_data['error'] = 'Scraping timed out after 10 minutes'
        # Log timeout to database
        execution_time = time.time() - start_time
        create_scrape_log(
            session_id=session_id,
            account_id=account_id,
            status='failed',
            error_message='Scraping timed out after 10 minutes',
            execution_time=execution_time
        )

    except Exception as e:
        account_data['status'] = 'error'
        account_data['error'] = str(e)
        # Log error to database
        execution_time = time.time() - start_time
        create_scrape_log(
            session_id=session_id,
            account_id=account_id,
            status='failed',
            error_message=str(e),
            execution_time=execution_time
        )

    finally:
        account_data['end_time'] = datetime.now().isoformat()

    # Check if all accounts are done
    all_done = all(
        acc['status'] in ['completed', 'error', 'timeout']
        for acc in session['accounts'].values()
    )

    if all_done:
        session['status'] = 'completed'
        session['end_time'] = datetime.now().isoformat()

        # Update session in database
        update_scrape_session(session_id, 'completed')


def parse_analyzer_output(output, username, start_date=None, end_date=None):
    """Parse tiktok_analyzer.py output into structured data."""
    import re

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


def load_scraped_data(session_id=None):
    """Load scraped data from database."""
    try:
        # If no session_id provided, get the most recent session
        if not session_id:
            sessions = get_all_sessions(limit=1)
            if not sessions:
                return None
            session_id = sessions[0]['session_id']
        
        # Get session from database
        session = get_session(session_id)
        if not session:
            return None
        
        # Get videos for this session
        settings = json.loads(session.get('configuration', '{}'))
        videos = get_videos_by_session(session_id, settings)
        
        # Convert to old format for compatibility
        data = {
            'session_id': session_id,
            'scrape_time': session.get('start_time'),
            'settings': settings,
            'videos': videos,
            'accounts': {}  # Will be populated from scrape_logs if needed
        }
        
        return data
    except Exception as e:
        print(f"Error loading scraped data: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_filtered_data(session_id=None, sound_keys=None):
    """Load filtered data from database."""
    try:
        # If no session_id provided, get the most recent session
        if not session_id:
            sessions = get_all_sessions(limit=1)
            if not sessions:
                return None
            session_id = sessions[0]['session_id']
        
        # Build filters
        filters = {}
        if sound_keys:
            # If sound_keys provided, we'll filter after fetching
            pass
        
        # Get videos for this session
        videos = get_videos_by_session(session_id, filters)
        
        # Filter by sound_keys if provided
        if sound_keys:
            sound_keys_set = set(sound_keys)
            videos = [v for v in videos if v.get('sound_key') in sound_keys_set]
        
        data = {
            'filter_time': datetime.now().isoformat(),
            'videos': videos,
            'session_id': session_id
        }
        
        return data
    except Exception as e:
        print(f"Error loading filtered data: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')


@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update settings."""
    if request.method == 'GET':
        settings = load_settings()
        return jsonify({'success': True, 'settings': settings})

    elif request.method == 'POST':
        settings = request.json
        success = save_settings(settings)
        return jsonify({'success': success, 'settings': settings})


@app.route('/api/upload-sounds-csv', methods=['POST'])
def api_upload_sounds_csv():
    """
    Upload CSV containing TikTok sound links.
    Extracts ONLY TikTok music links - ignores all other CSV data.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV'})

    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')

        if len(lines) < 1:
            return jsonify({'success': False, 'error': 'CSV is empty'})

        # Extract ONLY TikTok music links from the entire CSV
        sound_links = []

        for line in lines:
            # Split by common delimiters and check each cell
            cells = line.split(',')
            for cell in cells:
                cell = cell.strip().strip('"').strip("'")
                # Check if it's a TikTok music link
                if 'tiktok.com/music/' in cell:
                    # Clean up the link (remove query params)
                    clean_link = cell.split('?')[0].split('&')[0]
                    if clean_link not in sound_links:
                        sound_links.append(clean_link)

        if not sound_links:
            return jsonify({
                'success': False,
                'error': 'No TikTok music links found in CSV. Links should contain "tiktok.com/music/"'
            })

        # Extract sound IDs from music links
        print(f"📋 Extracting sound IDs from {len(sound_links)} music links...")
        sound_ids_map = {}  # Map sound_id -> music_link

        for music_link in sound_links:
            print(f"  Processing: {music_link}")
            sound_id, song_title, artist = extract_sound_id_from_music_link(music_link)

            if sound_id:
                sound_ids_map[sound_id] = {
                    'music_link': music_link,
                    'song_title': song_title,
                    'artist': artist
                }
                print(f"    ✅ Sound ID: {sound_id} - {song_title} by {artist}")
            else:
                print(f"    ⚠️  Could not extract sound ID")

        # Store both music links and sound IDs
        try:
            with open(MUSIC_LINKS_WHITELIST_FILE, 'w') as f:
                json.dump({
                    'links': sound_links,
                    'sound_ids_map': sound_ids_map,  # NEW: Map of sound IDs
                    'uploaded_at': datetime.now().isoformat(),
                    'count': len(sound_links)
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving music links whitelist: {e}")

        return jsonify({
            'success': True,
            'sound_links': sound_links,
            'sound_ids': list(sound_ids_map.keys()),  # Return list of sound IDs
            'message': f'Found {len(sound_links)} TikTok sound links ({len(sound_ids_map)} with sound IDs)',
            'count': len(sound_links)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing CSV: {str(e)}'})


@app.route('/api/upload-accounts-csv', methods=['POST'])
def api_upload_accounts_csv():
    """
    Upload CSV containing TikTok account usernames.
    Extracts ONLY TikTok handles (@username) - ignores all other CSV data.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV'})

    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')

        if len(lines) < 1:
            return jsonify({'success': False, 'error': 'CSV is empty'})

        # Extract ONLY TikTok handles from the entire CSV
        accounts = []

        for line in lines:
            # Split by common delimiters
            cells = line.split(',')
            for cell in cells:
                cell = cell.strip().strip('"').strip("'")
                
                # Check for @username pattern
                if '@' in cell:
                    # Extract handle - could be @username or tiktok.com/@username
                    if 'tiktok.com/@' in cell:
                        # Extract from URL
                        match = re.search(r'tiktok\.com/@([\w\.]+)', cell)
                        if match:
                            handle = '@' + match.group(1)
                            if handle not in accounts:
                                accounts.append(handle)
                    elif cell.startswith('@'):
                        # Already a handle
                        handle = cell.split()[0].split('?')[0].split('&')[0]  # Clean up
                        if handle not in accounts and len(handle) > 1:
                            accounts.append(handle)
                    else:
                        # Extract @username from text
                        match = re.search(r'@([\w\.]+)', cell)
                        if match:
                            handle = '@' + match.group(1)
                            if handle not in accounts:
                                accounts.append(handle)

        if not accounts:
            return jsonify({
                'success': False,
                'error': 'No TikTok usernames found in CSV. Usernames should contain "@" symbol or be in format "tiktok.com/@username".'
            })

        # Store accounts whitelist
        try:
            with open(ACCOUNTS_WHITELIST_FILE, 'w') as f:
                json.dump({
                    'accounts': accounts,
                    'uploaded_at': datetime.now().isoformat(),
                    'count': len(accounts)
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving accounts whitelist: {e}")

        return jsonify({
            'success': True,
            'accounts': accounts,
            'message': f'Found {len(accounts)} TikTok accounts',
            'count': len(accounts)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing CSV: {str(e)}'})


@app.route('/api/warner-songs')
def api_warner_songs():
    """Get list of Warner songs from CSV."""
    songs = load_warner_songs()
    return jsonify({'success': True, 'songs': songs, 'count': len(songs)})


@app.route('/api/scrape/start', methods=['POST'])
def api_scrape_start():
    """Start a new scraping session."""
    global current_session_id

    settings = load_settings()
    accounts = settings.get('accounts', ACCOUNTS)

    # Create new session
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    current_session_id = session_id

    # Create session in database
    create_scrape_session(session_id, settings, len(accounts))

    # Create in-memory session for real-time updates
    scrape_sessions[session_id] = {
        'id': session_id,
        'status': 'running',
        'start_time': datetime.now().isoformat(),
        'settings': settings,
        'accounts': {}
    }

    # Start scraping each account in background threads
    for username in accounts:
        thread = threading.Thread(
            target=scrape_account_background,
            args=(session_id, username, settings)
        )
        thread.daemon = True
        thread.start()

    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'Started scraping {len(accounts)} accounts'
    })


@app.route('/api/scrape/status')
def api_scrape_status():
    """Get status of current scraping session."""
    global current_session_id

    if not current_session_id or current_session_id not in scrape_sessions:
        return jsonify({'success': False, 'message': 'No active scraping session'})

    session = scrape_sessions[current_session_id]

    return jsonify({
        'success': True,
        'session': {
            'id': session['id'],
            'status': session['status'],
            'start_time': session['start_time'],
            'accounts': {
                username: {
                    'status': acc['status'],
                    'video_count': len(acc.get('videos', [])),
                    'error': acc.get('error'),
                    'timeout': acc.get('timeout', False)
                }
                for username, acc in session['accounts'].items()
            }
        }
    })


@app.route('/api/scraped-data')
def api_scraped_data():
    """Get scraped data for editing."""
    data = load_scraped_data()

    if not data:
        return jsonify({'success': False, 'message': 'No scraped data available'})

    # Group videos by song
    songs_map = defaultdict(list)
    for video in data.get('videos', []):
        sound_key = video.get('sound_key', 'Unknown Sound')
        songs_map[sound_key].append(video)

    # Convert to list of songs with video counts
    songs = []
    for sound_key, videos in songs_map.items():
        songs.append({
            'sound_key': sound_key,
            'video_count': len(videos),
            'videos': videos,
            'total_views': sum(v.get('views', 0) for v in videos),
            'total_likes': sum(v.get('likes', 0) for v in videos),
        })

    # Sort by video count (most used first)
    songs.sort(key=lambda x: x['video_count'], reverse=True)

    return jsonify({
        'success': True,
        'songs': songs,
        'total_songs': len(songs),
        'total_videos': len(data.get('videos', [])),
        'scrape_info': {
            'scrape_time': data.get('scrape_time'),
            'accounts': data.get('accounts', {})
        }
    })


@app.route('/api/filter-songs', methods=['POST'])
def api_filter_songs():
    """
    Apply manual filtering to scraped songs.

    Request body:
    {
        "kept_songs": ["sound_key1", "sound_key2", ...],
        "session_id": "session_xxx" (optional, uses most recent if not provided)
    }
    """
    session_id = request.json.get('session_id')
    kept_songs = request.json.get('kept_songs', [])
    
    if not kept_songs:
        return jsonify({'success': False, 'message': 'No songs specified to keep'})

    # Load data with filtering
    data = load_filtered_data(session_id=session_id, sound_keys=kept_songs)
    if not data:
        return jsonify({'success': False, 'message': 'No scraped data available'})

    filtered_videos = data.get('videos', [])
    # Get total videos count for this session
    all_videos = get_videos_by_session(data.get('session_id'), {})
    total_videos = len(all_videos)

    return jsonify({
        'success': True,
        'filtered_count': len(filtered_videos),
        'removed_count': total_videos - len(filtered_videos),
        'session_id': data.get('session_id')
    })


@app.route('/api/report/generate', methods=['POST'])
def api_report_generate():
    """Generate analytics report from filtered data."""
    session_id = request.json.get('session_id') if request.is_json else None
    sound_keys = request.json.get('sound_keys') if request.is_json else None
    
    data = load_filtered_data(session_id=session_id, sound_keys=sound_keys)

    if not data:
        return jsonify({'success': False, 'message': 'No filtered data available. Please run scrape and filter first.'})

    videos = data.get('videos', [])

    # Group by account
    accounts_data = defaultdict(lambda: {'videos': [], 'sounds': defaultdict(list)})

    for video in videos:
        account = video.get('account')
        sound_key = video.get('sound_key')

        accounts_data[account]['videos'].append(video)
        accounts_data[account]['sounds'][sound_key].append(video)

    # Generate report data
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'total_accounts': len(accounts_data),
        'accounts': []
    }

    for account, data in accounts_data.items():
        account_report = {
            'username': account,
            'total_videos': len(data['videos']),
            'total_sounds': len(data['sounds']),
            'sounds': []
        }

        # Sound stats
        for sound_key, sound_videos in data['sounds'].items():
            sound_stat = {
                'sound_key': sound_key,
                'video_count': len(sound_videos),
                'total_views': sum(v.get('views', 0) for v in sound_videos),
                'total_likes': sum(v.get('likes', 0) for v in sound_videos),
                'total_comments': sum(v.get('comments', 0) for v in sound_videos),
                'total_shares': sum(v.get('shares', 0) for v in sound_videos),
                'avg_engagement_rate': round(
                    sum(v.get('engagement_rate', 0) for v in sound_videos) / len(sound_videos),
                    2
                ),
                'videos': sound_videos
            }
            account_report['sounds'].append(sound_stat)

        # Sort sounds by video count
        account_report['sounds'].sort(key=lambda x: x['video_count'], reverse=True)

        report['accounts'].append(account_report)

    # Sort accounts by video count
    report['accounts'].sort(key=lambda x: x['total_videos'], reverse=True)

    return jsonify({'success': True, 'report': report})


@app.route('/api/report/generate-csvs', methods=['POST'])
def api_generate_csvs():
    """Generate CSV files for each song from filtered data."""
    data = load_filtered_data()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No filtered data available. Please run scrape and filter first.'
        })
    
    videos = data.get('videos', [])
    
    if not videos:
        return jsonify({
            'success': False,
            'message': 'No videos in filtered data.'
        })
    
    try:
        # Ensure output directory exists
        SONG_CSVS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate CSV files using the utility function
        csv_files_created, total_rows, file_list = generate_csv_files_from_videos(
            videos,
            SONG_CSVS_DIR
        )
        
        return jsonify({
            'success': True,
            'csv_files_created': csv_files_created,
            'total_rows': total_rows,
            'files': file_list,
            'message': f'Generated {csv_files_created} CSV files with {total_rows} total video rows'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating CSV files: {str(e)}'
        })


@app.route('/api/csvs/list', methods=['GET'])
def api_list_csvs():
    """List all generated CSV files."""
    try:
        if not SONG_CSVS_DIR.exists():
            return jsonify({
                'success': True,
                'files': [],
                'count': 0,
                'message': 'No CSV files generated yet'
            })
        
        csv_files = []
        for file_path in sorted(SONG_CSVS_DIR.glob('*.csv')):
            file_stat = file_path.stat()
            csv_files.append({
                'filename': file_path.name,
                'size': file_stat.st_size,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        return jsonify({
            'success': True,
            'files': csv_files,
            'count': len(csv_files),
            'directory': str(SONG_CSVS_DIR)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error listing CSV files: {str(e)}'
        })


@app.route('/api/csvs/download/<path:filename>', methods=['GET'])
def api_download_csv(filename):
    """Download a specific CSV file."""
    try:
        from urllib.parse import unquote
        # Decode URL-encoded filename
        filename = unquote(filename)
        
        # Security: prevent directory traversal
        if '..' in filename or filename.startswith('/') or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        # Ensure it's a CSV file
        if not filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        file_path = SONG_CSVS_DIR / filename
        
        # Additional security: ensure file is within the CSV directory
        try:
            file_path.resolve().relative_to(SONG_CSVS_DIR.resolve())
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid file path'}), 400
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error downloading file: {str(e)}'
        }), 500


@app.route('/api/csvs/download-all', methods=['GET'])
def api_download_all_csvs():
    """Download all CSV files as a zip archive."""
    try:
        if not SONG_CSVS_DIR.exists():
            return jsonify({
                'success': False,
                'error': 'No CSV files generated yet'
            }), 404
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            csv_files = list(SONG_CSVS_DIR.glob('*.csv'))
            
            if not csv_files:
                return jsonify({
                    'success': False,
                    'error': 'No CSV files found'
                }), 404
            
            for file_path in csv_files:
                zip_file.write(file_path, file_path.name)
        
        zip_buffer.seek(0)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'song_csvs_{timestamp}.zip'
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error creating zip file: {str(e)}'
        }), 500


@app.route('/api/csv-report/load', methods=['GET'])
def api_load_csv_report():
    """Load the complete CSV report data."""
    try:
        if not CSV_REPORT_FILE.exists():
            return jsonify({
                'success': False,
                'error': f'CSV report file not found: {CSV_REPORT_FILE}'
            }), 404
        
        rows = []
        with open(CSV_REPORT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                try:
                    row['Views'] = int(row.get('Views', 0) or 0)
                    row['Likes'] = int(row.get('Likes', 0) or 0)
                    row['Comments'] = int(row.get('Comments', 0) or 0)
                    row['Shares'] = int(row.get('Shares', 0) or 0)
                    row['Engagement Rate (%)'] = float(row.get('Engagement Rate (%)', 0) or 0)
                except (ValueError, TypeError):
                    pass
                rows.append(row)
        
        # Calculate summary statistics
        total_rows = len(rows)
        unique_accounts = len(set(row.get('Account', '') for row in rows))
        unique_songs = len(set(f"{row.get('Song Name', '')} - {row.get('Artist', '')}" for row in rows))
        total_views = sum(row.get('Views', 0) for row in rows)
        total_likes = sum(row.get('Likes', 0) for row in rows)
        total_comments = sum(row.get('Comments', 0) for row in rows)
        total_shares = sum(row.get('Shares', 0) for row in rows)
        avg_engagement = sum(row.get('Engagement Rate (%)', 0) for row in rows) / total_rows if total_rows > 0 else 0
        
        # Get top songs by usage
        song_usage = defaultdict(lambda: {'count': 0, 'views': 0, 'likes': 0})
        for row in rows:
            song_key = f"{row.get('Song Name', '')} - {row.get('Artist', '')}"
            song_usage[song_key]['count'] += 1
            song_usage[song_key]['views'] += row.get('Views', 0)
            song_usage[song_key]['likes'] += row.get('Likes', 0)
        
        top_songs = sorted(
            [{'song': k, **v} for k, v in song_usage.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        # Get top accounts by video count
        account_usage = defaultdict(int)
        for row in rows:
            account_usage[row.get('Account', '')] += 1
        
        top_accounts = sorted(
            [{'account': k, 'count': v} for k, v in account_usage.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        return jsonify({
            'success': True,
            'rows': rows,
            'summary': {
                'total_rows': total_rows,
                'unique_accounts': unique_accounts,
                'unique_songs': unique_songs,
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'avg_engagement': round(avg_engagement, 2)
            },
            'top_songs': top_songs,
            'top_accounts': top_accounts
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error loading CSV report: {str(e)}'
        }), 500


# Register API blueprint
from api import init_api
init_api(app)


if __name__ == '__main__':
    print("=" * 60)
    print("Warner Sound Tracker - Internal Dashboard")
    print("=" * 60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()
    # Get port from environment variable (for Railway) or use default
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("Starting INTERNAL TOOL on http://localhost:{}".format(port))
    print("(Port 8000 = Client Reports)")
    print("API endpoints available at http://localhost:{}/api/v1/".format(port))
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(debug=debug, host='0.0.0.0', port=port)
