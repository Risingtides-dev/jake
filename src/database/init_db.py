#!/usr/bin/env python3
"""
Warner Sound Tracker - Database Initialization Script

This script creates and initializes the SQLite database for the Warner Sound Tracker.
It defines the schema for storing scraped TikTok data, tracking scrape sessions,
and maintaining historical records.

Usage:
    python3 init_db.py [--reset]

Options:
    --reset     Drop existing tables and recreate (WARNING: destroys all data)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Import configuration
from config import PROJECT_ROOT, CONFIG_DIR

# Database path
DB_PATH = PROJECT_ROOT / 'tracker.db'


def create_tables(conn):
    """Create all database tables with proper schema."""
    cursor = conn.cursor()

    # ============================================
    # ACCOUNTS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT,
            followers INTEGER,
            following INTEGER,
            total_videos INTEGER,
            total_likes INTEGER,
            bio TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_target_account BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_scraped_at TIMESTAMP,
            scrape_count INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')

    # ============================================
    # VIDEOS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL UNIQUE,
            account_id INTEGER NOT NULL,
            tiktok_url TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            caption TEXT,
            hashtags TEXT,
            sound_id INTEGER,
            duration INTEGER,
            is_deleted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
            FOREIGN KEY (sound_id) REFERENCES sounds (id) ON DELETE SET NULL
        )
    ''')

    # ============================================
    # SOUNDS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sound_key TEXT NOT NULL UNIQUE,
            song_title TEXT NOT NULL,
            artist_name TEXT,
            is_exclusive BOOLEAN DEFAULT 0,
            total_usage_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_shares INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')

    # ============================================
    # SCRAPE_SESSIONS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'running',
            total_accounts INTEGER DEFAULT 0,
            successful_scrapes INTEGER DEFAULT 0,
            failed_scrapes INTEGER DEFAULT 0,
            total_videos_scraped INTEGER DEFAULT 0,
            total_new_videos INTEGER DEFAULT 0,
            total_updated_videos INTEGER DEFAULT 0,
            error_log TEXT,
            configuration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ============================================
    # SCRAPE_LOGS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            account_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            videos_found INTEGER DEFAULT 0,
            new_videos INTEGER DEFAULT 0,
            updated_videos INTEGER DEFAULT 0,
            error_message TEXT,
            execution_time_seconds REAL,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
        )
    ''')

    # ============================================
    # VIDEO_HISTORY TABLE (for tracking metric changes over time)
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE
        )
    ''')

    # ============================================
    # EXCLUSIVE_SONGS TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exclusive_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sound_key TEXT NOT NULL UNIQUE,
            song_title TEXT NOT NULL,
            artist_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by TEXT DEFAULT 'system',
            reason TEXT,
            FOREIGN KEY (sound_key) REFERENCES sounds (sound_key) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    print("✅ Tables created successfully")


def create_indexes(conn):
    """Create indexes for better query performance."""
    cursor = conn.cursor()

    indexes = [
        # Accounts indexes
        'CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)',
        'CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active)',
        'CREATE INDEX IF NOT EXISTS idx_accounts_target ON accounts(is_target_account)',
        'CREATE INDEX IF NOT EXISTS idx_accounts_last_scraped ON accounts(last_scraped_at)',

        # Videos indexes
        'CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id)',
        'CREATE INDEX IF NOT EXISTS idx_videos_account_id ON videos(account_id)',
        'CREATE INDEX IF NOT EXISTS idx_videos_sound_id ON videos(sound_id)',
        'CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date)',
        'CREATE INDEX IF NOT EXISTS idx_videos_views ON videos(views)',
        'CREATE INDEX IF NOT EXISTS idx_videos_engagement ON videos(engagement_rate)',

        # Sounds indexes
        'CREATE INDEX IF NOT EXISTS idx_sounds_sound_key ON sounds(sound_key)',
        'CREATE INDEX IF NOT EXISTS idx_sounds_exclusive ON sounds(is_exclusive)',
        'CREATE INDEX IF NOT EXISTS idx_sounds_usage_count ON sounds(total_usage_count)',

        # Scrape sessions indexes
        'CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON scrape_sessions(session_id)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON scrape_sessions(start_time)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_status ON scrape_sessions(status)',

        # Scrape logs indexes
        'CREATE INDEX IF NOT EXISTS idx_logs_session_id ON scrape_logs(session_id)',
        'CREATE INDEX IF NOT EXISTS idx_logs_account_id ON scrape_logs(account_id)',
        'CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON scrape_logs(timestamp)',

        # Video history indexes
        'CREATE INDEX IF NOT EXISTS idx_history_video_id ON video_history(video_id)',
        'CREATE INDEX IF NOT EXISTS idx_history_session_id ON video_history(session_id)',
        'CREATE INDEX IF NOT EXISTS idx_history_scraped_at ON video_history(scraped_at)',
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    conn.commit()
    print("✅ Indexes created successfully")


def create_triggers(conn):
    """Create triggers for automatic timestamp updates."""
    cursor = conn.cursor()

    # Update timestamp trigger for accounts
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_accounts_timestamp
        AFTER UPDATE ON accounts
        BEGIN
            UPDATE accounts SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    ''')

    # Update timestamp trigger for videos
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_videos_timestamp
        AFTER UPDATE ON videos
        BEGIN
            UPDATE videos SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    ''')

    # Update timestamp trigger for sounds
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_sounds_timestamp
        AFTER UPDATE ON sounds
        BEGIN
            UPDATE sounds SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END
    ''')

    conn.commit()
    print("✅ Triggers created successfully")


def insert_sample_data(conn):
    """Insert sample/seed data for testing."""
    cursor = conn.cursor()

    # Check if we already have data
    cursor.execute('SELECT COUNT(*) FROM accounts')
    if cursor.fetchone()[0] > 0:
        print("⚠️  Database already contains data. Skipping sample data insertion.")
        return

    print("📝 Inserting sample data...")

    # Sample account (for testing)
    cursor.execute('''
        INSERT INTO accounts (username, display_name, is_active, is_target_account)
        VALUES (?, ?, ?, ?)
    ''', ('@sample_account', 'Sample Account', 1, 0))

    conn.commit()
    print("✅ Sample data inserted successfully")


def reset_database(conn):
    """Drop all tables and recreate them (WARNING: destroys all data)."""
    cursor = conn.cursor()

    print("⚠️  WARNING: Dropping all tables...")

    tables = [
        'video_history',
        'scrape_logs',
        'scrape_sessions',
        'exclusive_songs',
        'videos',
        'sounds',
        'accounts'
    ]

    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')

    conn.commit()
    print("✅ All tables dropped")


def show_database_info(conn):
    """Display information about the database."""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE INFORMATION")
    print("="*60)

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\n📊 Tables: {len(tables)}")
    for table in tables:
        table_name = table[0]
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} rows")

    print(f"\n💾 Database Location: {DB_PATH}")
    print(f"📏 Database Size: {DB_PATH.stat().st_size / 1024:.2f} KB")
    print("="*60 + "\n")


def main():
    """Main function to initialize the database."""
    parser = argparse.ArgumentParser(description='Initialize Warner Sound Tracker database')
    parser.add_argument('--reset', action='store_true',
                       help='Drop existing tables and recreate (WARNING: destroys all data)')
    parser.add_argument('--info', action='store_true',
                       help='Show database information')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("WARNER SOUND TRACKER - DATABASE INITIALIZATION")
    print("="*60 + "\n")

    # Check if database exists
    db_exists = DB_PATH.exists()

    if db_exists and args.reset:
        response = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted.")
            return

    try:
        # Connect to database (creates it if it doesn't exist)
        conn = sqlite3.connect(DB_PATH)
        print(f"📦 Connected to database: {DB_PATH}")

        if args.reset:
            reset_database(conn)

        if args.info and not args.reset:
            show_database_info(conn)
            return

        # Create schema
        create_tables(conn)
        create_indexes(conn)
        create_triggers(conn)

        # Insert sample data if this is a fresh database
        if not db_exists or args.reset:
            insert_sample_data(conn)

        # Show info
        show_database_info(conn)

        print("✅ Database initialization completed successfully!\n")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
