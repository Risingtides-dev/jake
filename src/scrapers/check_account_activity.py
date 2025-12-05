#!/usr/bin/env python3
"""
Quick script to check which TikTok accounts have posted within the last 7 days.
Uses yt-dlp to fetch just the first video timestamp from each account.
Much faster than a full scrape - only checks the most recent post.
"""

import subprocess
import json
import csv
from datetime import datetime, timedelta

def check_account_activity(account_username):
    """
    Check if account has posted in the last 7 days using yt-dlp.
    Returns: (account, is_active, last_post_date, error)
    """
    url = f"https://www.tiktok.com/@{account_username}"

    try:
        # Use yt-dlp to get just the first video metadata
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--dump-json',
            '--playlist-end', '1',  # Only get the first video
            '--no-warnings',
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0 or not result.stdout.strip():
            return (account_username, False, None, "No videos found or account unavailable")

        # Parse the JSON output
        video_data = json.loads(result.stdout.strip())

        # Get upload date (format: YYYYMMDD)
        upload_date_str = video_data.get('upload_date')
        if not upload_date_str:
            return (account_username, False, None, "Could not extract upload date")

        # Parse the date
        upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
        days_ago = (datetime.now() - upload_date).days

        is_active = days_ago <= 7

        return (account_username, is_active, upload_date.strftime('%Y-%m-%d'), None)

    except subprocess.TimeoutExpired:
        return (account_username, False, None, "Timeout - account check took too long")
    except json.JSONDecodeError:
        return (account_username, False, None, "Could not parse video data")
    except Exception as e:
        return (account_username, False, None, str(e))

def main():
    # Read in-house accounts
    inhouse_accounts = [
        'backroaddriver', 'blakewhitencore', 'boone.reynolds', 'brew.pilled',
        'buck.wilders', 'cash.culpepper', 'clevis.the.cowboy', 'coffee.healing.peace',
        'coffee.yearnings', 'coffeelover_127', 'coffeequotesforeveryone', 'coffeesentimental',
        'country_lifelover124', 'dallasramsey5.3', 'dearest.arthur', 'dieselmechanic4life',
        'dirtroad.drivin', 'earl.boone1', 'ericcromartie', 'ghostofarthurmorgan',
        'gusjohnson_quotes', 'hookedupfishing61', 'humans.are.awesom4', 'pinkfonthalfspeed',
        'quinnbmovin', 'ricos.revenge', 'sipsofsentiment', 'sopranosyndrome', 'southpawoutlaw1',
        'spaceboylonerism', 'trailheadtravis', 'v8s.and.heartbreaks', 'yellowfont.halfspeed'
    ]

    print(f"\n{'='*80}")
    print(f"Checking {len(inhouse_accounts)} In-House Network accounts for activity...")
    print(f"Looking for posts within the last 7 days")
    print(f"{'='*80}\n")

    results = []
    for i, account in enumerate(inhouse_accounts, 1):
        print(f"[{i}/{len(inhouse_accounts)}] Checking @{account}...", end=' ', flush=True)
        result = check_account_activity(account)
        results.append(result)

        # Print result
        status = "✓ ACTIVE" if result[1] else "✗ INACTIVE"
        date_info = f"(last post: {result[2]})" if result[2] else f"({result[3]})"
        print(f"{status} {date_info}")

    # Separate active and inactive
    active_accounts = [r for r in results if r[1]]
    inactive_accounts = [r for r in results if not r[1]]

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Active accounts (posted in last 7 days): {len(active_accounts)}")
    print(f"Inactive accounts: {len(inactive_accounts)}")

    # Save results to CSV
    output_file = 'campaigns/inhouse/account_activity_check.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Account', 'Active', 'Last Post Date', 'Error/Note'])
        for result in results:
            writer.writerow([
                result[0],
                'Yes' if result[1] else 'No',
                result[2] if result[2] else 'N/A',
                result[3] if result[3] else ''
            ])

    print(f"\nFull results saved to: {output_file}")

    # Save filtered active accounts list
    active_output = 'campaigns/inhouse/accounts_active_only.csv'
    with open(active_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Account'])
        for result in active_accounts:
            writer.writerow([result[0]])

    print(f"Active accounts list saved to: {active_output}")
    print(f"\n{len(active_accounts)} active accounts ready for scraping!\n")

if __name__ == "__main__":
    main()
