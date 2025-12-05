#!/bin/bash

# Deploy report to GitHub Pages
# Usage: ./deploy_to_github.sh <repo-name> <csv-file>

REPO_NAME="${1:-warner-reports}"
CSV_FILE="${2:-campaigns/warner/warner_oct13_nov13_2025.csv}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Deploying to GitHub Pages..."
echo ""

# Generate the report
echo "📊 Generating report from: $CSV_FILE"
python3 generate_csv_report.py "$CSV_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Error generating report"
    exit 1
fi

CSV_BASENAME=$(basename "$CSV_FILE" .csv)
REPORT_FILE="output/${CSV_BASENAME}_report.html"

if [ ! -f "$REPORT_FILE" ]; then
    echo "❌ Report file not found: $REPORT_FILE"
    exit 1
fi

echo "✅ Report generated: $REPORT_FILE"
echo ""

# Create a temporary directory for GitHub Pages
TEMP_DIR=$(mktemp -d)
echo "📁 Creating deployment directory..."

# Copy report as index.html
cp "$REPORT_FILE" "$TEMP_DIR/index.html"

# Create a simple README
cat > "$TEMP_DIR/README.md" << EOF
# Warner Reports

Analytics dashboard for TikTok sound usage tracking.

## View Report

The report is automatically deployed via GitHub Pages.

EOF

# Initialize git repo in temp directory
cd "$TEMP_DIR"
git init
git add .
git commit -m "Deploy report: $CSV_BASENAME"

echo ""
echo "✅ Deployment package ready!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   Repository name: $REPO_NAME"
echo "   Make it PUBLIC (required for free GitHub Pages)"
echo ""
echo "2. Run these commands:"
echo ""
echo "   cd $TEMP_DIR"
echo "   git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Enable GitHub Pages:"
echo "   - Go to: https://github.com/YOUR_USERNAME/$REPO_NAME/settings/pages"
echo "   - Source: Deploy from a branch"
echo "   - Branch: main"
echo "   - Folder: / (root)"
echo "   - Click Save"
echo ""
echo "4. Your report will be live at:"
echo "   https://YOUR_USERNAME.github.io/$REPO_NAME/"
echo ""
echo "📂 Deployment files are in: $TEMP_DIR"
echo ""
echo "💡 Tip: You can also use the GitHub CLI:"
echo "   gh repo create $REPO_NAME --public --source=$TEMP_DIR --remote=origin --push"



