#!/usr/bin/env python3
"""
TikTok Profile Analyzer
Extracts engagement metrics and song information from TikTok profile videos
"""

import sys
import argparse
import subprocess
import json
import re
from datetime import datetime
from extract_sound_id import extract_sound_id_from_video

def get_profile_username(url_or_username):
    """Extract username from TikTok profile URL or handle"""
    if not url_or_username.startswith('http'):
        username = url_or_username.lstrip('@')
        return username

    match = re.search(r'@([\w\.]+)', url_or_username)
    if match:
        return match.group(1)
    return None

def build_profile_url(username):
    """Build TikTok profile URL from username"""
    return f"https://www.tiktok.com/@{username}"

def scrape_profile_videos_detailed(profile_url, limit=10):
    """
    Scrape videos from a TikTok profile with full metadata including song info
    """
    print(f"Analyzing profile: {profile_url}")
    print(f"Fetching detailed metadata for recent videos...")
    print("")

    # Use yt-dlp to get full video metadata
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--dump-json',
        '--playlist-end', str(limit * 3),  # Fetch more to ensure we get enough
        profile_url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error scraping profile: {result.stderr}")
        return []

    # Parse JSON output (one JSON object per line)
    videos = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                video_data = json.loads(line)

                # Extract upload date/timestamp
                upload_date = video_data.get('upload_date', '')
                if upload_date:
                    try:
                        upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                        formatted_date = upload_datetime.strftime('%Y-%m-%d')
                    except:
                        formatted_date = upload_date
                else:
                    formatted_date = 'Unknown'

                # Extract music link - try multiple possible fields
                music_link = None
                music_id = video_data.get('music_id') or video_data.get('musicId')
                
                # Try to construct music link from music_id
                if music_id:
                    # Music links are typically: https://www.tiktok.com/music/[Song-Name]-[music_id]
                    track = video_data.get('track', '')
                    if track:
                        # Create URL-friendly version of track name
                        track_slug = track.replace(' ', '-').replace("'", '').replace('(', '').replace(')', '')
                        music_link = f"https://www.tiktok.com/music/{track_slug}-{music_id}"
                    else:
                        music_link = f"https://www.tiktok.com/music/original-sound-{music_id}"
                
                # Also check if music_info has a URL
                music_info = video_data.get('music_info', {})
                if isinstance(music_info, dict):
                    if 'url' in music_info:
                        music_link = music_info['url']
                    elif 'music_url' in music_info:
                        music_link = music_info['music_url']
                
                # Check for music URL in other fields
                if not music_link:
                    # Search through all string values for music URLs
                    for key, value in video_data.items():
                        if isinstance(value, str) and 'tiktok.com/music/' in value:
                            music_link = value
                            break
                
                video_url = video_data.get('webpage_url') or video_data.get('url')

                # Extract sound ID by fetching the video page
                # This is the ONLY reliable way to get the actual sound ID
                print(f"  Fetching sound ID for video {video_data.get('id')}...")
                sound_id, song_title_from_page = extract_sound_id_from_video(video_url)

                # Use song title from video page if available, otherwise from yt-dlp
                song_title = song_title_from_page or video_data.get('track', '')

                video_info = {
                    'id': video_data.get('id'),
                    'url': video_url,
                    'title': video_data.get('title', '').strip(),
                    'description': video_data.get('description', '').strip(),
                    'views': video_data.get('view_count', 0),
                    'likes': video_data.get('like_count', 0),
                    'comments': video_data.get('comment_count', 0),
                    'shares': video_data.get('repost_count', 0),
                    'duration': video_data.get('duration', 0),
                    'upload_date': formatted_date,
                    'timestamp': video_data.get('timestamp', 0),
                    # Song/music information
                    'song_title': song_title,
                    'song_artist': video_data.get('artist', ''),
                    'song_album': video_data.get('album', ''),
                    'music_info': music_info,
                    'music_link': music_link,  # This will likely be None
                    'music_id': sound_id,  # THE ACTUAL SOUND ID from video page
                }

                # Try to extract music info from other fields if not in standard fields
                if not video_info['song_title']:
                    # Check creator field or other music-related fields
                    creator = video_data.get('creator', '')
                    if creator:
                        video_info['song_artist'] = creator

                videos.append(video_info)

                if len(videos) >= limit:
                    break

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                continue

    # Sort by timestamp (most recent first) if available, otherwise by views
    videos.sort(key=lambda x: (x['timestamp'] if x['timestamp'] else 0), reverse=True)

    return videos[:limit]

