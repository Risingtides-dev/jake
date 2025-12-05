#!/bin/bash

# Quick report generator and opener
# Usage: ./generate_report.sh campaigns/warner/warner_oct13_nov13_2025.csv

if [ -z "$1" ]; then
    echo "Usage: $0 <csv_file>"
    echo "Example: $0 campaigns/warner/warner_oct13_nov13_2025.csv"
    exit 1
fi

CSV_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

echo "📊 Generating report from: $CSV_FILE"
python3 generate_csv_report.py "$CSV_FILE"

if [ $? -eq 0 ]; then
    # Get the output filename
    CSV_BASENAME=$(basename "$CSV_FILE" .csv)
    OUTPUT_FILE="output/${CSV_BASENAME}_report.html"
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo ""
        echo "✅ Report generated successfully!"
        echo "📂 Opening: $OUTPUT_FILE"
        
        # Open in default browser (works on macOS, Linux, Windows)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "$OUTPUT_FILE"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open "$OUTPUT_FILE"
        elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            start "$OUTPUT_FILE"
        else
            echo "Please open manually: $OUTPUT_FILE"
        fi
    else
        echo "❌ Error: Report file not found: $OUTPUT_FILE"
        exit 1
    fi
else
    echo "❌ Error generating report"
    exit 1
fi

