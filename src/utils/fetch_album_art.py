#!/usr/bin/env python3
"""
Fetch Album Art for Songs
Downloads album art images from various sources and stores them locally
"""

import os
import sys
import requests
import json
from pathlib import Path
from urllib.parse import quote
import hashlib

# Import configuration
try:
    import config
except ImportError:
    print("ERROR: config.py not found.")
    sys.exit(1)

# Create album art directory
ALBUM_ART_DIR = config.OUTPUT_DIR / 'album_art'
ALBUM_ART_DIR.mkdir(exist_ok=True)

def get_song_hash(song_title, artist_name):
    """Generate a hash for the song to use as filename"""
    combined = f"{song_title}|{artist_name}".lower().strip()
    return hashlib.md5(combined.encode('utf-8')).hexdigest()

def fetch_from_itunes(song_title, artist_name):
    """Fetch album art from iTunes API"""
    try:
        # Clean up the search terms
        search_term = f"{song_title} {artist_name}".strip()
        encoded = quote(search_term)
        
        url = f"https://itunes.apple.com/search?term={encoded}&media=music&limit=1"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                artwork_url = result.get('artworkUrl100') or result.get('artworkUrl60')
                
                if artwork_url:
                    # Get higher resolution (600x600)
                    artwork_url = artwork_url.replace('100x100', '600x600').replace('60x60', '600x600')
                    return artwork_url
    except Exception as e:
        print(f"  ⚠️  iTunes API error: {e}")
    
    return None

def fetch_from_lastfm(song_title, artist_name):
    """Fetch album art from Last.fm API (requires API key, but we can try without)"""
    try:
        # Last.fm requires API key, but we can try a direct image URL pattern
        # This is a fallback method
        search_term = f"{artist_name} {song_title}".strip()
        # Last.fm image URLs are complex, so we'll skip this for now
        pass
    except Exception as e:
        pass
    
    return None

def download_image(url, filepath):
    """Download image from URL and save to filepath"""
    try:
        response = requests.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"  ⚠️  Download error: {e}")
    
    return False

def get_album_art(song_title, artist_name, force_refresh=False):
    """
    Get album art for a song. Returns the local file path if found/downloaded.
    
    Args:
        song_title: Song title
        artist_name: Artist name
        force_refresh: If True, re-download even if file exists
    
    Returns:
        Path to local image file, or None if not found
    """
    if not song_title or not artist_name or song_title == 'Unknown' or artist_name == 'Unknown':
        return None
    
    # Generate filename
    file_hash = get_song_hash(song_title, artist_name)
    image_path = ALBUM_ART_DIR / f"{file_hash}.jpg"
    
    # Check if we already have it
    if image_path.exists() and not force_refresh:
        return image_path
    
    print(f"  🎨 Fetching album art for: {song_title} - {artist_name}")
    
    # Try iTunes first (most reliable, no API key needed)
    artwork_url = fetch_from_itunes(song_title, artist_name)
    
    if artwork_url:
        if download_image(artwork_url, image_path):
            print(f"  ✅ Downloaded: {image_path.name}")
            return image_path
        else:
            print(f"  ❌ Failed to download image")
    else:
        print(f"  ⚠️  No artwork found")
    
    return None

def batch_fetch_album_art(songs_list):
    """
    Batch fetch album art for a list of songs.
    
    Args:
        songs_list: List of dicts with 'song' and 'artist' keys
    
    Returns:
        Dict mapping (song, artist) tuples to image paths
    """
    results = {}
    total = len(songs_list)
    
    print(f"\n🎨 Fetching album art for {total} songs...\n")
    
    for i, song_info in enumerate(songs_list, 1):
        song_title = song_info.get('song', '') or song_info.get('song_title', '')
        artist_name = song_info.get('artist', '') or song_info.get('song_artist', '')
        
        if song_title and artist_name:
            image_path = get_album_art(song_title, artist_name)
            if image_path:
                results[(song_title, artist_name)] = image_path
        
        # Progress indicator
        if i % 10 == 0:
            print(f"  Progress: {i}/{total} songs processed...")
    
    print(f"\n✅ Album art fetch complete! Found {len(results)} images.")
    return results

def get_relative_image_path(absolute_path):
    """Convert absolute path to relative path from output directory"""
    if absolute_path is None:
        return None
    
    try:
        # Get relative path from output directory
        rel_path = absolute_path.relative_to(config.OUTPUT_DIR)
        return str(rel_path)
    except:
        # Fallback: just return the filename
        return absolute_path.name if absolute_path else None

if __name__ == '__main__':
    # Test with a few songs
    test_songs = [
        {'song': 'Midnight Dreams', 'artist': 'The Sound Collective'},
        {'song': 'Urban Vibes', 'artist': 'City Beats'},
        {'song': 'Chill Beats', 'artist': 'Relaxation Station'},
    ]
    
    print("Testing album art fetching...\n")
    results = batch_fetch_album_art(test_songs)
    
    print(f"\n📊 Results:")
    for (song, artist), path in results.items():
        print(f"  {song} - {artist}: {path}")

