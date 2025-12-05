"""
Report API endpoints
"""

from flask import jsonify, request
from services.database import get_videos_by_session, get_all_sessions

# Import api_bp from parent module
from api import api_bp


@api_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate analytics report from filtered data."""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        sound_keys = data.get('sound_keys')
        format_type = data.get('format', 'json')  # 'json' or 'html'
        
        if not session_id:
            # Get most recent session
            sessions = get_all_sessions(limit=1)
            if not sessions:
                return jsonify({
                    'success': False,
                    'error': 'No sessions found'
                }), 404
            session_id = sessions[0]['session_id']
        
        if format_type == 'html':
            # Generate HTML report
            html_file = save_html_report(session_id, sound_keys)
            return jsonify({
                'success': True,
                'report_url': f'/output/{html_file.name}',
                'file_path': str(html_file),
                'message': 'HTML report generated successfully'
            })
        else:
            # Generate JSON report
            # Get videos
            filters = {}
            videos = get_videos_by_session(session_id, filters)
            
            # Filter by sound_keys if provided
            if sound_keys:
                sound_keys_set = set(sound_keys)
                videos = [v for v in videos if v.get('sound_key') in sound_keys_set]
            
            # Group by account
            from collections import defaultdict
            accounts_data = defaultdict(lambda: {'videos': [], 'sounds': defaultdict(list)})
            
            for video in videos:
                account = video.get('account')
                sound_key = video.get('sound_key')
                
                accounts_data[account]['videos'].append(video)
                accounts_data[account]['sounds'][sound_key].append(video)
            
            # Generate report data
            from datetime import datetime
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_videos': len(videos),
                'total_accounts': len(accounts_data),
                'accounts': []
            }
            
            for account, data in accounts_data.items():
                account_report = {
                    'username': account,
                    'total_videos': len(data['videos']),
                    'total_sounds': len(data['sounds']),
                    'sounds': []
                }
                
                # Sound stats
                for sound_key, sound_videos in data['sounds'].items():
                    sound_stat = {
                        'sound_key': sound_key,
                        'video_count': len(sound_videos),
                        'total_views': sum(v.get('views', 0) for v in sound_videos),
                        'total_likes': sum(v.get('likes', 0) for v in sound_videos),
                        'total_comments': sum(v.get('comments', 0) for v in sound_videos),
                        'total_shares': sum(v.get('shares', 0) for v in sound_videos),
                        'avg_engagement_rate': round(
                            sum(v.get('engagement_rate', 0) for v in sound_videos) / len(sound_videos) if sound_videos else 0,
                            2
                        ),
                        'videos': sound_videos
                    }
                    account_report['sounds'].append(sound_stat)
                
                # Sort sounds by video count
                account_report['sounds'].sort(key=lambda x: x['video_count'], reverse=True)
                
                report['accounts'].append(account_report)
            
            # Sort accounts by video count
            report['accounts'].sort(key=lambda x: x['total_videos'], reverse=True)
            
            return jsonify({
                'success': True,
                'report': report
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

