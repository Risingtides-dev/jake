"""
Session API endpoints
"""

from flask import jsonify, request
from datetime import datetime
from services.database import (
    get_session,
    get_all_sessions,
    create_scrape_session,
    update_scrape_session
)

# Import api_bp from parent module
from api import api_bp


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """Get all scraping sessions."""
    try:
        limit = request.args.get('limit', 50, type=int)
        sessions = get_all_sessions(limit=limit)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session_by_id(session_id):
    """Get a specific session by ID."""
    try:
        session = get_session(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'session': session
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/accounts', methods=['GET'])
def list_accounts():
    """Get all tracked accounts."""
    try:
        from services.database import get_accounts
        accounts = get_accounts()
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

