#!/usr/bin/env python3
"""
Run all Warner campaigns and show statistics
"""

import subprocess
import sys
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

OUTPUT_DIR = Path("output")

def get_all_campaign_csvs():
    """Get all campaign CSV files from output directory"""
    campaign_files = list(OUTPUT_DIR.glob("*_campaign.csv"))
    # Filter out duplicates and special cases
    campaigns = {}
    for csv_file in campaign_files:
        # Skip R3 and other variants, use base name
        name = csv_file.stem.replace("_campaign", "")
        if "R3" not in name and "ONE_HIT_WONDER" not in name:
            campaigns[name] = csv_file
    return campaigns

def run_campaign_scrape(csv_file, start_date):
    """Run scraper on a campaign CSV"""
    print(f"\n{'='*80}")
    print(f"Scraping: {csv_file.name}")
    print(f"{'='*80}\n")
    
    cmd = [sys.executable, "scrape_external_accounts_cached.py", str(csv_file), "--start-date", start_date]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            # Extract stats from output
            output = result.stdout
            matched_match = None
            for line in output.split('\n'):
                if 'Matched' in line and 'videos' in line:
                    matched_match = line
                    break
            
            return True, output, matched_match
        else:
            return False, result.stderr, None
    except subprocess.TimeoutExpired:
        return False, "Timeout after 1 hour", None
    except Exception as e:
        return False, str(e), None

def get_stats_from_results():
    """Get stats from existing results files"""
    stats = []
    
    # Find all results files
    results_files = list(OUTPUT_DIR.glob("*_results.txt"))
    
    for results_file in results_files:
        campaign_name = results_file.stem.replace("_results", "").replace("_", " ")
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract stats
                total_uses_match = None
                total_views_match = None
                total_likes_match = None
                
                for line in content.split('\n'):
                    if 'Total Uses:' in line:
                        total_uses_match = line
                    elif 'Total Views:' in line:
                        total_views_match = line
                    elif 'Total Likes:' in line:
                        total_likes_match = line
                
                # Parse numbers
                total_uses = 0
                total_views = 0
                total_likes = 0
                
                if total_uses_match:
                    try:
                        total_uses = int(total_uses_match.split('Total Uses:')[1].split()[0])
                    except:
                        pass
                
                if total_views_match:
                    try:
                        views_str = total_views_match.split('Total Views:')[1].strip().replace(',', '')
                        total_views = int(views_str)
                    except:
                        pass
                
                if total_likes_match:
                    try:
                        likes_str = total_likes_match.split('Total Likes:')[1].strip().replace(',', '')
                        total_likes = int(likes_str)
                    except:
                        pass
                
                if total_uses > 0:
                    stats.append({
                        'campaign': campaign_name,
                        'videos': total_uses,
                        'views': total_views,
                        'likes': total_likes
                    })
        except Exception as e:
            continue
    
    return stats

def main():
    start_date = "2025-11-15"
    
    print("="*80)
    print("WARNER CAMPAIGNS - FULL SCRAPE WITH STATS")
    print("="*80)
    print(f"Start Date: {start_date}")
    print()
    
    campaigns = get_all_campaign_csvs()
    print(f"Found {len(campaigns)} campaigns to scrape\n")
    
    results = []
    
    for name, csv_file in sorted(campaigns.items()):
        print(f"Processing: {csv_file.name}")
        success, output, matched_info = run_campaign_scrape(csv_file, start_date)
        
        if success:
            # Try to extract stats from output
            videos = 0
            views = 0
            likes = 0
            
            # Look for stats in output
            for line in output.split('\n'):
                if 'Total Uses:' in line:
                    try:
                        videos = int(line.split('Total Uses:')[1].split()[0])
                    except:
                        pass
                elif 'Total Views:' in line:
                    try:
                        views_str = line.split('Total Views:')[1].strip().replace(',', '')
                        views = int(views_str)
                    except:
                        pass
                elif 'Total Likes:' in line:
                    try:
                        likes_str = line.split('Total Likes:')[1].strip().replace(',', '')
                        likes = int(likes_str)
                    except:
                        pass
            
            results.append({
                'campaign': name.replace('_', ' '),
                'videos': videos,
                'views': views,
                'likes': likes,
                'success': True
            })
            print(f"  ✓ Success: {videos} videos, {views:,} views, {likes:,} likes")
        else:
            results.append({
                'campaign': name.replace('_', ' '),
                'videos': 0,
                'views': 0,
                'likes': 0,
                'success': False
            })
            print(f"  ✗ Failed: {output[:100]}")
    
    # Print summary stats
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print()
    
    total_videos = sum(r['videos'] for r in results)
    total_views = sum(r['views'] for r in results)
    total_likes = sum(r['likes'] for r in results)
    successful = sum(1 for r in results if r['success'])
    
    print(f"Total Campaigns: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print()
    print(f"Total Videos: {total_videos:,}")
    print(f"Total Views: {total_views:,}")
    print(f"Total Likes: {total_likes:,}")
    if total_videos > 0:
        print(f"Average Views per Video: {total_views // total_videos:,}")
        print(f"Average Likes per Video: {total_likes // total_videos:,}")
    print()
    
    # Top campaigns by videos
    print("Top 10 Campaigns by Video Count:")
    sorted_by_videos = sorted(results, key=lambda x: x['videos'], reverse=True)
    for i, r in enumerate(sorted_by_videos[:10], 1):
        status = "✓" if r['success'] else "✗"
        print(f"  {i}. {status} {r['campaign']}: {r['videos']} videos ({r['views']:,} views)")
    
    print()
    
    # Top campaigns by views
    print("Top 10 Campaigns by Total Views:")
    sorted_by_views = sorted(results, key=lambda x: x['views'], reverse=True)
    for i, r in enumerate(sorted_by_views[:10], 1):
        status = "✓" if r['success'] else "✗"
        print(f"  {i}. {status} {r['campaign']}: {r['views']:,} views ({r['videos']} videos)")
    
    print()
    print("="*80)

if __name__ == "__main__":
    main()


