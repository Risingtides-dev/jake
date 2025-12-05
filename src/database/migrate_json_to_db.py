#!/usr/bin/env python3
"""
Migration script to import existing JSON data into SQLite database
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from config import PROJECT_ROOT, OUTPUT_DIR
from services.database import (
    ensure_account_exists,
    ensure_sound_exists,
    insert_or_update_video,
    create_scrape_session,
    update_scrape_session,
    create_scrape_log,
    get_db_connection
)

# JSON file paths
SCRAPED_DATA_FILE = OUTPUT_DIR / 'scraped_data.json'
FILTERED_DATA_FILE = OUTPUT_DIR / 'filtered_data.json'


def migrate_scraped_data():
    """Migrate scraped_data.json to database."""
    if not SCRAPED_DATA_FILE.exists():
        print(f"⚠️  {SCRAPED_DATA_FILE} not found. Skipping migration.")
        return False
    
    print(f"📦 Migrating {SCRAPED_DATA_FILE}...")
    
    try:
        with open(SCRAPED_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        session_id = data.get('session_id')
        if not session_id:
            print("❌ No session_id found in scraped_data.json")
            return False
        
        settings = data.get('settings', {})
        accounts = settings.get('accounts', [])
        videos = data.get('videos', [])
        
        print(f"  Found {len(accounts)} accounts and {len(videos)} videos")
        
        # Create scrape session
        create_scrape_session(session_id, settings, len(accounts))
        print(f"  ✅ Created session: {session_id}")
        
        # Process each account
        account_stats = {}
        for account in accounts:
            account_id = ensure_account_exists(account)
            account_stats[account] = {
                'account_id': account_id,
                'videos_found': 0,
                'new_videos': 0,
                'updated_videos': 0
            }
        
        # Process videos
        for video in videos:
            account = video.get('account')
            if not account or account not in account_stats:
                continue
            
            account_id = account_stats[account]['account_id']
            is_new, success = insert_or_update_video(video, account_id, session_id)
            
            if success:
                account_stats[account]['videos_found'] += 1
                if is_new:
                    account_stats[account]['new_videos'] += 1
                else:
                    account_stats[account]['updated_videos'] += 1
        
        # Create scrape logs
        for account, stats in account_stats.items():
            create_scrape_log(
                session_id=session_id,
                account_id=stats['account_id'],
                status='success' if stats['videos_found'] > 0 else 'skipped',
                videos_found=stats['videos_found'],
                new_videos=stats['new_videos'],
                updated_videos=stats['updated_videos']
            )
        
        # Update session status
        update_scrape_session(session_id, 'completed')
        
        print(f"  ✅ Migrated {len(videos)} videos")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating scraped_data.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_filtered_data():
    """Migrate filtered_data.json to database (if it exists)."""
    if not FILTERED_DATA_FILE.exists():
        print(f"⚠️  {FILTERED_DATA_FILE} not found. Skipping migration.")
        return False
    
    print(f"📦 Migrating {FILTERED_DATA_FILE}...")
    
    try:
        with open(FILTERED_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        videos = data.get('videos', [])
        print(f"  Found {len(videos)} filtered videos")
        
        # Note: Filtered data doesn't have a session_id, so we'll need to
        # match videos by video_id and mark them as filtered
        # For now, we'll just log that filtered data exists
        print(f"  ✅ Filtered data found (will be handled by application logic)")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating filtered_data.json: {e}")
        return False


def backup_json_files():
    """Create backup of JSON files before migration."""
    backup_dir = OUTPUT_DIR / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if SCRAPED_DATA_FILE.exists():
        import shutil
        shutil.copy2(SCRAPED_DATA_FILE, backup_dir / 'scraped_data.json')
        print(f"  ✅ Backed up {SCRAPED_DATA_FILE} to {backup_dir}")
    
    if FILTERED_DATA_FILE.exists():
        import shutil
        shutil.copy2(FILTERED_DATA_FILE, backup_dir / 'filtered_data.json')
        print(f"  ✅ Backed up {FILTERED_DATA_FILE} to {backup_dir}")
    
    return backup_dir


def main():
    """Main migration function."""
    print("=" * 60)
    print("WARNER SOUND TRACKER - JSON TO DATABASE MIGRATION")
    print("=" * 60)
    print()
    
    # Check if database exists
    db_path = PROJECT_ROOT / 'tracker.db'
    if not db_path.exists():
        print("❌ Database not found. Please run: python3 init_db.py")
        sys.exit(1)
    
    # Backup JSON files
    print("📦 Creating backup of JSON files...")
    backup_dir = backup_json_files()
    print()
    
    # Migrate scraped data
    print("🔄 Migrating scraped data...")
    success1 = migrate_scraped_data()
    print()
    
    # Migrate filtered data
    print("🔄 Migrating filtered data...")
    success2 = migrate_filtered_data()
    print()
    
    if success1 or success2:
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print(f"📁 Backups saved to: {backup_dir}")
        print("=" * 60)
    else:
        print("=" * 60)
        print("⚠️  No data migrated (JSON files may not exist)")
        print("=" * 60)


if __name__ == '__main__':
    main()

