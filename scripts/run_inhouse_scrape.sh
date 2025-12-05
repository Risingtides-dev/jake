#!/bin/bash
#
# In-House Network Campaign Scrape
# October 13 - November 13, 2025
#

set -e

echo ""
echo "🎯 IN-HOUSE NETWORK Campaign Scrape"
echo "===================================="
echo "Date Range: October 13 - November 13, 2025"
echo "Accounts: 22 active in-house accounts"
echo "Mode: FULL CATALOG (no song filtering)"
echo ""

cd campaigns/inhouse

# Use the active accounts only
if [ -f "accounts_active_only.csv" ]; then
    cp accounts_active_only.csv accounts_scrape.csv
    echo "Using active accounts only (22 accounts)"
else
    echo "Warning: Using all accounts from accounts.csv"
fi

# Activate venv if exists
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
fi

# Run the scraper (NO --songs flag = full catalog mode)
python3 ../../unified_scraper.py \
    --accounts accounts_scrape.csv \
    --start-date 2025-10-13 \
    --limit 500 \
    --output inhouse_oct13_nov13_2025

echo ""
echo "✅ In-House scrape complete!"
echo "Output: campaigns/inhouse/inhouse_oct13_nov13_2025.csv"
echo ""
