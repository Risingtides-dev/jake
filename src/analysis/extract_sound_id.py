#!/usr/bin/env python3
"""
Extract sound ID from TikTok video URL
"""

import requests
import json
import re
import sys

def extract_sound_id_from_video(video_url):
    """
    Extract the sound/music ID from a TikTok video by fetching its webpage
    and parsing the embedded JSON data.

    Args:
        video_url: TikTok video URL (e.g., https://www.tiktok.com/@user/video/123...)

    Returns:
        tuple: (sound_id, song_title) or (None, None) if not found

    Example:
        sound_id, song_title = extract_sound_id_from_video(video_url)
        # Returns: ("7560990161272621073", "Rollin' Stone (Full Band Version)")
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Fetch the video page HTML
        response = requests.get(video_url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None, None

        html = response.text

        # Extract JSON data embedded in the page
        # TikTok embeds video data in <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
        pattern = r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL)

        if not matches:
            return None, None

        # Parse the JSON
        data = json.loads(matches[0])

        # Navigate to the music object
        try:
            music = data['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']['music']
            sound_id = music.get('id')
            song_title = music.get('title', '')

            return sound_id, song_title
        except (KeyError, TypeError):
            return None, None

    except Exception as e:
        print(f"Error extracting sound ID from {video_url}: {e}", file=sys.stderr)
        return None, None


def extract_sound_id_from_music_link(music_link):
    """
    Extract sound ID from a TikTok music link by fetching the music page.

    Args:
        music_link: TikTok music URL (e.g., https://www.tiktok.com/music/Pink-Skies-7371957890313275408)

    Returns:
        tuple: (sound_id, song_title, artist_name) or (None, None, None) if not found

    Example:
        sound_id, song_title, artist = extract_sound_id_from_music_link(link)
        # Returns: ("7371957890313275408", "Pink Skies", "Zach Bryan")
    """
    try:
        # First try to extract ID from URL pattern
        # Clean URL first (remove query params)
        clean_link = music_link.split('?')[0].split('&')[0]
        url_id_match = re.search(r'music/[^/]+-(\d+)', clean_link)
        url_sound_id = url_id_match.group(1) if url_id_match else None

        # Fetch the music page to get authoritative data
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(music_link, headers=headers, timeout=15)

        if response.status_code != 200:
            return url_sound_id, None, None

        html = response.text

        # Extract JSON data from the music page
        pattern = r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL)

        if not matches:
            return url_sound_id, None, None

        data = json.loads(matches[0])

        # Navigate to the music object
        try:
            music = data['__DEFAULT_SCOPE__']['webapp.music-detail']['musicInfo']['music']
            sound_id = music.get('id', url_sound_id)
            song_title = music.get('title', '')
            artist_name = music.get('authorName', '')

            return sound_id, song_title, artist_name
        except (KeyError, TypeError):
            return url_sound_id, None, None

    except Exception as e:
        print(f"Error extracting sound ID from music link {music_link}: {e}", file=sys.stderr)
        # Try to at least return the ID from the URL
        url_id_match = re.search(r'music/[^/]+-(\d+)', music_link)
        if url_id_match:
            return url_id_match.group(1), None, None
        return None, None, None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 extract_sound_id.py <video_or_music_url>")
        print()
        print("Examples:")
        print("  python3 extract_sound_id.py 'https://www.tiktok.com/@user/video/123...'")
        print("  python3 extract_sound_id.py 'https://www.tiktok.com/music/Pink-Skies-7371957890313275408'")
        sys.exit(1)

    url = sys.argv[1]

    if '/video/' in url:
        sound_id, song_title = extract_sound_id_from_video(url)
        if sound_id:
            print(f"Sound ID: {sound_id}")
            print(f"Song: {song_title}")
        else:
            print("Could not extract sound ID from video")
    elif '/music/' in url:
        sound_id, song_title, artist = extract_sound_id_from_music_link(url)
        if sound_id:
            print(f"Sound ID: {sound_id}")
            if song_title:
                print(f"Song: {song_title}")
            if artist:
                print(f"Artist: {artist}")
        else:
            print("Could not extract sound ID from music link")
    else:
        print("Error: URL must be a TikTok video or music link")
