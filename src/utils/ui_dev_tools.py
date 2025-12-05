#!/usr/bin/env python3
"""
UI Development Tools
Helper utilities for designing and previewing HTML reports
"""

import os
import sys
from pathlib import Path
import subprocess
import webbrowser
import json
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.absolute()
OUTPUT_DIR = PROJECT_ROOT / 'output'

def list_html_files():
    """List all HTML files in output directory"""
    html_files = list(OUTPUT_DIR.glob('*.html'))
    return html_files

def open_in_browser(file_path):
    """Open HTML file in default browser"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    file_url = f"file://{file_path.absolute()}"
    webbrowser.open(file_url)
    print(f"✅ Opened: {file_path.name}")
    return True

def create_test_html():
    """Create a test HTML file for UI development"""
    test_html = OUTPUT_DIR / 'ui_test.html'
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Test - Warner Tracker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 60px 20px;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            color: #fff;
            font-size: 2.75rem;
            margin-bottom: 50px;
        }
        
        .test-section {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
        }
        
        .color-palette {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .color-swatch {
            height: 100px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>UI Design Test Page</h1>
        
        <div class="test-section">
            <h2>Color Palette</h2>
            <div class="color-palette">
                <div class="color-swatch" style="background: #8a2be2;">Primary Purple</div>
                <div class="color-swatch" style="background: #a855f7;">Light Purple</div>
                <div class="color-swatch" style="background: #4b0082;">Dark Purple</div>
                <div class="color-swatch" style="background: #1a1a2e;">Dark Blue</div>
                <div class="color-swatch" style="background: #16213e;">Mid Blue</div>
            </div>
        </div>
        
        <div class="test-section">
            <h2>Typography</h2>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <h3>Heading 3</h3>
            <p>Body text - Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        </div>
    </div>
</body>
</html>'''
    
    with open(test_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created test HTML: {test_html}")
    return test_html

def watch_and_reload():
    """Watch for file changes and reload browser"""
    print("👀 Watching for file changes...")
    print("💡 This feature requires the preview server to be running")
    print("   Run: python3 preview_server.py")

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("UI Development Tools")
        print("=" * 50)
        print("Usage:")
        print("  python3 ui_dev_tools.py list          - List all HTML files")
        print("  python3 ui_dev_tools.py open <file>   - Open HTML file in browser")
        print("  python3 ui_dev_tools.py test          - Create test HTML file")
        print("  python3 ui_dev_tools.py server        - Start preview server")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        html_files = list_html_files()
        if html_files:
            print(f"\n📄 Found {len(html_files)} HTML file(s):\n")
            for i, f in enumerate(html_files, 1):
                print(f"  {i}. {f.name}")
        else:
            print("⚠️  No HTML files found in output directory")
    
    elif command == 'open':
        if len(sys.argv) < 3:
            print("❌ Please specify a file to open")
            return
        open_in_browser(sys.argv[2])
    
    elif command == 'test':
        test_file = create_test_html()
        open_in_browser(test_file)
    
    elif command == 'server':
        # Import and run preview server
        from preview_server import start_server
        start_server()
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()

