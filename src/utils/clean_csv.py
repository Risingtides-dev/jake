#!/usr/bin/env python3
"""
Clean and convert existing Warner CSVs to the required format.

Takes your Notion export CSV and converts it to the standard format:
sound_key,song,artist,song_link

Usage:
    python3 clean_csv.py input.csv output.csv
"""

import csv
import sys
from pathlib import Path

def clean_warner_csv(input_file, output_file):
    """
    Clean Warner Sound Tracker CSV from Notion export.

    Input format (Notion export):
    Artist Name,Assignee,Description,Due date,Page Type,Posts Per Day,Priority,Song,Song Link,Status

    Output format (required):
    sound_key,song,artist,song_link
    """
    songs = []
    skipped = []

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=2):
            # Extract required fields
            artist = row.get('Artist Name', '').strip()
            song = row.get('Song', '').strip()
            song_link = row.get('Song Link', '').strip()

            # Skip if missing critical data
            if not song or not artist:
                skipped.append(f"Row {i}: Missing song or artist")
                continue

            # Create sound_key in format "Song - Artist"
            sound_key = f"{song} - {artist}"

            songs.append({
                'sound_key': sound_key,
                'song': song,
                'artist': artist,
                'song_link': song_link
            })

    # Write cleaned CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sound_key', 'song', 'artist', 'song_link'])
        writer.writeheader()
        writer.writerows(songs)

    print(f"✅ Cleaned CSV successfully!")
    print(f"   Input:  {input_file}")
    print(f"   Output: {output_file}")
    print(f"   Kept:   {len(songs)} songs")
    if skipped:
        print(f"   Skipped: {len(skipped)} rows")
        for msg in skipped[:5]:
            print(f"      - {msg}")
        if len(skipped) > 5:
            print(f"      ... and {len(skipped) - 5} more")

    return songs


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 clean_csv.py input.csv output.csv")
        print()
        print("Example:")
        print('  python3 clean_csv.py "data/Private & Shared 4/WARNER Sound Use Tracker.csv" data/warner_songs_clean.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not Path(input_file).exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    songs = clean_warner_csv(input_file, output_file)

    print()
    print("Preview of first 5 songs:")
    for i, song in enumerate(songs[:5], 1):
        print(f"  {i}. {song['sound_key']}")
