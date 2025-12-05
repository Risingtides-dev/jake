#!/bin/bash
#
# Warner Sound Tracker - Web UI Startup Script
#
# This script activates the virtual environment and starts the Flask web UI.
# Access the UI at: http://localhost:5000
#

cd "$(dirname "$0")"

echo "======================================================================"
echo "  Warner Sound Tracker - Web UI"
echo "======================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

echo ""
echo "Starting web server..."
echo "Access the UI at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"
echo ""

python3 web_ui.py
