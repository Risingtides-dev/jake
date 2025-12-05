#!/usr/bin/env python3
"""
Create copy/paste file from all robust scraper results
Extracts all video URLs from completed campaigns
Separates videos by last 24 hours
"""

from pathlib import Path
import csv
from datetime import datetime, timedelta

OUTPUT_DIR = Path("output")

def parse_timestamp(timestamp_str):
    """Parse timestamp from various formats"""
    if not timestamp_str:
        return None
    
    # Try different timestamp formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%m/%d/%Y %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str.strip(), fmt)
        except:
            continue
    
    return None

def create_copy_paste_from_robust_results():
    """Create copy/paste file from all robust results CSVs"""
    
    # Find all robust results files
    robust_files = list(OUTPUT_DIR.glob("*_robust_results.csv"))
    
    if not robust_files:
        print("No robust results files found yet. Waiting for campaigns to complete...")
        return
    
    print(f"Found {len(robust_files)} robust results files")
    print("="*80)
    
    # Calculate 24-hour cutoff
    now = datetime.now()
    last_24h_cutoff = now - timedelta(hours=24)
    
    all_links = []
    all_recent_links = []
    campaign_stats = {}
    
    # Process each results file
    for results_file in sorted(robust_files):
        campaign_name = results_file.stem.replace('_robust_results', '').replace('_', ' - ')
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                links = []
                recent_links = []
                
                for row in reader:
                    url = row.get('url', '').strip()
                    if url:
                        links.append(url)
                        all_links.append(url)
                        
                        # Check if video is from last 24 hours
                        timestamp_str = row.get('timestamp', '').strip()
                        if timestamp_str:
                            video_timestamp = parse_timestamp(timestamp_str)
                            if video_timestamp and video_timestamp >= last_24h_cutoff:
                                recent_links.append(url)
                                all_recent_links.append(url)
                
                campaign_stats[campaign_name] = {
                    'total': len(links),
                    'recent': len(recent_links),
                    'older': len(links) - len(recent_links)
                }
                print(f"{campaign_name}: {len(links)} videos ({len(recent_links)} in last 24h)")
        
        except Exception as e:
            print(f"Error reading {results_file.name}: {e}")
            continue
    
    # Create copy/paste file
    copy_paste_file = OUTPUT_DIR / "all_robust_campaigns_copy_paste.txt"
    
    with open(copy_paste_file, 'w', encoding='utf-8') as f:
        f.write("ALL 2025 CAMPAIGNS - ROBUST SCRAPER RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Last 24 hours cutoff: {last_24h_cutoff.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Campaigns: {len(robust_files)}\n")
        f.write(f"Total Videos: {len(all_links)} ({len(all_recent_links)} in last 24h, {len(all_links) - len(all_recent_links)} older)\n")
        f.write("="*80 + "\n\n")
        
        # Group by campaign
        for results_file in sorted(robust_files):
            campaign_name = results_file.stem.replace('_robust_results', '').replace('_', ' - ')
            stats = campaign_stats.get(campaign_name, {'total': 0, 'recent': 0, 'older': 0})
            
            f.write(f"\n{'='*80}\n")
            f.write(f"CAMPAIGN: {campaign_name}\n")
            f.write(f"Videos: {stats['total']} ({stats['recent']} in last 24h, {stats['older']} older)\n")
            f.write(f"{'='*80}\n\n")
            
            try:
                with open(results_file, 'r', encoding='utf-8') as csv_file:
                    reader = csv.DictReader(csv_file)
                    
                    recent_videos = []
                    older_videos = []
                    
                    for row in reader:
                        url = row.get('url', '').strip()
                        if not url:
                            continue
                        
                        timestamp_str = row.get('timestamp', '').strip()
                        video_timestamp = parse_timestamp(timestamp_str) if timestamp_str else None
                        
                        if video_timestamp and video_timestamp >= last_24h_cutoff:
                            recent_videos.append((url, video_timestamp))
                        else:
                            older_videos.append(url)
                    
                    # Write recent videos first
                    if recent_videos:
                        f.write(f"--- NEW IN LAST 24 HOURS ({len(recent_videos)} videos) ---\n\n")
                        # Sort by timestamp (newest first)
                        recent_videos.sort(key=lambda x: x[1], reverse=True)
                        for url, _ in recent_videos:
                            f.write(f"{url}\n")
                        f.write("\n")
                    
                    # Then older videos
                    if older_videos:
                        f.write(f"--- OLDER VIDEOS ({len(older_videos)} videos) ---\n\n")
                        for url in older_videos:
                            f.write(f"{url}\n")
                        f.write("\n")
                    
            except Exception as e:
                f.write(f"[Error reading campaign file: {e}]\n\n")
        
        # Add summary at the end
        f.write("\n" + "="*80 + "\n")
        f.write("SUMMARY BY CAMPAIGN\n")
        f.write("="*80 + "\n")
        for campaign, stats in sorted(campaign_stats.items()):
            f.write(f"{campaign}: {stats['total']} videos ({stats['recent']} in last 24h, {stats['older']} older)\n")
    
    print("\n" + "="*80)
    print("[SUCCESS] Copy/paste file created!")
    print(f"File: {copy_paste_file}")
    print(f"Total videos: {len(all_links)} ({len(all_recent_links)} in last 24h)")
    print(f"Total campaigns: {len(robust_files)}")
    print("="*80)
    
    return copy_paste_file

if __name__ == '__main__':
    create_copy_paste_from_robust_results()

