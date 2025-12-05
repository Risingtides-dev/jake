# Deploy Reports to the Internet

Quick deployment options for your HTML reports.

## Quick Deploy (Recommended)

### Option 1: Netlify Drop (No CLI needed - Easiest!)
1. Go to: https://app.netlify.com/drop
2. Drag and drop your `output/*_report.html` file
3. Get instant live URL!

### Option 2: Using the deploy script
```bash
# Deploy to Netlify
./deploy.sh campaigns/warner/warner_oct13_nov13_2025.csv netlify

# Deploy to Vercel
./deploy.sh campaigns/warner/warner_oct13_nov13_2025.csv vercel

# Deploy to Surge.sh
./deploy.sh campaigns/warner/warner_oct13_nov13_2025.csv surge
```

## Installation (One-time setup)

### Netlify CLI
```bash
npm install -g netlify-cli
netlify login
```

### Vercel CLI
```bash
npm install -g vercel
vercel login
```

### Surge.sh CLI
```bash
npm install -g surge
surge login
```

## Manual Deployment Methods

### 1. Netlify (Easiest - Drag & Drop)
- Visit: https://app.netlify.com/drop
- Drag your HTML file
- Get instant URL

### 2. GitHub Pages
```bash
# If you have a GitHub repo
git checkout -b gh-pages
cp output/warner_oct13_nov13_2025_report.html index.html
git add index.html
git commit -m "Deploy report"
git push origin gh-pages

# Then enable in repo: Settings > Pages > Source: gh-pages branch
```

### 3. Cloudflare Pages
```bash
# Install Wrangler
npm install -g wrangler

# Deploy
cd output
wrangler pages deploy . --project-name=warner-reports
```

### 4. Vercel (via web)
- Visit: https://vercel.com
- Drag and drop your HTML file
- Get instant URL

### 5. Surge.sh (Free subdomain)
```bash
cd output
surge . your-report-name.surge.sh
```

## Quick One-Liners

### Generate + Deploy to Netlify
```bash
python3 generate_csv_report.py campaigns/warner/warner_oct13_nov13_2025.csv && \
cd output && \
netlify deploy --prod --dir=. --open
```

### Generate + Deploy to Surge
```bash
python3 generate_csv_report.py campaigns/warner/warner_oct13_nov13_2025.csv && \
cd output && \
cp warner_oct13_nov13_2025_report.html index.html && \
surge . warner-report-$(date +%Y%m%d).surge.sh
```

## Recommended: Netlify Drop
**Fastest option** - No installation needed:
1. Generate report: `python3 generate_csv_report.py campaigns/warner/warner_oct13_nov13_2025.csv`
2. Go to: https://app.netlify.com/drop
3. Drag `output/warner_oct13_nov13_2025_report.html` to the page
4. Get instant live URL!

