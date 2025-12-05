#!/bin/bash
#
# Full Catalog Runner - For extracting ALL songs from in-house accounts
# Usage: ./run_full_catalog.sh <campaign_folder> [options]
#
# Example: ./run_full_catalog.sh campaigns/plgrnd --start-date 2025-11-01 --limit 1000
#

set -e

# Check if campaign folder provided
if [ -z "$1" ]; then
    echo "Usage: ./run_full_catalog.sh <campaign_folder> [options]"
    echo ""
    echo "Example:"
    echo "  ./run_full_catalog.sh campaigns/plgrnd"
    echo "  ./run_full_catalog.sh campaigns/inhouse --start-date 2025-11-01 --limit 1000"
    echo ""
    echo "Campaign folder should contain:"
    echo "  - accounts.csv (with columns: URL or account Handle or Account)"
    echo ""
    echo "Note: This mode extracts ALL songs used, no filtering"
    exit 1
fi

CAMPAIGN_DIR="$1"
shift  # Remove campaign dir from args, keep remaining options

# Check if campaign directory exists
if [ ! -d "$CAMPAIGN_DIR" ]; then
    echo "Error: Campaign directory '$CAMPAIGN_DIR' does not exist"
    exit 1
fi

# Find accounts.csv
ACCOUNTS_CSV=$(find "$CAMPAIGN_DIR" -maxdepth 1 -name "*accounts*.csv" -o -name "*Accounts*.csv" -o -name "*ACCOUNTS*.csv" | head -n 1)
if [ -z "$ACCOUNTS_CSV" ]; then
    echo "Error: No accounts CSV found in $CAMPAIGN_DIR"
    echo "Please add a file named 'accounts.csv' or similar"
    exit 1
fi

# Create output directory
OUTPUT_DIR="$CAMPAIGN_DIR/output"
mkdir -p "$OUTPUT_DIR"

# Get campaign name from folder
CAMPAIGN_NAME=$(basename "$CAMPAIGN_DIR")

# Output filename
OUTPUT_PREFIX="$OUTPUT_DIR/${CAMPAIGN_NAME}_full_catalog"

echo "================================================================================================"
echo "FULL CATALOG RUNNER - EXTRACT ALL SONGS"
echo "================================================================================================"
echo ""
echo "Campaign: $CAMPAIGN_NAME"
echo "Accounts CSV: $ACCOUNTS_CSV"
echo "Output: $OUTPUT_PREFIX_aggregated.csv / $OUTPUT_PREFIX_detailed.csv"
echo ""
echo "================================================================================================"
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the full catalog scraper
python3 full_catalog_scraper.py \
    --accounts "$ACCOUNTS_CSV" \
    --output "$OUTPUT_PREFIX" \
    "$@"

echo ""
echo "================================================================================================"
echo "Campaign Complete!"
echo "================================================================================================"
echo ""
echo "Reports saved to:"
echo "  - $OUTPUT_PREFIX_aggregated.csv (song usage summary)"
echo "  - $OUTPUT_PREFIX_detailed.csv (all videos list)"
echo ""
