#!/usr/bin/env python3
"""
Utility script to extract TikTok account handles from CSV files
Reads account login CSV files and extracts account handles for use in config.py
"""

import csv
import re
import sys
from pathlib import Path

def extract_account_from_url(url):
    """Extract @handle from TikTok URL"""
    if not url:
        return None
    # Match @username pattern in URL
    match = re.search(r'@([\w\.]+)', url)
    if match:
        return f"@{match.group(1)}"
    return None

def extract_accounts_from_csv(csv_file):
    """Extract account handles from a CSV file"""
    accounts = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Look for columns that might contain account URLs or handles
            for row in reader:
                for key, value in row.items():
                    if value and ('tiktok.com' in value.lower() or key.lower() in ['account handle', 'handle', 'url', 'account']):
                        account = extract_account_from_url(value)
                        if account:
                            accounts.add(account)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
    
    return accounts

def main():
    # Look for account login CSV files in the data directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'Private & Shared 4'
    
    # Fallback to Private & Shared 4 in current directory if data dir doesn't exist
    if not data_dir.exists():
        data_dir = project_root / 'Private & Shared 4'
    
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        print("Please ensure CSV files are in the correct location.")
        return
    
    all_accounts = set()
    
    # Find all CSV files
    csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s)")
    print("=" * 60)
    
    for csv_file in csv_files:
        if 'Account Logins' in csv_file.name or 'account' in csv_file.name.lower():
            print(f"\nProcessing: {csv_file.name}")
            accounts = extract_accounts_from_csv(csv_file)
            if accounts:
                print(f"  Found {len(accounts)} account(s):")
                for acc in sorted(accounts):
                    print(f"    - {acc}")
                all_accounts.update(accounts)
            else:
                print(f"  No accounts found")
    
    if all_accounts:
        print("\n" + "=" * 60)
        print(f"\nTotal unique accounts found: {len(all_accounts)}")
        print("\nAccounts list for config.py:")
        print("ACCOUNTS = [")
        for acc in sorted(all_accounts):
            print(f"    '{acc}',")
        print("]")
    else:
        print("\nNo accounts found in CSV files.")

if __name__ == '__main__':
    main()

