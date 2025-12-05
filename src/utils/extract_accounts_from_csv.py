#!/usr/bin/env python3
"""
Utility script to extract TikTok account handles from CSV files
This helps populate the config.py file with accounts from the account logins CSV
"""

import csv
import re
from pathlib import Path

def extract_account_handle(url_or_handle):
    """Extract @username from URL or handle string"""
    if not url_or_handle:
        return None
    
    # If it's already a handle like @username
    if url_or_handle.startswith('@'):
        return url_or_handle
    
    # Extract from URL like https://www.tiktok.com/@username
    match = re.search(r'@([\w\.]+)', url_or_handle)
    if match:
        return f"@{match.group(1)}"
    
    return None

def extract_accounts_from_csv(csv_file):
    """Extract all unique account handles from CSV file"""
    accounts = set()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Try to detect the column name (might have BOM)
            reader = csv.DictReader(f)
            
            # Look for account handle column (could be 'account Handle', 'URL', etc.)
            for row in reader:
                # Check multiple possible column names
                for col_name in ['account Handle', 'URL', 'TikTok Handle', 'Handle']:
                    if col_name in row and row[col_name]:
                        handle = extract_account_handle(row[col_name])
                        if handle:
                            accounts.add(handle)
                
                # Also check all columns for @ patterns
                for col_name, value in row.items():
                    if value and '@' in value:
                        handle = extract_account_handle(value)
                        if handle:
                            accounts.add(handle)
    
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
    
    return sorted(list(accounts))

def main():
    """Extract accounts from account logins CSV files"""
    data_dir = Path(__file__).parent / 'data' / 'Private & Shared 4'
    
    # Find account login CSV files
    account_csv_files = list(data_dir.glob('*Account Logins*.csv'))
    
    if not account_csv_files:
        print("No account login CSV files found in data/Private & Shared 4/")
        return
    
    all_accounts = set()
    
    for csv_file in account_csv_files:
        print(f"Processing: {csv_file.name}")
        accounts = extract_accounts_from_csv(csv_file)
        all_accounts.update(accounts)
        print(f"  Found {len(accounts)} accounts")
    
    # Sort and display
    all_accounts = sorted(list(all_accounts))
    
    print(f"\n{'='*60}")
    print(f"Total unique accounts found: {len(all_accounts)}")
    print(f"{'='*60}\n")
    
    # Print accounts in Python list format
    print("Accounts (Python list format):")
    print("ACCOUNTS = [")
    for account in all_accounts:
        print(f"    '{account}',")
    print("]")
    
    print(f"\n{'='*60}")
    print("Copy the above list into config.py ACCOUNTS variable")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

