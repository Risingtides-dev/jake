# Multi-Campaign Tracker System

Simple drop-folder system for running TikTok tracking campaigns. Just drop your CSVs in a folder and run a command!

## Quick Start

### Step 1: Create a Campaign Folder

```bash
mkdir -p campaigns/mycampaign
```

### Step 2: Add Your CSVs

Drop your CSV files into the campaign folder:

**For Filtered Mode** (match against specific songs):
- `songs.csv` - Songs to track
- `accounts.csv` - TikTok accounts to monitor

**For Full Catalog Mode** (extract all songs):
- `accounts.csv` - TikTok accounts to analyze

### Step 3: Run the Campaign

**Filtered Mode:**
```bash
./run_filtered_campaign.sh campaigns/mycampaign
```

**Full Catalog Mode:**
```bash
./run_full_catalog.sh campaigns/mycampaign
```

## Two Campaign Modes

### 1. Filtered Mode (Song Matching)

**Use When:** You want to track specific songs across accounts (e.g., Warner campaign)

**What It Does:**
- Scrapes videos from specified accounts
- Extracts sound IDs from each video
- Matches against your song list
- Reports only videos using your tracked songs

**Required CSVs:**
- `songs.csv` with columns: `Song Link`, `Song`, `Artist Name`
- `accounts.csv` with columns: `URL` or `account Handle`

**Output:**
- `{campaign}_filtered_report.csv` - Videos using your tracked songs

**Example:**
```bash
./run_filtered_campaign.sh campaigns/warner --start-date 2025-10-14 --limit 500
```

### 2. Full Catalog Mode (Complete Song Extraction)

**Use When:** You want to see ALL songs used on in-house accounts (e.g., PLGRND network)

**What It Does:**
- Scrapes ALL videos from specified accounts
- Extracts sound ID from every video
- Aggregates song usage statistics
- No filtering - captures everything

**Required CSVs:**
- `accounts.csv` with columns: `URL` or `account Handle` or `Account`

**Output:**
- `{campaign}_full_catalog_aggregated.csv` - Song usage summary
- `{campaign}_full_catalog_detailed.csv` - All videos with songs

**Example:**
```bash
./run_full_catalog.sh campaigns/plgrnd --start-date 2025-11-01 --limit 1000
```

## CSV File Formats

### songs.csv (Filtered Mode Only)
```csv
Song Link,Song,Artist Name
https://www.tiktok.com/music/Pink-Skies-7371957890313275408,Pink Skies,Zach Bryan
https://www.tiktok.com/music/Rollin-Stone-7560990161272621073,Rollin' Stone,Cassandra Coleman
```

### accounts.csv (Both Modes)
```csv
URL
https://www.tiktok.com/@beaujenkins
@codyjames6.7
https://www.tiktok.com/@gavin.wilder1?lang=en
@smoked.999
```

Or with header variations:
```csv
account Handle
@beaujenkins
@codyjames6.7
```

## Command Options

### Common Options (Both Modes)

**`--start-date YYYY-MM-DD`**
Only include videos from this date onwards

Example:
```bash
./run_full_catalog.sh campaigns/plgrnd --start-date 2025-11-01
```

**`--limit N`**
Maximum videos to scrape per account (default: 500)

Example:
```bash
./run_filtered_campaign.sh campaigns/warner --limit 1000
```

### Combining Options

```bash
./run_filtered_campaign.sh campaigns/warner \
    --start-date 2025-10-14 \
    --limit 500
```

## Directory Structure

```
warnertracker/
├── campaigns/
│   ├── warner/                      # Warner campaign
│   │   ├── songs.csv
│   │   ├── accounts.csv
│   │   └── output/
│   │       └── warner_filtered_report.csv
│   │
│   ├── plgrnd/                      # PLGRND in-house network
│   │   ├── accounts.csv
│   │   └── output/
│   │       ├── plgrnd_full_catalog_aggregated.csv
│   │       └── plgrnd_full_catalog_detailed.csv
│   │
│   └── _template/                   # Template for new campaigns
│       ├── songs.csv.example
│       └── accounts.csv.example
│
├── run_filtered_campaign.sh         # Filtered mode runner
├── run_full_catalog.sh              # Full catalog mode runner
├── full_catalog_scraper.py          # Full catalog Python script
└── full_production_scrape.py        # Filtered mode Python script (existing)
```

## Real-World Examples

### Example 1: Warner Campaign (Filtered Mode)

**Scenario:** Track 32 Warner songs across 5 creator accounts

**Setup:**
```bash
mkdir -p campaigns/warner
# Drop songs.csv with 32 Warner songs
# Drop accounts.csv with 5 accounts
```

**Run:**
```bash
./run_filtered_campaign.sh campaigns/warner \
    --start-date 2025-10-14 \
    --limit 500
```

**Output:** CSV showing which videos use Warner songs

### Example 2: PLGRND In-House Network (Full Catalog)

**Scenario:** Analyze all songs used on PLGRND-managed accounts

**Setup:**
```bash
mkdir -p campaigns/plgrnd
# Drop accounts.csv with PLGRND accounts
```

**Run:**
```bash
./run_full_catalog.sh campaigns/plgrnd \
    --start-date 2025-11-01 \
    --limit 1000
```

