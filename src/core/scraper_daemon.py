#!/usr/bin/env python3
"""
Warner Sound Tracker - Automated Scraping Daemon

This daemon automatically scrapes TikTok accounts on a schedule, using timestamp
tracking to only scrape accounts that haven't been updated recently. It stores
all data in the SQLite database for persistent storage and historical tracking.

Usage:
    python3 scraper_daemon.py [--interval HOURS] [--once] [--force]

Options:
    --interval HOURS    Hours between scrape checks (default: 24)
    --once              Run once and exit (don't loop)
    --force             Force scrape all accounts (ignore last_scraped_at)
    --accounts ACC1,ACC2  Only scrape specific accounts (comma-separated)
    --verbose           Enable verbose logging

Examples:
    # Run daemon with 24-hour interval
    python3 scraper_daemon.py

    # Run once (for testing or cron jobs)
    python3 scraper_daemon.py --once

    # Force immediate scrape of all accounts
    python3 scraper_daemon.py --once --force

    # Scrape specific accounts
    python3 scraper_daemon.py --once --accounts @account1,@account2
"""

import argparse
import json
import logging
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import configuration
from config import (
    ACCOUNTS,
    CUTOFF_DATE,
    EXCLUSIVE_SONGS,
    OUTPUT_DIR,
    PROJECT_ROOT
)

# Database path
DB_PATH = PROJECT_ROOT / 'tracker.db'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'scraper.log')
    ]
)
logger = logging.getLogger(__name__)


