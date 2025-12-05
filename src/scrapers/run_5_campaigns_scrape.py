#!/usr/bin/env python3
"""
Run scrape on 5 specific campaigns and create combined copy/paste output
with last 24 hours separated
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import csv
import time

OUTPUT_DIR = Path("output")

# Campaigns to scrape
CAMPAIGNS = [
    "The_Rose_Kingfishr_campaign.csv",
    "Simple_Things_Ne-Yo_campaign.csv",
    "Pretty_Little_Cameron_Whitcomb_campaign.csv",
    "Fade_Out_Kami_Kehoe_campaign.csv",
    "Wheres_Your_Head_At_Eurotripp_campaign.csv"
]

def run_scrape(campaign_csv, start_date=None):
    """Run scraper on a campaign CSV"""
    print(f"\n{'='*80}")
    print(f"Scraping: {campaign_csv}")
    print(f"{'='*80}\n")
    
    cmd = [sys.executable, "scrape_external_accounts_cached.py", str(OUTPUT_DIR / campaign_csv)]
    
    if start_date:
        cmd.extend(["--start-date", start_date])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ Completed: {campaign_csv}\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error scraping {campaign_csv}: {e}\n")
        return False

def create_combined_copy_paste():
    """Create combined copy/paste file from all 5 campaigns with 24-hour separation"""
    
    # Map campaign CSVs to their result files (try both naming conventions)
    campaign_map = {
        "The_Rose_Kingfishr_campaign.csv": ["The_Rose_Kingfishr_results.txt", "The_Rose_-_Kingfishr_results.txt"],
        "Simple_Things_Ne-Yo_campaign.csv": ["Simple_Things_Ne-Yo_results.txt", "Simple_Things_-_Ne-Yo_results.txt"],
        "Pretty_Little_Cameron_Whitcomb_campaign.csv": ["Pretty_Little_Cameron_Whitcomb_results.txt", "Pretty_Little_-_Cameron_Whitcomb_results.txt"],
        "Fade_Out_Kami_Kehoe_campaign.csv": ["Fade_Out_Kami_Kehoe_results.txt", "Fade_Out_-_Kami_Kehoe_results.txt"],
        "Wheres_Your_Head_At_Eurotripp_campaign.csv": ["Wheres_Your_Head_At_Eurotripp_results.txt", "Wheres_Your_Head_At_-_Eurotripp_results.txt"]
    }
    
    all_recent_links = []
    all_older_links = []
    campaign_stats = {}
    
    print(f"\n{'='*80}")
    print("Gathering results from all campaigns...")
    print(f"{'='*80}\n")
    
    import re
    
    # Calculate 24-hour cutoff
    now = datetime.now()
    last_24h_cutoff = now - timedelta(hours=24)
    
    for campaign_csv, results_files in campaign_map.items():
        # Try to find the results file (check both naming conventions)
        results_path = None
        for results_file in results_files:
            test_path = OUTPUT_DIR / results_file
            if test_path.exists():
                results_path = test_path
                break
        
        campaign_name = campaign_csv.replace("_campaign.csv", "").replace("_", " ")
        
        if not results_path:
            print(f"⚠ Results file not found for: {campaign_csv}")
            continue
        
        try:
            recent_links = []
            older_links = []
            
            # Read the results file
            with open(results_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find the sections
            in_recent_section = False
            in_older_section = False
            
            for line in lines:
                # Check for section headers
                if "NEW IN LAST 24 HOURS" in line.upper() or "--- NEW IN LAST 24 HOURS" in line:
                    in_recent_section = True
                    in_older_section = False
                    continue
                elif "OLDER VIDEOS" in line.upper() or "--- OLDER VIDEOS" in line:
                    in_recent_section = False
                    in_older_section = True
                    continue
                elif "SONG:" in line or "ARTIST:" in line or "="*80 in line or line.strip() == "":
                    # Skip headers and separators
                    continue
                
                # Extract video URLs
                url_match = re.search(r'https://www\.tiktok\.com/@[\w\.]+/video/\d+', line)
                if url_match:
                    url = url_match.group(0)
                    if in_recent_section:
                        recent_links.append(url)
                        all_recent_links.append(url)
                    elif in_older_section:
                        older_links.append(url)
                        all_older_links.append(url)
            
            campaign_stats[campaign_name] = {
                'recent': len(recent_links),
                'older': len(older_links),
                'total': len(recent_links) + len(older_links)
            }
            
            print(f"{campaign_name}: {campaign_stats[campaign_name]['total']} videos ({campaign_stats[campaign_name]['recent']} in last 24h)")
        
        except Exception as e:
            print(f"Error reading {results_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Create combined copy/paste file
    output_file = OUTPUT_DIR / "5_campaigns_combined_copy_paste.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("5 CAMPAIGNS - COMBINED COPY/PASTE\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Last 24 hours cutoff: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Campaigns: {len(CAMPAIGNS)}\n\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-"*80 + "\n")
        total_recent = sum(s['recent'] for s in campaign_stats.values())
        total_older = sum(s['older'] for s in campaign_stats.values())
        f.write(f"Total Videos (Last 24h): {total_recent}\n")
        f.write(f"Total Videos (Older): {total_older}\n")
        f.write(f"Grand Total: {total_recent + total_older}\n\n")
        
        for campaign, stats in campaign_stats.items():
            f.write(f"{campaign}: {stats['total']} videos ({stats['recent']} recent, {stats['older']} older)\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("NEW IN LAST 24 HOURS\n")
        f.write("="*80 + "\n\n")
        
        if all_recent_links:
            for link in all_recent_links:
                f.write(link + "\n")
        else:
            f.write("No videos found in the last 24 hours.\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("OLDER VIDEOS\n")
        f.write("="*80 + "\n\n")
        
        if all_older_links:
            for link in all_older_links:
                f.write(link + "\n")
        else:
            f.write("No older videos found.\n")
    
    print(f"\n{'='*80}")
    print(f"✓ Combined copy/paste file created: {output_file}")
    print(f"{'='*80}\n")
    
    return output_file

def main():
    print("="*80)
    print("5 CAMPAIGNS SCRAPE")
    print("="*80)
    print("\nCampaigns to scrape:")
    for i, campaign in enumerate(CAMPAIGNS, 1):
        print(f"  {i}. {campaign}")
    
    # Get start date for Where's Your Head At (12/01/25 = 2025-12-01)
    start_dates = {
        "Wheres_Your_Head_At_Eurotripp_campaign.csv": "2025-12-01"
    }
    
    # Run scrapes
    print("\nStarting scrapes...\n")
    for campaign in CAMPAIGNS:
        start_date = start_dates.get(campaign)
        run_scrape(campaign, start_date)
        time.sleep(2)  # Small delay between campaigns
    
    # Create combined copy/paste
    create_combined_copy_paste()
    
    print("="*80)
    print("ALL DONE!")
    print("="*80)

if __name__ == "__main__":
    main()

