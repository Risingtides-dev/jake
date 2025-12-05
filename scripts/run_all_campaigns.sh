#!/bin/bash
#
# Run All Campaign Scrapes
# Warner, PLGRND, and In-House Network
# October 13 - November 13, 2025
#

set -e

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 RUNNING ALL CAMPAIGN SCRAPES"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Date Range: October 13 - November 13, 2025"
echo ""
echo "This will run three scrapes:"
echo "  1. Warner (5 accounts, 32 songs filtered)"
echo "  2. PLGRND (6 accounts, 11 songs filtered)"
echo "  3. In-House Network (22 active accounts, full catalog)"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Make scripts executable
chmod +x run_warner_scrape.sh
chmod +x run_plgrnd_scrape.sh
chmod +x run_inhouse_scrape.sh

# Run Warner
echo ""
echo "▶️  STEP 1/3: Warner Campaign"
echo "────────────────────────────────────────────────────────────────────────────────"
./run_warner_scrape.sh

# Run PLGRND
echo ""
echo "▶️  STEP 2/3: PLGRND Campaign"
echo "────────────────────────────────────────────────────────────────────────────────"
./run_plgrnd_scrape.sh

# Run In-House
echo ""
echo "▶️  STEP 3/3: In-House Network Campaign"
echo "────────────────────────────────────────────────────────────────────────────────"
./run_inhouse_scrape.sh

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ ALL CAMPAIGN SCRAPES COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Output files:"
echo "  📄 campaigns/warner/warner_oct13_nov13_2025.csv"
echo "  📄 campaigns/plgrnd/plgrnd_oct13_nov13_2025.csv"
echo "  📄 campaigns/inhouse/inhouse_oct13_nov13_2025.csv"
echo ""
echo "Ready for dashboard deliverables!"
echo ""
