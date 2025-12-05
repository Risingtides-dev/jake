"""
Sound API endpoints
"""

from flask import jsonify, request
from services.database import get_sounds_by_session, get_all_sessions

# Import api_bp from parent module
from api import api_bp


@api_bp.route('/sounds', methods=['GET'])
def list_sounds():
    """Get sounds with aggregation stats."""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            # Get most recent session
            sessions = get_all_sessions(limit=1)
            if not sessions:
                return jsonify({
                    'success': False,
                    'error': 'No sessions found'
                }), 404
            session_id = sessions[0]['session_id']
        
        sounds = get_sounds_by_session(session_id)
        
        return jsonify({
            'success': True,
            'sounds': sounds,
            'count': len(sounds),
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

