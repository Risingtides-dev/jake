#!/bin/bash

# Deploy report to GitHub Pages on Tracker-Warner repository
# Usage: ./deploy_github_pages.sh [csv-file]

CSV_FILE="${1:-campaigns/warner/warner_oct13_nov13_2025.csv}"
REPO_URL="https://github.com/Risingtides-dev/Tracker-Warner.git"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Deploying to GitHub Pages..."
echo "Repository: $REPO_URL"
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

# Check if we're in a git repo
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

echo "📦 Preparing deployment..."
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Create or checkout gh-pages branch
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "📂 Checking out existing gh-pages branch..."
    git checkout gh-pages
else
    echo "📂 Creating new gh-pages branch..."
    git checkout -b gh-pages 2>/dev/null || git checkout --orphan gh-pages
fi

# Copy report as index.html
echo "📄 Copying report to index.html..."
cp "$REPORT_FILE" index.html

# Create a simple README for the pages
cat > README.md << EOF
# Warner Tracker Reports

Analytics dashboard for TikTok sound usage tracking.

## Latest Report

The latest report is available at the root of this site.

Generated: $(date)
Source: $CSV_BASENAME

EOF

# Add and commit (force add index.html in case it's in .gitignore)
echo "💾 Committing changes..."
git add -f index.html README.md
git commit -m "Deploy report: $CSV_BASENAME - $(date +%Y-%m-%d)" || echo "No changes to commit"

# Push to gh-pages branch
echo ""
echo "🚀 Pushing to GitHub..."
git push origin gh-pages --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully deployed to GitHub Pages!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Go to: https://github.com/Risingtides-dev/Tracker-Warner/settings/pages"
    echo "2. Under 'Source', select:"
    echo "   - Branch: gh-pages"
    echo "   - Folder: / (root)"
    echo "3. Click Save"
    echo ""
    echo "🌐 Your report will be live at:"
    echo "   https://risingtides-dev.github.io/Tracker-Warner/"
    echo ""
else
    echo ""
    echo "❌ Error pushing to GitHub"
    echo "Make sure you have push access to the repository."
    echo ""
    echo "You may need to:"
    echo "1. Set up authentication (SSH key or GitHub token)"
    echo "2. Or push manually: git push origin gh-pages"
fi

# Switch back to original branch
git checkout "$CURRENT_BRANCH" 2>/dev/null || git checkout main 2>/dev/null

echo ""
echo "✅ Deployment script completed!"

