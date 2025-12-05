"""
API Blueprint for Warner Sound Tracker
Provides REST API endpoints for frontend consumption
"""

from flask import Blueprint

# Create blueprint first
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def init_api(app):
    """Initialize API blueprint and register routes."""
    # Import route modules here to register routes with blueprint
    # This happens after api_bp is created, avoiding circular imports
    import api.sessions
    import api.videos
    import api.sounds
    import api.reports
    
    # Register blueprint with app
    app.register_blueprint(api_bp)

