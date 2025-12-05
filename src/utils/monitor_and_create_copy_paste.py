#!/usr/bin/env python3
"""
Monitor robust scraper results and automatically create/update copy/paste file
Runs continuously and updates as campaigns complete
"""

import time
from pathlib import Path
from create_robust_copy_paste import create_copy_paste_from_robust_results

OUTPUT_DIR = Path("output")
CHECK_INTERVAL = 30  # Check every 30 seconds

def monitor_and_update():
    """Monitor for new robust results and update copy/paste file"""
    print("="*80)
    print("MONITORING ROBUST SCRAPER RESULTS")
    print("="*80)
    print("This script will automatically update the copy/paste file")
    print("as campaigns complete. Press Ctrl+C to stop monitoring.")
    print("="*80)
    print()
    
    last_file_count = 0
    
    try:
        while True:
            # Count current robust results files
            robust_files = list(OUTPUT_DIR.glob("*_robust_results.csv"))
            current_count = len(robust_files)
            
            if current_count > last_file_count:
                print(f"\n[{time.strftime('%H:%M:%S')}] New campaigns detected! ({current_count} total)")
                print("Updating copy/paste file...")
                create_copy_paste_from_robust_results()
                last_file_count = current_count
            elif current_count > 0:
                print(f"[{time.strftime('%H:%M:%S')}] Monitoring... ({current_count} campaigns completed)", end='\r')
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        print("Creating final copy/paste file...")
        create_copy_paste_from_robust_results()
        print("Done!")

if __name__ == '__main__':
    monitor_and_update()


