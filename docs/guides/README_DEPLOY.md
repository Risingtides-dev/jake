# Quick Deploy Guide

## Generate and Open Report

### Option 1: Using the shell script (easiest)
```bash
./generate_report.sh campaigns/warner/warner_oct13_nov13_2025.csv
```

### Option 2: Direct Python command
```bash
python3 generate_csv_report.py campaigns/warner/warner_oct13_nov13_2025.csv && open output/warner_oct13_nov13_2025_report.html
```

### Option 3: One-liner with auto-open
```bash
python3 generate_csv_report.py campaigns/warner/warner_oct13_nov13_2025.csv && open output/$(basename campaigns/warner/warner_oct13_nov13_2025.csv .csv)_report.html
```

## Serve Locally (for sharing/testing)

### Simple HTTP Server
```bash
cd output
python3 -m http.server 8000
```
Then open: http://localhost:8000/warner_oct13_nov13_2025_report.html

### With auto-open
```bash
cd output && python3 -m http.server 8000 & sleep 1 && open http://localhost:8000/warner_oct13_nov13_2025_report.html
```

## Quick Reference

- **CSV Location**: `campaigns/warner/`
- **Output Location**: `output/`
- **Report Format**: Single HTML file (self-contained, email-ready)

