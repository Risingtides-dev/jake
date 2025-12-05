#!/usr/bin/env python3
"""
Run all external TikTok campaigns with caching and 24-hour separation.
This is the main entry point for daily external account tracking.
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(
        description='Run all external TikTok campaigns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use start dates from CSV files
  python run_external_tiktoks.py
  
  # Override start date for all campaigns
  python run_external_tiktoks.py --start-date "2025-11-26"
        """
    )
    parser.add_argument('--start-date', 
                       help='Override start date for all campaigns (YYYY-MM-DD). If not provided, uses dates from CSV files.')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("RUNNING EXTERNAL TIKTOKS - ALL 2025 SOUND CAMPAIGNS")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / 'run_all_campaigns_cached.py'
    
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)
    
    try:
        # Build command with optional start date
        cmd = [sys.executable, str(script_path)]
        if args.start_date:
            cmd.extend(['--start-date', args.start_date])
        
        # Run the cached campaigns scraper
        result = subprocess.run(
            cmd,
            capture_output=False,  # Let the child script print to console
            text=True,
            check=True  # Raise an exception for non-zero exit codes
        )
        
        print("\n" + "=" * 80)
        print("External campaigns completed successfully!")
        print("=" * 80)
        print("\nResults saved to: output/all_campaigns_with_24h_separation.txt")
        print("=" * 80)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] External campaigns failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n[ERROR] Script not found: {script_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

