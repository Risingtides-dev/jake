#!/usr/bin/env python3
"""
Run all campaigns with automatic cache validation.
Clears caches for accounts that need to go back further than what's cached.
"""

import sys
import argparse
import pickle
from pathlib import Path
from datetime import datetime
import subprocess

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_profile_username(url_or_username):
    """Extract username from TikTok profile URL or handle"""
    import re
    if not url_or_username or not isinstance(url_or_username, str):
        return None
    if not url_or_username.startswith('http'):
        username = url_or_username.lstrip('@')
        return username
    match = re.search(r'@([\w\.]+)', url_or_username)
    if match:
        return match.group(1)
    return None

def get_earliest_video_date(cached_videos):
    """Get the earliest upload date from cached videos"""
    if not cached_videos:
        return None
    
    earliest = None
    for video in cached_videos:
        upload_date = video.get('upload_date', '')
        if upload_date:
            try:
                date_obj = datetime.strptime(upload_date, '%Y%m%d').date()
                if earliest is None or date_obj < earliest:
                    earliest = date_obj
            except (ValueError, TypeError):
                continue
    
    return earliest

def check_and_clear_caches(csv_path, start_date):
    """Check caches for accounts in CSV and clear if needed"""
    import csv
    
    if not start_date:
        return 0
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    except ValueError:
        print(f"[WARNING] Invalid start date format: {start_date}")
        return 0
    
    accounts_to_check = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            account = None
            for col in ['Account', 'account', 'Account URL', 'URL', 'account Handle', 'Creator Handles']:
                if col in row and row[col]:
                    account = row[col].strip()
                    break
            if account:
                accounts_to_check.append(account)
    
    cleared_count = 0
    for account in accounts_to_check:
        username = get_profile_username(account)
        if not username:
            continue
        
        cache_file = CACHE_DIR / f"{username}_cache.pkl"
        if not cache_file.exists():
            continue
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                cached_videos = cache_data.get('videos', [])
            
            earliest_date = get_earliest_video_date(cached_videos)
            
            # If cache doesn't go back far enough, clear it
            if earliest_date is None or earliest_date > start_date_obj:
                print(f"  [CACHE] Clearing cache for @{username} (earliest: {earliest_date}, need: {start_date_obj})")
                cache_file.unlink()
                cleared_count += 1
            else:
                print(f"  [CACHE] @{username} cache OK (earliest: {earliest_date}, need: {start_date_obj})")
        except Exception as e:
            print(f"  [WARNING] Error checking cache for @{username}: {e}")
            # If we can't read the cache, clear it to be safe
            if cache_file.exists():
                cache_file.unlink()
                cleared_count += 1
    
    return cleared_count

def main():
    parser = argparse.ArgumentParser(
        description='Run all campaigns with automatic cache validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use start dates from CSV files (checks caches automatically)
  python run_all_campaigns_with_cache_check.py
  
  # Override start date for all campaigns
  python run_all_campaigns_with_cache_check.py --start-date "2025-11-19"
  
  # Force clear all caches first
  python run_all_campaigns_with_cache_check.py --clear-all-caches
        """
    )
    parser.add_argument('--start-date', 
                       help='Override start date for all campaigns (YYYY-MM-DD). If not provided, uses dates from CSV files.')
    parser.add_argument('--clear-all-caches', 
                       action='store_true',
                       help='Clear all caches before running (nuclear option)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("RUNNING ALL CAMPAIGNS WITH CACHE VALIDATION")
    print("=" * 80)
    print()
    
    # Clear all caches if requested
    if args.clear_all_caches:
        print("[INFO] Clearing all caches...")
        cache_files = list(CACHE_DIR.glob("*.pkl"))
        for cache_file in cache_files:
            cache_file.unlink()
        print(f"[INFO] Cleared {len(cache_files)} cache files")
        print()
    
    # Import the campaign runner to get CSV files
    from pathlib import Path as PathLib
    CLAUDE_SANDBOX = PathLib(r"C:\Users\jakeb\OneDrive\Desktop\Claude Sandbox")
    
    csv_files = list(CLAUDE_SANDBOX.glob("2025 Sound Campaigns - *.csv"))
    csv_files = [f for f in csv_files if 'Chariot' not in f.name]
    
    if not csv_files:
        print(f"[INFO] No campaign CSV files found in {CLAUDE_SANDBOX}")
        print("[INFO] Will check caches for campaigns in output/ directory instead")
        
        # Check existing campaign CSVs in output directory
        output_dir = PathLib("output")
        campaign_csvs = list(output_dir.glob("*_campaign.csv"))
        
        if campaign_csvs:
            print(f"[INFO] Found {len(campaign_csvs)} campaign CSVs in output/")
            for csv_file in campaign_csvs:
                if args.start_date:
                    cleared = check_and_clear_caches(csv_file, args.start_date)
                    if cleared > 0:
                        print(f"  [INFO] Cleared {cleared} caches for {csv_file.name}")
        else:
            print("[INFO] No campaign CSVs found. Skipping cache check.")
    else:
        print(f"[INFO] Found {len(csv_files)} campaign CSV files")
        print("[INFO] Checking caches for each campaign...")
        print()
        
        # Check caches for each campaign
        for csv_path in sorted(csv_files):
            # Try to extract start date from CSV if not overridden
            start_date_to_check = args.start_date
            if not start_date_to_check:
                import csv as csv_module
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv_module.DictReader(f)
                        for row in reader:
                            if row.get('Start Date'):
                                try:
                                    date_obj = datetime.strptime(row['Start Date'], '%m/%d/%Y')
                                    start_date_to_check = date_obj.strftime('%Y-%m-%d')
                                    break
                                except:
                                    pass
                except:
                    pass
            
            if start_date_to_check:
                # Safely print filename, handling Unicode
                try:
                    print(f"Checking: {csv_path.name}")
                except UnicodeEncodeError:
                    safe_name = csv_path.name.encode('ascii', errors='replace').decode('ascii')
                    print(f"Checking: {safe_name}")
                except Exception:
                    print(f"Checking: [filename with special characters]")
                cleared = check_and_clear_caches(csv_path, start_date_to_check)
                if cleared > 0:
                    print(f"  [INFO] Cleared {cleared} caches")
            else:
                # Safely print filename, handling Unicode
                try:
                    print(f"Skipping cache check for {csv_path.name} (no start date found)")
                except UnicodeEncodeError:
                    safe_name = csv_path.name.encode('ascii', errors='replace').decode('ascii')
                    print(f"Skipping cache check for {safe_name} (no start date found)")
                except Exception:
                    print(f"Skipping cache check for [filename] (no start date found)")
            print()
    
    print("=" * 80)
    print("Running campaigns...")
    print("=" * 80)
    print()
    
    # Now run the actual campaign scraper
    script_path = Path(__file__).parent / 'run_all_campaigns_cached.py'
    
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)
    
    try:
        cmd = [sys.executable, str(script_path)]
        if args.start_date:
            cmd.extend(['--start-date', args.start_date])
        
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            check=True
        )
        
        print("\n" + "=" * 80)
        print("All campaigns completed successfully!")
        print("=" * 80)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Campaigns failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

