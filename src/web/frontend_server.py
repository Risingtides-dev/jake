#!/usr/bin/env python3
"""
Frontend server for Warner Sound Tracker Dashboard
Serves the frontend application on port 8000
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
PORT = 8000


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler with CORS and SPA routing support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve files from frontend directory
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
        
        # Serve static files
        return super().do_GET()


def start_server():
    """Start the frontend server"""
    # Ensure frontend directory exists
    FRONTEND_DIR.mkdir(exist_ok=True)
    
    handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"\n{'='*60}")
            print(f"🚀 Frontend Server Started")
            print(f"{'='*60}")
            print(f"📍 Server running at: http://localhost:{PORT}")
            print(f"📁 Serving from: {FRONTEND_DIR}")
            print(f"🔗 Backend API: http://localhost:5001/api/v1")
            print(f"\n💡 Make sure the backend is running on port 5001")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print(f"{'='*60}\n")
            
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use.")
            print(f"💡 Try: lsof -ti:{PORT} | xargs kill")
            sys.exit(1)
        else:
            raise


if __name__ == '__main__':
    start_server()

