#!/usr/bin/env python3
"""
Process all 2025 Sound Campaign CSVs using cached scraper.
Outputs results separated by sound campaign with 24-hour separation.
"""

import csv
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta

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
    """Convert campaign CSV to format expected by scraper"""
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

def handle_attack_attack_csv(csv_path):
    """Special handling for Attack Attack CSV which has 2 sounds"""
    csv1 = OUTPUT_DIR / "ONE_HIT_WONDER_1_campaign.csv"
    csv2 = OUTPUT_DIR / "ONE_HIT_WONDER_2_campaign.csv"
    
    rows1 = []
    rows2 = []
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
            tiktok_sound_ids_str = row.get('Tiktok Sound ID', '').strip()
            
            if creator_handle:
                # Split sound IDs if multiple
                sound_ids = [s.strip() for s in tiktok_sound_ids_str.split(',') if s.strip()]
                
                if len(sound_ids) >= 1:
                    rows1.append({
                        'Song': 'ONE HIT WONDER',
                        'Artist': 'Attack Attack!',
                        'Account': creator_handle
                    })
                
                if len(sound_ids) >= 2:
                    rows2.append({
                        'Song': 'ONE HIT WONDER',
                        'Artist': 'Attack Attack!',
                        'Account': creator_handle
                    })
    
    results = []
    for csv_file, rows, sound_num in [(csv1, rows1, 1), (csv2, rows2, 2)]:
        if rows:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=['Song', 'Artist', 'Account'])
                writer.writeheader()
                writer.writerows(rows)
            results.append((csv_file, start_date, len(rows), f'ONE HIT WONDER - Attack Attack! (Sound {sound_num})'))
    
    return results

