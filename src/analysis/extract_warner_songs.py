#!/usr/bin/env python3
"""
Extract Warner song list from CSV file.
Outputs a Python set that can be used to filter songs in reports.
"""

import csv
from pathlib import Path

# CSV file path
CSV_FILE = Path(__file__).parent / 'data' / 'Private & Shared 4' / 'WARNER Sound Use Tracker - October 28d1465bb82981929dabde2da2622466_all.csv'

def extract_songs():
    """Extract unique songs from Warner CSV."""
    songs = set()

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row.get('Artist Name', '').strip()
            song = row.get('Song', '').strip()

            if artist and song:
                # Create sound key in format "Song - Artist"
                sound_key = f"{song} - {artist}"
                songs.add(sound_key)
            elif song:
                # Just song name if no artist
                songs.add(song)

    return songs

if __name__ == '__main__':
    songs = extract_songs()

    print(f"Found {len(songs)} Warner songs:\n")
    print("WARNER_SONGS = {")
    for song in sorted(songs):
        print(f"    '{song}',")
    print("}")

    print(f"\n\nTotal: {len(songs)} songs")
