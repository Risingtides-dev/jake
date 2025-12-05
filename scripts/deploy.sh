#!/bin/bash

# Quick deployment script for HTML reports
# Supports: Netlify, Vercel, Surge, GitHub Pages

CSV_FILE="${1:-campaigns/warner/warner_oct13_nov13_2025.csv}"
DEPLOY_METHOD="${2:-netlify}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Generate report first
echo "📊 Generating report..."
python3 generate_csv_report.py "$CSV_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Error generating report"
    exit 1
fi

CSV_BASENAME=$(basename "$CSV_FILE" .csv)
OUTPUT_FILE="output/${CSV_BASENAME}_report.html"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Report file not found: $OUTPUT_FILE"
    exit 1
fi

echo "✅ Report generated: $OUTPUT_FILE"
echo ""

case "$DEPLOY_METHOD" in
    netlify)
        echo "🚀 Deploying to Netlify..."
        if ! command -v netlify &> /dev/null; then
            echo "Installing Netlify CLI..."
            npm install -g netlify-cli
        fi
        # Create a temp directory with the report
        TEMP_DIR=$(mktemp -d)
        cp "$OUTPUT_FILE" "$TEMP_DIR/index.html"
        cd "$TEMP_DIR"
        netlify deploy --prod --dir=. --open
        cd "$SCRIPT_DIR"
        rm -rf "$TEMP_DIR"
        ;;
    
    vercel)
        echo "🚀 Deploying to Vercel..."
        if ! command -v vercel &> /dev/null; then
            echo "Installing Vercel CLI..."
            npm install -g vercel
        fi
        TEMP_DIR=$(mktemp -d)
        cp "$OUTPUT_FILE" "$TEMP_DIR/index.html"
        cd "$TEMP_DIR"
        vercel --prod --yes
        cd "$SCRIPT_DIR"
        rm -rf "$TEMP_DIR"
        ;;
    
    surge)
        echo "🚀 Deploying to Surge.sh..."
        if ! command -v surge &> /dev/null; then
            echo "Installing Surge CLI..."
            npm install -g surge
        fi
        TEMP_DIR=$(mktemp -d)
        cp "$OUTPUT_FILE" "$TEMP_DIR/index.html"
        cd "$TEMP_DIR"
        surge . "${CSV_BASENAME}-report.surge.sh"
        cd "$SCRIPT_DIR"
        rm -rf "$TEMP_DIR"
        ;;
    
    github)
        echo "🚀 Deploying to GitHub Pages..."
        # Check if we're in a git repo
        if [ ! -d ".git" ]; then
            echo "❌ Not a git repository. Initialize with: git init"
            exit 1
        fi
        
        # Create gh-pages branch and deploy
        git checkout -b gh-pages 2>/dev/null || git checkout gh-pages
        cp "$OUTPUT_FILE" index.html
        git add index.html
        git commit -m "Deploy report: $CSV_BASENAME" 2>/dev/null || true
        git push origin gh-pages --force
        git checkout main 2>/dev/null || git checkout master 2>/dev/null || git checkout -b main
        
        echo "✅ Deployed! Enable GitHub Pages in repo settings: Settings > Pages > Source: gh-pages branch"
        ;;
    
    *)
        echo "❌ Unknown deployment method: $DEPLOY_METHOD"
        echo "Available methods: netlify, vercel, surge, github"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment complete!"

