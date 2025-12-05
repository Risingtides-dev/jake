"""
Video API endpoints
"""

from flask import jsonify, request
from services.database import get_videos_by_session, get_session, get_all_sessions

# Import api_bp from parent module
from api import api_bp


@api_bp.route('/videos', methods=['GET'])
def list_videos():
    """Get videos with optional filters."""
    try:
        session_id = request.args.get('session_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        account = request.args.get('account')
        sound_key = request.args.get('sound_key')
        
        if not session_id:
            # Get most recent session
            sessions = get_all_sessions(limit=1)
            if not sessions:
                return jsonify({
                    'success': False,
                    'error': 'No sessions found'
                }), 404
            session_id = sessions[0]['session_id']
        
        # Build filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if account:
            filters['account'] = account
        if sound_key:
            filters['sound_key'] = sound_key
        
        videos = get_videos_by_session(session_id, filters)
        
        return jsonify({
            'success': True,
            'videos': videos,
            'count': len(videos),
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

