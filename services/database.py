#!/usr/bin/env python3
"""
Database connection and query helpers for Warner Sound Tracker
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from config import PROJECT_ROOT
import os

# Database path - can be overridden by environment variable (for Railway)
db_path_str = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'tracker.db'))
DB_PATH = Path(db_path_str)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_account_exists(username: str) -> int:
    """Ensure account exists in database, create if needed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM accounts WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            return result['id']
        
        # Create new account
        cursor.execute('''
            INSERT INTO accounts (username, is_active, is_target_account)
            VALUES (?, ?, ?)
        ''', (username, 1, 0))
        
        return cursor.lastrowid


def ensure_sound_exists(song_title: str, artist_name: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> Optional[int]:
    """Ensure sound exists in database, create if needed."""
    if not song_title:
        return None
    
    sound_key = f"{song_title} - {artist_name}" if artist_name else song_title
    
    # Use provided connection or create new one
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM sounds WHERE sound_key = ?', (sound_key,))
        result = cursor.fetchone()
        
        if result:
            return result['id']
        
        # Create new sound
        cursor.execute('''
            INSERT INTO sounds (sound_key, song_title, artist_name, is_exclusive)
            VALUES (?, ?, ?, ?)
        ''', (sound_key, song_title, artist_name, 0))
        
        return cursor.lastrowid
    else:
        with get_db_connection() as db_conn:
            cursor = db_conn.cursor()
            cursor.execute('SELECT id FROM sounds WHERE sound_key = ?', (sound_key,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # Create new sound
            cursor.execute('''
                INSERT INTO sounds (sound_key, song_title, artist_name, is_exclusive)
                VALUES (?, ?, ?, ?)
            ''', (sound_key, song_title, artist_name, 0))
            
            return cursor.lastrowid


def insert_or_update_video(video_data: Dict, account_id: int, session_id: str) -> Tuple[bool, bool]:
    """
    Insert or update video in database.
    Returns: (is_new, success)
    """
    video_id = video_data.get('video_id')
    if not video_id:
        return False, False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if video exists
        cursor.execute('SELECT id FROM videos WHERE video_id = ?', (video_id,))
        existing = cursor.fetchone()
        
        # Get or create sound (using same connection)
        sound_id = ensure_sound_exists(
            video_data.get('song_title'),
            video_data.get('artist_name'),
            conn=conn
        )
        
        if existing:
            # Update existing video
            cursor.execute('''
                UPDATE videos
                SET views = ?,
                    likes = ?,
                    comments = ?,
                    shares = ?,
                    engagement_rate = ?,
                    caption = ?,
                    sound_id = ?
                WHERE video_id = ?
            ''', (
                video_data.get('views', 0),
                video_data.get('likes', 0),
                video_data.get('comments', 0),
                video_data.get('shares', 0),
                video_data.get('engagement_rate', 0.0),
                video_data.get('caption'),
                sound_id,
                video_id
            ))
            
            # Create history snapshot (using same connection)
            create_video_history_internal(video_id, session_id, video_data, conn)
            
            return False, True
        else:
            # Insert new video
            cursor.execute('''
                INSERT INTO videos (
                    video_id, account_id, tiktok_url, upload_date,
                    views, likes, comments, shares, engagement_rate,
                    caption, sound_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                account_id,
                video_data.get('url'),
                video_data.get('upload_date'),
                video_data.get('views', 0),
                video_data.get('likes', 0),
                video_data.get('comments', 0),
                video_data.get('shares', 0),
                video_data.get('engagement_rate', 0.0),
                video_data.get('caption'),
                sound_id
            ))
            
            # Create history snapshot (using same connection)
            create_video_history_internal(video_id, session_id, video_data, conn)
            
            return True, True


def create_video_history_internal(video_id: str, session_id: str, video_data: Dict, conn: sqlite3.Connection):
    """Create a historical snapshot of video metrics (internal, uses provided connection)."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO video_history (
            video_id, session_id, views, likes, comments, shares, engagement_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        video_id,
        session_id,
        video_data.get('views', 0),
        video_data.get('likes', 0),
        video_data.get('comments', 0),
        video_data.get('shares', 0),
        video_data.get('engagement_rate', 0.0)
    ))


def create_video_history(video_id: str, session_id: str, video_data: Dict):
    """Create a historical snapshot of video metrics."""
    with get_db_connection() as conn:
        create_video_history_internal(video_id, session_id, video_data, conn)


def create_scrape_session(session_id: str, settings: Dict, total_accounts: int) -> bool:
    """Create a new scrape session."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scrape_sessions (
                    session_id, start_time, status, total_accounts, configuration
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                datetime.now().isoformat(),
                'running',
                total_accounts,
                json.dumps(settings)
            ))
            return True
    except sqlite3.IntegrityError:
        # Session already exists
        return False


def update_scrape_session(session_id: str, status: str, error_log: Optional[str] = None):
    """Update scrape session with final statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get statistics from scrape_logs
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(videos_found) as total_videos,
                SUM(new_videos) as new_videos,
                SUM(updated_videos) as updated_videos
            FROM scrape_logs
            WHERE session_id = ?
        ''', (session_id,))
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            UPDATE scrape_sessions
            SET end_time = ?,
                status = ?,
                successful_scrapes = ?,
                failed_scrapes = ?,
                total_videos_scraped = ?,
                total_new_videos = ?,
                total_updated_videos = ?,
                error_log = ?
            WHERE session_id = ?
        ''', (
            datetime.now().isoformat(),
            status,
            stats['successful'] or 0,
            stats['failed'] or 0,
            stats['total_videos'] or 0,
            stats['new_videos'] or 0,
            stats['updated_videos'] or 0,
            error_log,
            session_id
        ))


def create_scrape_log(session_id: str, account_id: int, status: str, 
                     videos_found: int = 0, new_videos: int = 0, 
                     updated_videos: int = 0, error_message: Optional[str] = None,
                     execution_time: float = 0.0):
    """Create a log entry for a scrape attempt."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scrape_logs (
                session_id, account_id, status, videos_found,
                new_videos, updated_videos, error_message, execution_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, account_id, status, videos_found,
            new_videos, updated_videos, error_message, execution_time
        ))


def get_session(session_id: str) -> Optional[Dict]:
    """Get scrape session by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM scrape_sessions WHERE session_id = ?
        ''', (session_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None


def get_videos_by_session(session_id: str, filters: Optional[Dict] = None) -> List[Dict]:
    """Get videos for a session with optional filters."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get video IDs from history for this session
        cursor.execute('SELECT DISTINCT video_id FROM video_history WHERE session_id = ?', (session_id,))
        video_ids = [row[0] for row in cursor.fetchall()]
        
        if not video_ids:
            return []
        
        # Build query with IN clause
        placeholders = ','.join('?' * len(video_ids))
        query = f'''
            SELECT v.*, a.username as account, s.sound_key, s.song_title, s.artist_name
            FROM videos v
            JOIN accounts a ON v.account_id = a.id
            LEFT JOIN sounds s ON v.sound_id = s.id
            WHERE v.video_id IN ({placeholders})
        '''
        
        params = list(video_ids)
        
        if filters:
            if filters.get('start_date'):
                query += ' AND v.upload_date >= ?'
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += ' AND v.upload_date <= ?'
                params.append(filters['end_date'])
            if filters.get('account'):
                query += ' AND a.username = ?'
                params.append(filters['account'])
            if filters.get('sound_key'):
                query += ' AND s.sound_key = ?'
                params.append(filters['sound_key'])
        
        query += ' ORDER BY v.upload_date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dict and ensure all fields are present
        videos = []
        for row in rows:
            video = dict(row)
            # Ensure url field exists (use tiktok_url)
            if 'url' not in video and 'tiktok_url' in video:
                video['url'] = video['tiktok_url']
            videos.append(video)
        
        return videos


def get_sounds_by_session(session_id: str) -> List[Dict]:
    """Get sounds with aggregation stats for a session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                s.id,
                s.sound_key,
                s.song_title,
                s.artist_name,
                COUNT(DISTINCT v.id) as video_count,
                SUM(v.views) as total_views,
                SUM(v.likes) as total_likes,
                SUM(v.comments) as total_comments,
                SUM(v.shares) as total_shares,
                AVG(v.engagement_rate) as avg_engagement_rate
            FROM sounds s
            JOIN videos v ON s.id = v.sound_id
            WHERE v.id IN (
                SELECT DISTINCT vh.video_id
                FROM video_history vh
                WHERE vh.session_id = ?
            )
            GROUP BY s.id, s.sound_key, s.song_title, s.artist_name
            ORDER BY video_count DESC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_sessions(limit: int = 50) -> List[Dict]:
    """Get all scrape sessions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM scrape_sessions
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_accounts() -> List[Dict]:
    """Get all accounts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE is_active = 1')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_account_last_scraped(account_id: int):
    """Update account's last_scraped_at timestamp."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts
            SET last_scraped_at = ?,
                scrape_count = scrape_count + 1
            WHERE id = ?
        ''', (datetime.now().isoformat(), account_id))