class ScraperDaemon:
    """Main scraper daemon class."""

    def __init__(self, interval_hours: int = 24, force: bool = False,
                 specific_accounts: Optional[List[str]] = None):
        """
        Initialize the scraper daemon.

        Args:
            interval_hours: Hours between scrape checks
            force: Force scrape all accounts regardless of last_scraped_at
            specific_accounts: List of specific accounts to scrape (or None for all)
        """
        self.interval_hours = interval_hours
        self.force = force
        self.specific_accounts = specific_accounts
        self.conn = None
        self.session_id = None

        # Ensure database exists
        if not DB_PATH.exists():
            logger.error(f"Database not found at {DB_PATH}")
            logger.error("Please run: python3 init_db.py")
            sys.exit(1)

    def connect_db(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {DB_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            sys.exit(1)

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def get_accounts_to_scrape(self) -> List[Tuple[str, Optional[str]]]:
        """
        Get list of accounts that need scraping.

        Returns:
            List of tuples: (username, last_scraped_at)
        """
        cursor = self.conn.cursor()

        # Build account list
        if self.specific_accounts:
            accounts_to_check = self.specific_accounts
        else:
            accounts_to_check = ACCOUNTS

        accounts_needing_scrape = []

        for username in accounts_to_check:
            # Check if account exists in database
            cursor.execute('SELECT id, last_scraped_at FROM accounts WHERE username = ?',
                          (username,))
            result = cursor.fetchone()

            if result is None:
                # Account not in database - needs scraping
                logger.info(f"Account {username} not in database - will scrape")
                accounts_needing_scrape.append((username, None))
            else:
                account_id, last_scraped = result
                if self.force:
                    # Force mode - scrape regardless of timestamp
                    logger.info(f"Force mode: will scrape {username}")
                    accounts_needing_scrape.append((username, last_scraped))
                elif last_scraped is None:
                    # Never scraped before
                    logger.info(f"Account {username} never scraped - will scrape")
                    accounts_needing_scrape.append((username, last_scraped))
                else:
                    # Check if scrape is stale
                    last_scraped_dt = datetime.fromisoformat(last_scraped)
                    threshold = datetime.now() - timedelta(hours=self.interval_hours)

                    if last_scraped_dt < threshold:
                        logger.info(f"Account {username} last scraped {last_scraped} - will scrape")
                        accounts_needing_scrape.append((username, last_scraped))
                    else:
                        logger.debug(f"Account {username} recently scraped - skipping")

        return accounts_needing_scrape

    def create_scrape_session(self) -> str:
        """
        Create a new scrape session in the database.

        Returns:
            Session ID (UUID)
        """
        self.session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO scrape_sessions (
                session_id, start_time, status, total_accounts, configuration
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            datetime.now().isoformat(),
            'running',
            len(ACCOUNTS) if not self.specific_accounts else len(self.specific_accounts),
            json.dumps({
                'interval_hours': self.interval_hours,
                'force': self.force,
                'specific_accounts': self.specific_accounts,
                'cutoff_date': CUTOFF_DATE.isoformat() if CUTOFF_DATE else None
            })
        ))

        self.conn.commit()
        logger.info(f"Created scrape session: {self.session_id}")
        return self.session_id

    def update_scrape_session(self, status: str, error_log: Optional[str] = None):
        """
        Update the scrape session with final statistics.

        Args:
            status: Session status (completed, failed, partial)
            error_log: Optional error log text
        """
        cursor = self.conn.cursor()

        # Get statistics from scrape_logs for this session
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
        ''', (self.session_id,))

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
            self.session_id
        ))

        self.conn.commit()
        logger.info(f"Updated scrape session: {status}")

    def ensure_account_exists(self, username: str) -> int:
        """
        Ensure account exists in database, create if needed.

        Args:
            username: TikTok username (with @)

        Returns:
            Account ID
        """
        cursor = self.conn.cursor()

        cursor.execute('SELECT id FROM accounts WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            return result['id']

        # Create new account
        is_target = username in getattr(self, 'target_accounts', set())

        cursor.execute('''
            INSERT INTO accounts (username, is_active, is_target_account)
            VALUES (?, ?, ?)
        ''', (username, 1, is_target))

        self.conn.commit()
        account_id = cursor.lastrowid
        logger.info(f"Created new account: {username} (ID: {account_id})")
        return account_id

    def scrape_account(self, username: str, last_scraped_at: Optional[str]) -> Tuple[str, Dict]:
        """
        Scrape a single TikTok account using tiktok_analyzer.py.

        Args:
            username: TikTok username (with @)
            last_scraped_at: ISO timestamp of last scrape (or None)

        Returns:
            Tuple of (status, result_dict)
            status: 'success', 'failed', 'skipped'
            result_dict: Contains videos_found, new_videos, updated_videos, error_message
        """
        start_time = time.time()
        account_id = self.ensure_account_exists(username)

        result = {
            'videos_found': 0,
            'new_videos': 0,
            'updated_videos': 0,
            'error_message': None
        }

        try:
            # Run tiktok_analyzer.py
            logger.info(f"Scraping {username}...")

            cmd = [
                'python3',
                str(PROJECT_ROOT / 'tiktok_analyzer.py'),
                '--url', username,
                '--limit', '100',  # Adjust as needed
                '--json'  # Request JSON output (we'll need to modify tiktok_analyzer.py to support this)
            ]

            # For now, we'll parse the text output
            # TODO: Add --json flag to tiktok_analyzer.py for structured output
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if process.returncode != 0:
                error_msg = process.stderr or "Unknown error"
                logger.error(f"Error scraping {username}: {error_msg}")
                result['error_message'] = error_msg
                status = 'failed'
            else:
                # Parse output (this is a simplified version)
                # In production, should use JSON output from analyzer
                output = process.stdout
                videos = self._parse_analyzer_output(output)

                result['videos_found'] = len(videos)

                # Process each video
                for video_data in videos:
                    # Check if video exists
                    cursor = self.conn.cursor()
                    cursor.execute('SELECT id FROM videos WHERE video_id = ?',
                                 (video_data['video_id'],))
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing video
                        self._update_video(video_data, account_id)
                        result['updated_videos'] += 1
                    else:
                        # Insert new video
                        self._insert_video(video_data, account_id)
                        result['new_videos'] += 1

                    # Create history snapshot
                    self._create_video_history(video_data['video_id'])

                # Update account metadata
                cursor.execute('''
                    UPDATE accounts
                    SET last_scraped_at = ?,
                        scrape_count = scrape_count + 1
                    WHERE id = ?
                ''', (datetime.now().isoformat(), account_id))

                self.conn.commit()
                status = 'success'
                logger.info(f"✅ {username}: {result['videos_found']} videos "
                          f"({result['new_videos']} new, {result['updated_videos']} updated)")

        except subprocess.TimeoutExpired:
            error_msg = "Scrape timeout (>5 minutes)"
            logger.error(f"Timeout scraping {username}")
            result['error_message'] = error_msg
            status = 'failed'

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception scraping {username}: {error_msg}")
            result['error_message'] = error_msg
            status = 'failed'

        # Log the scrape attempt
        execution_time = time.time() - start_time
        self._create_scrape_log(account_id, status, result, execution_time)

        return status, result

    def _parse_analyzer_output(self, output: str) -> List[Dict]:
        """
        Parse tiktok_analyzer.py output.

        This is a simplified parser. In production, tiktok_analyzer.py should
        output JSON for easier parsing.

        Args:
            output: Text output from tiktok_analyzer.py

        Returns:
            List of video dictionaries
        """
        # This is a placeholder - needs to be implemented based on actual output format
        # For now, return empty list
        # TODO: Modify tiktok_analyzer.py to output JSON with --json flag
        logger.warning("Video parsing not yet implemented - please add --json flag to tiktok_analyzer.py")
        return []

    def _insert_video(self, video_data: Dict, account_id: int):
        """Insert a new video into the database."""
        cursor = self.conn.cursor()

        # Get or create sound
        sound_id = self._ensure_sound_exists(video_data.get('song_title'), video_data.get('artist'))

        cursor.execute('''
            INSERT INTO videos (
                video_id, account_id, tiktok_url, upload_date,
                views, likes, comments, shares, engagement_rate,
                caption, sound_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_data['video_id'],
            account_id,
            video_data['url'],
            video_data['upload_date'],
            video_data.get('views', 0),
            video_data.get('likes', 0),
            video_data.get('comments', 0),
            video_data.get('shares', 0),
            video_data.get('engagement_rate', 0.0),
            video_data.get('caption'),
            sound_id
        ))

    def _update_video(self, video_data: Dict, account_id: int):
        """Update an existing video in the database."""
        cursor = self.conn.cursor()

        cursor.execute('''
            UPDATE videos
            SET views = ?,
                likes = ?,
                comments = ?,
                shares = ?,
                engagement_rate = ?
            WHERE video_id = ?
        ''', (
            video_data.get('views', 0),
            video_data.get('likes', 0),
            video_data.get('comments', 0),
            video_data.get('shares', 0),
            video_data.get('engagement_rate', 0.0),
            video_data['video_id']
        ))

    def _ensure_sound_exists(self, song_title: Optional[str], artist: Optional[str]) -> Optional[int]:
        """Ensure sound exists in database, create if needed."""
        if not song_title:
            return None

        cursor = self.conn.cursor()
        sound_key = f"{song_title} - {artist}" if artist else song_title

        cursor.execute('SELECT id FROM sounds WHERE sound_key = ?', (sound_key,))
        result = cursor.fetchone()

        if result:
            return result['id']

        # Create new sound
        is_exclusive = sound_key in EXCLUSIVE_SONGS

        cursor.execute('''
            INSERT INTO sounds (sound_key, song_title, artist_name, is_exclusive)
            VALUES (?, ?, ?, ?)
        ''', (sound_key, song_title, artist, is_exclusive))

        self.conn.commit()
        return cursor.lastrowid

    def _create_video_history(self, video_id: str):
        """Create a historical snapshot of video metrics."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO video_history (video_id, session_id, views, likes, comments, shares, engagement_rate)
            SELECT video_id, ?, views, likes, comments, shares, engagement_rate
            FROM videos
            WHERE video_id = ?
        ''', (self.session_id, video_id))

    def _create_scrape_log(self, account_id: int, status: str, result: Dict, execution_time: float):
        """Create a log entry for this scrape attempt."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO scrape_logs (
                session_id, account_id, status, videos_found,
                new_videos, updated_videos, error_message, execution_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            account_id,
            status,
            result['videos_found'],
            result['new_videos'],
            result['updated_videos'],
            result['error_message'],
            execution_time
        ))

        self.conn.commit()

    def run_once(self):
        """Run the scraper once and exit."""
        logger.info("="*60)
        logger.info("WARNER SOUND TRACKER - SCRAPING SESSION")
        logger.info("="*60)

        self.connect_db()

        try:
            # Get accounts to scrape
            accounts = self.get_accounts_to_scrape()

            if not accounts:
                logger.info("No accounts need scraping at this time.")
                return

            logger.info(f"Found {len(accounts)} account(s) to scrape")

            # Create session
            self.create_scrape_session()

            # Scrape each account
            success_count = 0
            fail_count = 0

            for username, last_scraped in accounts:
                status, result = self.scrape_account(username, last_scraped)

                if status == 'success':
                    success_count += 1
                else:
                    fail_count += 1

            # Update session
            if fail_count == 0:
                session_status = 'completed'
            elif success_count == 0:
                session_status = 'failed'
            else:
                session_status = 'partial'

            self.update_scrape_session(session_status)

            logger.info("="*60)
            logger.info(f"SESSION COMPLETE: {success_count} successful, {fail_count} failed")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Critical error during scrape: {e}")
            if self.session_id:
                self.update_scrape_session('failed', str(e))

        finally:
            self.close_db()

    def run_daemon(self):
        """Run the scraper as a daemon (infinite loop with sleep)."""
        logger.info("Starting scraper daemon...")
        logger.info(f"Interval: {self.interval_hours} hours")

        while True:
            self.run_once()

            # Sleep until next run
            sleep_seconds = self.interval_hours * 3600
            logger.info(f"Sleeping for {self.interval_hours} hours...")
            time.sleep(sleep_seconds)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Warner Sound Tracker - Automated Scraping Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--interval', type=int, default=24,
                       help='Hours between scrape checks (default: 24)')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (don\'t loop)')
    parser.add_argument('--force', action='store_true',
                       help='Force scrape all accounts (ignore last_scraped_at)')
    parser.add_argument('--accounts', type=str,
                       help='Comma-separated list of accounts to scrape (e.g., @acc1,@acc2)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Parse specific accounts if provided
    specific_accounts = None
    if args.accounts:
        specific_accounts = [acc.strip() for acc in args.accounts.split(',')]

    # Create daemon instance
    daemon = ScraperDaemon(
        interval_hours=args.interval,
        force=args.force,
        specific_accounts=specific_accounts
    )

    # Run
    if args.once:
        daemon.run_once()
    else:
        try:
            daemon.run_daemon()
        except KeyboardInterrupt:
            logger.info("\nDaemon stopped by user")
            sys.exit(0)


if __name__ == '__main__':
    main()
