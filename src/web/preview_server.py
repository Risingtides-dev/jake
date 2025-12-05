#!/usr/bin/env python3
"""
Live Preview Server for HTML Reports
Serves HTML files with auto-reload functionality for real-time design preview
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path
import threading
import time

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()
OUTPUT_DIR = PROJECT_ROOT / 'output'
PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler with CORS and auto-reload script injection"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve files from output directory
        if self.path == '/' or self.path == '/index.html':
            # List available HTML files
            html_files = list(OUTPUT_DIR.glob('*.html'))
            if html_files:
                # Redirect to first HTML file
                self.path = f'/output/{html_files[0].name}'
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'<h1>No HTML files found in output directory</h1>')
                return
        
        # Serve from project root
        if self.path.startswith('/output/'):
            file_path = OUTPUT_DIR / self.path[8:]  # Remove '/output/' prefix
            if file_path.exists() and file_path.suffix == '.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Read and inject auto-reload script
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8')
                    
                    # Inject auto-reload script before </body>
                    reload_script = '''
                    <script>
                        // Auto-reload every 2 seconds if file changes
                        let lastModified = null;
                        setInterval(async () => {
                            try {
                                const response = await fetch(window.location.href + '?check=' + Date.now());
                                const text = await response.text();
                                const parser = new DOMParser();
                                const doc = parser.parseFromString(text, 'text/html');
                                const newContent = doc.body.innerHTML;
                                
                                if (newContent !== document.body.innerHTML) {
                                    console.log('Content changed, reloading...');
                                    location.reload();
                                }
                            } catch (e) {
                                console.error('Error checking for updates:', e);
                            }
                        }, 2000);
                    </script>
                    '''
                    
                    if '</body>' in content:
                        content = content.replace('</body>', reload_script + '</body>')
                    else:
                        content += reload_script
                    
                    self.wfile.write(content.encode('utf-8'))
                return
        
        # Default file serving
        return super().do_GET()

def start_server():
    """Start the preview server"""
    os.chdir(PROJECT_ROOT)
    
    handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"\n{'='*60}")
            print(f"🚀 Live Preview Server Started")
            print(f"{'='*60}")
            print(f"📍 Server running at: http://localhost:{PORT}")
            print(f"📁 Serving from: {PROJECT_ROOT}")
            print(f"📂 Output directory: {OUTPUT_DIR}")
            print(f"\n💡 Available HTML files:")
            
            html_files = list(OUTPUT_DIR.glob('*.html'))
            if html_files:
                for i, html_file in enumerate(html_files, 1):
                    print(f"   {i}. http://localhost:{PORT}/output/{html_file.name}")
            else:
                print("   ⚠️  No HTML files found. Generate a report first!")
            
            print(f"\n🔄 Auto-reload enabled (checks every 2 seconds)")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print(f"{'='*60}\n")
            
            # Open browser automatically
            if html_files:
                url = f"http://localhost:{PORT}/output/{html_files[0].name}"
                print(f"🌐 Opening browser: {url}\n")
                webbrowser.open(url)
            
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use.")
            print(f"💡 Try: lsof -ti:{PORT} | xargs kill")
            sys.exit(1)
        else:
            raise

if __name__ == '__main__':
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    start_server()

