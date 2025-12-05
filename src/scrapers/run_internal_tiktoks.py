#!/usr/bin/env python3
"""
Run internal TikTok accounts scrape for the last 24 hours.
This is the main entry point for daily internal account tracking.
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description='Run internal TikTok accounts scrape',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: last 36 hours
  python run_internal_tiktoks.py
  
  # Custom date range
  python run_internal_tiktoks.py --start-datetime "2024-11-26 05:00" --end-datetime "2024-11-27 12:00"
  
  # From specific date/time to now
  python run_internal_tiktoks.py --start-datetime "2024-11-26 05:00"
        """
    )
    parser.add_argument('--start-datetime', 
                       help='Start datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS). Default: 36 hours ago')
    parser.add_argument('--end-datetime',
                       help='End datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS). Default: now')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("RUNNING INTERNAL TIKTOKS DAILY REPORT")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / 'get_post_links_by_song.py'
    
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)
    
    try:
        # Build command with optional datetime arguments
        cmd = [sys.executable, str(script_path)]
        if args.start_datetime:
            cmd.extend(['--start-datetime', args.start_datetime])
        if args.end_datetime:
            cmd.extend(['--end-datetime', args.end_datetime])
        
        # Call the main scraping script
        result = subprocess.run(
            cmd,
            capture_output=False, # Let the child script print to console
            text=True,
            check=True # Raise an exception for non-zero exit codes
        )
        print("\n" + "=" * 80)
        print("Daily report completed successfully!")
        print("=" * 80)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Daily report failed: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[ERROR] Script not found: {script_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

