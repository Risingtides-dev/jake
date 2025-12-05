#!/bin/bash
#
# PLGRND Campaign Scrape
# October 13 - November 13, 2025
#

set -e

echo ""
echo "🎯 PLGRND Campaign Scrape"
echo "========================="
echo "Date Range: October 13 - November 13, 2025"
echo "Accounts: 6 PLGRND accounts"
echo "Songs: 11 PLGRND songs (filtered mode)"
echo ""

cd campaigns/plgrnd

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
    --output plgrnd_oct13_nov13_2025

echo ""
echo "✅ PLGRND scrape complete!"
echo "Output: campaigns/plgrnd/plgrnd_oct13_nov13_2025.csv"
echo ""
