#!/bin/bash
#
# Filtered Campaign Runner - For matching videos against specific songs
# Usage: ./run_filtered_campaign.sh <campaign_folder> [options]
#
# Example: ./run_filtered_campaign.sh campaigns/warner --start-date 2025-10-14 --limit 500
#

set -e

# Check if campaign folder provided
if [ -z "$1" ]; then
    echo "Usage: ./run_filtered_campaign.sh <campaign_folder> [options]"
    echo ""
    echo "Example:"
    echo "  ./run_filtered_campaign.sh campaigns/warner"
    echo "  ./run_filtered_campaign.sh campaigns/plgrnd --start-date 2025-11-01 --limit 1000"
    echo ""
    echo "Campaign folder should contain:"
    echo "  - songs.csv (with columns: Song Link, Song, Artist Name)"
    echo "  - accounts.csv (with columns: URL or account Handle)"
    exit 1
fi

CAMPAIGN_DIR="$1"
shift  # Remove campaign dir from args, keep remaining options

# Check if campaign directory exists
if [ ! -d "$CAMPAIGN_DIR" ]; then
    echo "Error: Campaign directory '$CAMPAIGN_DIR' does not exist"
    exit 1
fi

# Find songs.csv
SONGS_CSV=$(find "$CAMPAIGN_DIR" -maxdepth 1 -name "*songs*.csv" -o -name "*Songs*.csv" -o -name "*SONGS*.csv" | head -n 1)
if [ -z "$SONGS_CSV" ]; then
    echo "Error: No songs CSV found in $CAMPAIGN_DIR"
    echo "Please add a file named 'songs.csv' or similar"
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
OUTPUT_PREFIX="$OUTPUT_DIR/${CAMPAIGN_NAME}_filtered_report"

echo "================================================================================================"
echo "FILTERED CAMPAIGN RUNNER"
echo "================================================================================================"
echo ""
echo "Campaign: $CAMPAIGN_NAME"
echo "Songs CSV: $SONGS_CSV"
echo "Accounts CSV: $ACCOUNTS_CSV"
echo "Output: $OUTPUT_PREFIX.csv"
echo ""
echo "================================================================================================"
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the filtered scraper (modified full_production_scrape.py)
python3 filtered_campaign_scraper.py \
    --songs "$SONGS_CSV" \
    --accounts "$ACCOUNTS_CSV" \
    --output "$OUTPUT_PREFIX" \
    "$@"

echo ""
echo "================================================================================================"
echo "Campaign Complete!"
echo "================================================================================================"
echo ""
echo "Reports saved to:"
echo "  - $OUTPUT_PREFIX.csv"
echo ""
