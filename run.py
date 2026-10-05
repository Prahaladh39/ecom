"""
School E-Commerce Marketplace Launcher
One-click launcher for students and evaluators.
"""
import sys
import webbrowser
import threading
from app import app
from setup_db import seed_database

def open_browser():
    try:
        webbrowser.open_new("http://127.0.0.1:5000")
    except Exception:
        pass

if __name__ == '__main__':
    print("=" * 65)
    print("🎓 CBSE Class 12 Computer Science Project")
    print("📦 School Peer-to-Peer E-Commerce Marketplace")
    print("=" * 65)
    
    # 1. Initialize and verify database
    seed_database()

    print("\n🚀 Starting Web Application Server...")
    print("👉 Open your browser at: http://127.0.0.1:5000")
    print("💡 Press Ctrl + C in this terminal window to stop the server.\n")

    # Open browser automatically after 1.5 seconds
    threading.Timer(1.5, open_browser).start()

    # 2. Run Flask server
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)