**Output:**
- Aggregated report showing which songs are most popular
- Detailed report listing every video with its song

### Example 3: Multiple Label Campaigns

**Scenario:** Run campaigns for multiple labels

**Setup:**
```bash
# Create campaign folders
mkdir -p campaigns/warner campaigns/plgrnd campaigns/sony

# Add CSVs to each folder
# ...
```

**Run Each:**
```bash
# Warner (filtered)
./run_filtered_campaign.sh campaigns/warner --start-date 2025-10-14

# PLGRND (full catalog)
./run_full_catalog.sh campaigns/plgrnd --start-date 2025-11-01

# Sony (filtered)
./run_filtered_campaign.sh campaigns/sony --start-date 2025-09-01
```

## Output Formats

### Filtered Mode Output (Warner-style)
**File:** `{campaign}_filtered_report.csv`

```csv
Account,Song Name,Artist,Upload Date,Views,Likes,Comments,Shares,Engagement Rate (%),Video URL,Sound ID,Caption
@beaujenkins,Pink Skies,Zach Bryan,2025-10-15,50000,2500,150,200,5.70,https://tiktok.com/...,7371957890313275408,Great song!
```

### Full Catalog Mode Outputs

**File 1:** `{campaign}_full_catalog_aggregated.csv`
```csv
Song Title,Sound ID,Total Uses,Accounts Using,Account List,Total Views,Avg Views per Video,Total Likes,Total Comments,Total Shares,Avg Engagement Rate (%),Top Video URL,Top Video Views
Pink Skies,7371957890313275408,15,"@account1,@account2",1200000,80000,60000,3500,1200,5.29,https://tiktok.com/...,250000
```

**File 2:** `{campaign}_full_catalog_detailed.csv`
```csv
Song Title,Sound ID,Account,Upload Date,Views,Likes,Comments,Shares,Engagement Rate (%),Video URL,Caption
Pink Skies,7371957890313275408,@beaujenkins,2025-11-01,50000,2500,150,200,5.70,https://tiktok.com/...,Love this song
```

## Tips & Best Practices

### CSV File Naming
The scripts automatically find CSVs by searching for:
- `*songs*.csv` or `*Songs*.csv` (for filtered mode)
- `*accounts*.csv` or `*Accounts*.csv` (both modes)

So these all work:
- `songs.csv`
- `Warner_Songs_List.csv`
- `PLGRND_accounts.csv`
- `my_accounts_2025.csv`

### Video Limits
- `--limit 500` is usually enough to go back 2-3 months for most accounts
- For very active accounts, increase to `--limit 1000`
- The scraper stops including videos once it reaches your start date

### Date Filtering
- Always use `--start-date` to avoid scraping old videos
- Format: `YYYY-MM-DD` (e.g., `2025-10-14`)
- Without start date, scrapes all videos (can be slow)

### Performance
- Each video takes ~5-15 seconds to process (fetching sound ID from TikTok)
- 100 videos ≈ 8-25 minutes
- 500 videos ≈ 40-125 minutes (per account)
- Run campaigns in the background or overnight for large datasets

### Troubleshooting

**"No songs CSV found"**
- Make sure your file is named with "songs" somewhere in the name
- Check it's in the campaign folder, not a subdirectory

**"No accounts CSV found"**
- Same as above - needs "accounts" in the filename
- Check file location

**Scraper hangs/timeout**
- Some videos may be region-locked or deleted
- The scraper will skip and continue
- Check output for "⚠️  Timeout" warnings

**Empty output**
- Check your date filter - might be excluding all videos
- Verify accounts exist and are public
- For filtered mode, ensure sound IDs in songs.csv are correct

## Adding New Campaigns

1. Create campaign folder:
   ```bash
   mkdir -p campaigns/newlabel
   ```

2. Add CSV files:
   ```bash
   # For filtered mode:
   cp campaigns/_template/songs.csv.example campaigns/newlabel/songs.csv
   cp campaigns/_template/accounts.csv.example campaigns/newlabel/accounts.csv

   # Edit the CSVs with your data
   ```

3. Run:
   ```bash
   ./run_filtered_campaign.sh campaigns/newlabel
   # or
   ./run_full_catalog.sh campaigns/newlabel
   ```

## Advanced Usage

### Running Multiple Campaigns Sequentially

Create a batch script:
```bash
#!/bin/bash
./run_filtered_campaign.sh campaigns/warner --start-date 2025-10-14
./run_full_catalog.sh campaigns/plgrnd --start-date 2025-11-01
./run_filtered_campaign.sh campaigns/sony --start-date 2025-09-01
```

### Custom Output Locations

The scripts automatically save to `campaigns/{name}/output/`

To change, modify the `OUTPUT_DIR` variable in the shell scripts.

### Modifying Scraper Behavior

Edit the Python scripts directly:
- `full_catalog_scraper.py` - Full catalog mode logic
- `full_production_scrape.py` - Filtered mode logic (existing Warner script)

## Support

For issues or questions:
1. Check CSV file formats match examples above
2. Verify TikTok accounts are public and accessible
3. Try with smaller `--limit` first (e.g., `--limit 10`) to test
4. Check the output logs for specific error messages
