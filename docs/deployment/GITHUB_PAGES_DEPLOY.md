# Deploy Report to GitHub Pages

## Quick Deploy

```bash
./deploy_github_pages.sh campaigns/warner/warner_oct13_nov13_2025.csv
```

This will:
1. Generate the report
2. Create/checkout `gh-pages` branch
3. Copy report as `index.html`
4. Push to GitHub
5. Enable GitHub Pages (you need to do this once in settings)

## Manual Steps

### 1. Enable GitHub Pages

After running the script, enable GitHub Pages:

1. Go to: https://github.com/Risingtides-dev/Tracker-Warner/settings/pages
2. Under **Source**, select:
   - **Branch**: `gh-pages`
   - **Folder**: `/ (root)`
3. Click **Save**

### 2. Access Your Report

Your report will be live at:
**https://risingtides-dev.github.io/Tracker-Warner/**

## Update Report

To update the report with new data:

```bash
./deploy_github_pages.sh campaigns/warner/your_new_file.csv
```

The script will automatically:
- Generate the new report
- Update the `gh-pages` branch
- Push the changes

## Troubleshooting

### Authentication Issues

If you get authentication errors:

**Option 1: Use SSH**
```bash
git remote set-url origin git@github.com:Risingtides-dev/Tracker-Warner.git
```

**Option 2: Use GitHub CLI**
```bash
gh auth login
```

**Option 3: Use Personal Access Token**
```bash
git remote set-url origin https://YOUR_TOKEN@github.com/Risingtides-dev/Tracker-Warner.git
```

### Branch Already Exists

If the `gh-pages` branch already exists, the script will use it. To start fresh:

```bash
git branch -D gh-pages
./deploy_github_pages.sh
```

## Repository Structure

```
Tracker-Warner/
├── index.html          # The report (on gh-pages branch)
├── README.md           # GitHub Pages README
└── ...                 # Other files (on main branch)
```

The `gh-pages` branch only contains the report files needed for GitHub Pages.



