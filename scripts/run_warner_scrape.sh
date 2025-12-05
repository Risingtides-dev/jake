#!/bin/bash
#
# Warner Campaign Scrape
# October 13 - November 13, 2025
#

set -e

echo ""
echo "🎯 WARNER Campaign Scrape"
echo "=========================="
echo "Date Range: October 13 - November 13, 2025"
echo "Accounts: 5 Warner accounts"
echo "Songs: 32 Warner songs (filtered mode)"
echo ""

cd campaigns/warner

# Activate venv if exists
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
fi

# Run the scraper
python3 ../../unified_scraper.py \
    --accounts accounts.csv \
    --songs songs.csv \
    --start-date 2025-10-13 \
    --limit 500 \
    --output warner_oct13_nov13_2025

echo ""
echo "✅ Warner scrape complete!"
echo "Output: campaigns/warner/warner_oct13_nov13_2025.csv"
echo ""