def run_scraper(csv_file, start_date, campaign_name, override_start_date=None):
    """Run the cached external accounts scraper"""
    print(f"\n{'='*80}")
    print(f"PROCESSING: {campaign_name}")
    print(f"{'='*80}")
    
    output_file = OUTPUT_DIR / f"{campaign_name.replace(' ', '_').replace(',', '').replace('/', '_')}_results.txt"
    copy_paste_file = OUTPUT_DIR / f"{campaign_name.replace(' ', '_').replace(',', '').replace('/', '_')}_copy_paste.txt"
    
    # Use override date if provided, otherwise use the date from CSV
    actual_start_date = override_start_date if override_start_date else start_date
    
    try:
        result = subprocess.run(
            [
                sys.executable, 
                'scrape_external_accounts_cached.py', 
                str(csv_file), 
                '--start-date', actual_start_date,
                '--output', str(output_file)
            ],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            # Read the copy/paste file that was generated
            if copy_paste_file.exists():
                with open(copy_paste_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                matched_match = re.search(r'Matched (\d+) videos', result.stdout)
                matched_count = int(matched_match.group(1)) if matched_match else 0
                return True, matched_count, content, result.stdout
            else:
                matched_match = re.search(r'Matched (\d+) videos', result.stdout)
                matched_count = int(matched_match.group(1)) if matched_match else 0
                return True, matched_count, "", result.stdout
        else:
            return False, 0, "", result.stderr
    except subprocess.TimeoutExpired:
        return False, 0, "", "Timeout after 10 minutes"
    except Exception as e:
        return False, 0, "", str(e)

def extract_links_from_content(content):
    """Extract all links from content, separating recent and older"""
    lines = content.split('\n')
    current_section = None
    recent_links = []
    older_links = []
    
    in_recent = False
    in_older = False
    
    for line in lines:
        if '--- NEW IN LAST 24 HOURS' in line:
            in_recent = True
            in_older = False
            continue
        elif '--- OLDER VIDEOS' in line:
            in_recent = False
            in_older = True
            continue
        elif line.strip().startswith('http'):
            if in_recent:
                recent_links.append(line.strip())
            elif in_older:
                older_links.append(line.strip())
            else:
                # If no section marker, assume older
                older_links.append(line.strip())
    
    return recent_links, older_links

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process all 2025 Sound Campaign CSVs using cached scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use start dates from CSV files
  python run_all_campaigns_cached.py
  
  # Override start date for all campaigns
  python run_all_campaigns_cached.py --start-date "2025-11-26"
        """
    )
    parser.add_argument('--start-date', 
                       help='Override start date for all campaigns (YYYY-MM-DD). If not provided, uses dates from CSV files.')
    
    args = parser.parse_args()
    
    override_start_date = None
    if args.start_date:
        try:
            # Validate date format
            datetime.strptime(args.start_date, '%Y-%m-%d')
            override_start_date = args.start_date
            print(f"[INFO] Using override start date: {override_start_date} for all campaigns")
        except ValueError:
            print(f"[ERROR] Invalid date format: {args.start_date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    print("="*80)
    print("PROCESSING ALL 2025 SOUND CAMPAIGNS (WITH CACHING)")
    print("="*80)
    
    csv_files = list(CLAUDE_SANDBOX.glob("2025 Sound Campaigns - *.csv"))
    
    # Exclude Chariot campaign (finished, no longer needed)
    csv_files = [f for f in csv_files if 'Chariot' not in f.name]
    
    if not csv_files:
        print(f"No campaign CSV files found in {CLAUDE_SANDBOX}")
        return
    
    print(f"\nFound {len(csv_files)} campaign CSV files (excluding Chariot)\n")
    
    results_summary = []
    all_campaign_results = []
    last_24h_cutoff = datetime.now() - timedelta(hours=24)
    
    for csv_path in sorted(csv_files):
        filename = csv_path.name
        try:
            print(f"Processing: {filename}")
        except UnicodeEncodeError:
            # Handle encoding errors for filenames with special characters
            safe_filename = filename.encode('ascii', 'ignore').decode('ascii')
            print(f"Processing: {safe_filename}")
        
        if "Attack Attack" in filename:
            csv_outputs = handle_attack_attack_csv(csv_path)
            for output_csv, start_date, account_count, campaign_name in csv_outputs:
                # Use override date if provided, otherwise require date from CSV
                if not override_start_date and not start_date:
                    print(f"  [WARNING] No start date found for {campaign_name}")
                    continue
                success, matched_count, content, output = run_scraper(output_csv, start_date or override_start_date, campaign_name, override_start_date)
                results_summary.append({
                    'campaign': campaign_name,
                    'matched': matched_count,
                    'success': success
                })
                if success and matched_count > 0:
                    recent_links, older_links = extract_links_from_content(content)
                    all_campaign_results.append({
                        'name': campaign_name,
                        'recent': recent_links,
                        'older': older_links,
                        'total': matched_count
                    })
        else:
            song_name, artist_name = extract_song_artist_from_filename(filename)
            
            if not song_name or not artist_name:
                print(f"  [WARNING] Could not extract song/artist from filename: {filename}")
                continue
            
            output_csv, start_date, account_count = convert_csv_to_scraper_format(
                csv_path, song_name, artist_name
            )
            
            # Use override date if provided, otherwise require date from CSV
            if not override_start_date and not start_date:
                print(f"  [WARNING] No start date found in {filename}")
                continue
            
            campaign_name = f"{song_name} - {artist_name}"
            safe_name = campaign_name.replace(' ', '_').replace(',', '').replace('/', '_')
            success, matched_count, content, output = run_scraper(output_csv, start_date or override_start_date, safe_name, override_start_date)
            
            results_summary.append({
                'campaign': campaign_name,
                'matched': matched_count,
                'success': success
            })
            
            if success and matched_count > 0:
                recent_links, older_links = extract_links_from_content(content)
                all_campaign_results.append({
                    'name': campaign_name,
                    'recent': recent_links,
                    'older': older_links,
                    'total': matched_count
                })
    
    # Create combined output file with 24-hour separation
    combined_file = OUTPUT_DIR / "all_campaigns_with_24h_separation.txt"
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("ALL 2025 SOUND CAMPAIGNS - WITH 24-HOUR SEPARATION\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Last 24 hours cutoff: {last_24h_cutoff.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total campaigns processed: {len(results_summary)}\n")
        f.write(f"Campaigns with matches: {len(all_campaign_results)}\n\n")
        f.write("="*80 + "\n\n")
        
        for result in all_campaign_results:
            f.write("\n" + "="*80 + "\n")
            f.write(f"SOUND: {result['name']}\n")
            f.write(f"Total Videos: {result['total']} ({len(result['recent'])} in last 24h, {len(result['older'])} older)\n")
            f.write("="*80 + "\n\n")
            
            if result['recent']:
                f.write(f"--- NEW IN LAST 24 HOURS ({len(result['recent'])} videos) ---\n\n")
                for link in result['recent']:
                    f.write(f"{link}\n")
                f.write("\n")
            
            if result['older']:
                f.write(f"--- OLDER VIDEOS ({len(result['older'])} videos) ---\n\n")
                for link in result['older']:
                    f.write(f"{link}\n")
                f.write("\n")
    
    # Print summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for result in results_summary:
        status = "[OK]" if result['success'] else "[FAIL]"
        print(f"{status} {result['campaign']}: {result['matched']} videos matched")
    
    print(f"\n\nResults saved to:")
    print(f"  Combined with 24h separation: {combined_file}")
    print(f"  Individual campaign files in: {OUTPUT_DIR}/")
    print("="*80)

if __name__ == '__main__':
    main()