def format_number(num):
    """Format number with commas"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def display_video_analysis(videos):
    """Display detailed analysis of videos"""
    print("=" * 100)
    print(f"ENGAGEMENT ANALYSIS - Last {len(videos)} Videos")
    print("=" * 100)
    print("")

    for i, video in enumerate(videos, 1):
        print(f"VIDEO #{i}")
        print(f"{'─' * 100}")
        print(f"Title/Caption: {video['title'][:80] if video['title'] else '(No caption)'}")
        print(f"URL: {video['url']}")
        print(f"Upload Date: {video['upload_date']}")

        # Display timestamp if available
        if video.get('timestamp'):
            from datetime import datetime
            timestamp_dt = datetime.fromtimestamp(video['timestamp'])
            print(f"Posted: {timestamp_dt.strftime('%Y-%m-%d %I:%M %p')}")

        print("")
        print(f"ENGAGEMENT METRICS:")
        print(f"  Views:    {format_number(video['views']):>10} ({video['views']:,})")
        print(f"  Likes:    {format_number(video['likes']):>10} ({video['likes']:,})")
        print(f"  Comments: {format_number(video['comments']):>10} ({video['comments']:,})")
        print(f"  Shares:   {format_number(video['shares']):>10} ({video['shares']:,})")

        # Calculate engagement rate
        if video['views'] > 0:
            engagement_rate = ((video['likes'] + video['comments'] + video['shares']) / video['views']) * 100
            print(f"  Engagement Rate: {engagement_rate:.2f}%")

        print("")
        print(f"MUSIC/SOUND:")
        if video['song_title'] or video['song_artist']:
            print(f"  Song: {video['song_title'] or 'Unknown'}")
            print(f"  Artist: {video['song_artist'] or 'Unknown'}")
            if video['song_album']:
                print(f"  Album: {video['song_album']}")
        else:
            print(f"  Music info not available (may be original sound)")

        print("")
        print("")

    # Summary statistics
    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    total_views = sum(v['views'] for v in videos)
    total_likes = sum(v['likes'] for v in videos)
    total_comments = sum(v['comments'] for v in videos)
    total_shares = sum(v['shares'] for v in videos)

    avg_views = total_views // len(videos) if videos else 0
    avg_likes = total_likes // len(videos) if videos else 0
    avg_comments = total_comments // len(videos) if videos else 0
    avg_shares = total_shares // len(videos) if videos else 0

    print(f"Total Videos Analyzed: {len(videos)}")
    print(f"")
    print(f"Average Performance:")
    print(f"  Avg Views:    {format_number(avg_views)} ({avg_views:,})")
    print(f"  Avg Likes:    {format_number(avg_likes)} ({avg_likes:,})")
    print(f"  Avg Comments: {format_number(avg_comments)} ({avg_comments:,})")
    print(f"  Avg Shares:   {format_number(avg_shares)} ({avg_shares:,})")

    if total_views > 0:
        overall_engagement = ((total_likes + total_comments + total_shares) / total_views) * 100
        print(f"  Overall Engagement Rate: {overall_engagement:.2f}%")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze engagement metrics and songs from TikTok profile'
    )
    parser.add_argument('--url', required=True,
                       help='TikTok username or profile URL')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of recent videos to analyze (default: 10)')

    args = parser.parse_args()

    # Extract username
    username = get_profile_username(args.url)
    if not username:
        print("Error: Could not extract username")
        return 1

    # Build full profile URL
    profile_url = build_profile_url(username)

    print(f"\n🔍 TikTok Profile Analyzer")
    print(f"Profile: @{username}")
    print(f"=" * 100)
    print("")

    # Scrape and analyze videos
    videos = scrape_profile_videos_detailed(profile_url, args.limit)

    if not videos:
        print("No videos found or unable to scrape profile")
        return 1

    # Display analysis
    display_video_analysis(videos)

    return 0

if __name__ == '__main__':
    sys.exit(main())
