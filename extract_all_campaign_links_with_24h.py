#!/usr/bin/env python3
"""Extract all links from individual campaign result files and combine with 24-hour separation"""

from pathlib import Path
import re
from datetime import datetime, timedelta

OUTPUT_DIR = Path("output")

def extract_links_from_detailed_file(file_path):
    """Extract post links from a detailed result file, separating recent and older"""
    if not file_path.exists():
        return [], []
    
    recent_links = []
    older_links = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        in_recent_section = False
        in_older_section = False
        
        for line in lines:
            stripped = line.strip()
            if '--- NEW IN LAST 24 HOURS' in stripped:
                in_recent_section = True
                in_older_section = False
                continue
            elif '--- OLDER VIDEOS' in stripped:
                in_recent_section = False
                in_older_section = True
                continue
            elif 'http' in stripped and 'tiktok.com' in stripped:
                # Extract URL from line (may have leading spaces and numbers)
                url_match = re.search(r'https://www\.tiktok\.com/[^\s]+', stripped)
                if url_match:
                    url = url_match.group(0)
                    if in_recent_section:
                        recent_links.append(url)
                    elif in_older_section:
                        older_links.append(url)
            elif stripped and 'SONG:' in stripped and not in_recent_section and not in_older_section:
                # Reset sections if we hit a new song section (but only if we're not already in a section)
                pass
    
    return recent_links, older_links

def get_campaign_name_from_file(file_path):
    """Extract campaign name from filename"""
    name = file_path.stem.replace('_results', '').replace('_', ' ')
    # Clean up common patterns
    name = name.replace('ONE HIT WONDER', 'ONE HIT WONDER')
    return name

def main():
    # Find all result files
    result_files = sorted(OUTPUT_DIR.glob("*_results.txt"))
    
    # Filter out combined files
    result_files = [f for f in result_files if 'all_campaigns' not in f.name and 'external_accounts_by_song' not in f.name]
    
    combined_file = OUTPUT_DIR / "all_campaigns_with_24h_separation.txt"
    last_24h_cutoff = datetime.now() - timedelta(hours=24)
    
    all_campaigns = []
    
    for result_file in result_files:
        recent_links, older_links = extract_links_from_detailed_file(result_file)
        if recent_links or older_links:
            campaign_name = get_campaign_name_from_file(result_file)
            all_campaigns.append({
                'name': campaign_name,
                'recent': recent_links,
                'older': older_links,
                'total': len(recent_links) + len(older_links)
            })
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("ALL 2025 SOUND CAMPAIGNS - WITH 24-HOUR SEPARATION\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Last 24 hours cutoff: {last_24h_cutoff.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total campaigns: {len(all_campaigns)}\n\n")
        f.write("="*80 + "\n\n")
        
        for campaign in all_campaigns:
            f.write("\n" + "="*80 + "\n")
            f.write(f"SOUND: {campaign['name']}\n")
            f.write(f"Total Videos: {campaign['total']} ({len(campaign['recent'])} in last 24h, {len(campaign['older'])} older)\n")
            f.write("="*80 + "\n\n")
            
            if campaign['recent']:
                f.write(f"--- NEW IN LAST 24 HOURS ({len(campaign['recent'])} videos) ---\n\n")
                for link in campaign['recent']:
                    f.write(f"{link}\n")
                f.write("\n")
            
            if campaign['older']:
                f.write(f"--- OLDER VIDEOS ({len(campaign['older'])} videos) ---\n\n")
                for link in campaign['older']:
                    f.write(f"{link}\n")
                f.write("\n")
    
    print(f"Combined links saved to: {combined_file}")
    print(f"Processed {len(all_campaigns)} campaigns with links")
    total_recent = sum(len(c['recent']) for c in all_campaigns)
    total_older = sum(len(c['older']) for c in all_campaigns)
    print(f"Total: {total_recent + total_older} videos ({total_recent} in last 24h, {total_older} older)")

if __name__ == '__main__':
    main()

