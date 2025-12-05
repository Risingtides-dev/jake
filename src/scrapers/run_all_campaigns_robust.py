#!/usr/bin/env python3
"""
Run all 2025 campaigns using the robust scraper with parallel processing
"""

import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime

CLAUDE_SANDBOX = Path(r"C:\Users\jakeb\OneDrive\Desktop\Claude Sandbox")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_song_artist_from_filename(filename):
    """Extract song and artist from CSV filename"""
    match = re.search(r'2025 Sound Campaigns - (.+?) - (.+?)\.csv', filename)
    if match:
        artist = match.group(1).strip()
        song = match.group(2).strip()
        return song, artist
    return None, None

def convert_csv_to_scraper_format(csv_path, song_name, artist_name):
    """Convert campaign CSV to format expected by robust scraper"""
    import csv
    safe_name = f"{song_name.replace(' ', '_').replace(',', '').replace('/', '_')}_{artist_name.replace(' ', '_').replace(',', '').replace('/', '_')}"
    output_csv = OUTPUT_DIR / f"{safe_name}_campaign.csv"
    
    rows = []
    start_date = None
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f_in:
        reader = csv.DictReader(f_in)
        
        for row in reader:
            if not start_date and row.get('Start Date'):
                try:
                    date_obj = datetime.strptime(row['Start Date'], '%m/%d/%Y')
                    start_date = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            creator_handle = row.get('Creator Handles', '').strip()
            if creator_handle:
                rows.append({
                    'Song': song_name,
                    'Artist': artist_name,
                    'Account': creator_handle
                })
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=['Song', 'Artist', 'Account'])
        writer.writeheader()
        writer.writerows(rows)
    
    return output_csv, start_date, len(rows)

def main():
    import csv
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run all 2025 campaigns using robust scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--start-date', 
                       help='Override start date for all campaigns (YYYY-MM-DD)')
    parser.add_argument('--workers', 
                       type=int, default=10,
                       help='Parallel workers for sound ID extraction (default: 10)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("RUNNING ALL 2025 CAMPAIGNS WITH ROBUST SCRAPER")
    print("="*80)
    print()
    
    csv_files = list(CLAUDE_SANDBOX.glob("2025 Sound Campaigns - *.csv"))
    csv_files = [f for f in csv_files if 'Chariot' not in f.name]
    
    if not csv_files:
        print(f"No campaign CSV files found in {CLAUDE_SANDBOX}")
        return
    
    print(f"Found {len(csv_files)} campaign CSV files\n")
    
    results_summary = []
    
    for csv_path in sorted(csv_files):
        filename = csv_path.name
        try:
            print(f"Processing: {filename}")
        except UnicodeEncodeError:
            safe_filename = filename.encode('ascii', 'ignore').decode('ascii')
            print(f"Processing: {safe_filename}")
        
        song_name, artist_name = extract_song_artist_from_filename(filename)
        
        if not song_name or not artist_name:
            print(f"  [WARNING] Could not extract song/artist from filename")
            continue
        
        output_csv, start_date, account_count = convert_csv_to_scraper_format(
            csv_path, song_name, artist_name
        )
        
        # Use override date if provided
        actual_start_date = args.start_date if args.start_date else start_date
        
        if not actual_start_date:
            print(f"  [WARNING] No start date found, skipping")
            continue
        
        campaign_name = f"{song_name} - {artist_name}"
        safe_name = campaign_name.replace(' ', '_').replace(',', '').replace('/', '_')
        output_file = OUTPUT_DIR / f"{safe_name}_robust_results.csv"
        
        print(f"  Campaign: {campaign_name}")
        print(f"  Start Date: {actual_start_date}")
        print(f"  Accounts: {account_count}")
        print(f"  Running robust scraper...")
        
        try:
            cmd = [
                sys.executable,
                'robust_campaign_scraper.py',
                str(output_csv),
                '--start-date', actual_start_date,
                '--platform', 'tiktok',
                '--limit', '2000',  # Increased limit to ensure we get all videos
                '--workers', str(args.workers),
                '--output', str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hours per campaign - take as long as needed
            )
            
            if result.returncode == 0:
                # Count matched videos from output
                matched_match = re.search(r'Matched (\d+) videos', result.stdout)
                matched_count = int(matched_match.group(1)) if matched_match else 0
                print(f"  [SUCCESS] Matched {matched_count} videos")
                results_summary.append({
                    'campaign': campaign_name,
                    'matched': matched_count,
                    'success': True
                })
            else:
                print(f"  [ERROR] {result.stderr[:200]}")
                results_summary.append({
                    'campaign': campaign_name,
                    'matched': 0,
                    'success': False
                })
        
        except subprocess.TimeoutExpired:
            print(f"  [ERROR] Timeout after 1 hour")
            results_summary.append({
                'campaign': campaign_name,
                'matched': 0,
                'success': False
            })
        except Exception as e:
            print(f"  [ERROR] {e}")
            results_summary.append({
                'campaign': campaign_name,
                'matched': 0,
                'success': False
            })
        
        print()
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for result in results_summary:
        status = "[OK]" if result['success'] else "[FAIL]"
        print(f"{status} {result['campaign']}: {result['matched']} videos matched")
    
    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print("="*80)

if __name__ == '__main__':
    import csv
    main()

