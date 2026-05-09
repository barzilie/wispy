#!/usr/bin/env python3
"""
WiSpy Launcher
Starts both Flask backend and React frontend
"""

import os
import sys
import subprocess
import time
import signal

def check_dependencies():
    """Check if required dependencies are installed"""
    # Check virtual environment
    if not os.path.exists('.venv'):
        print("❌ Error: Virtual environment not found")
        print("Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)

    # Check npm
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: npm not found. Install Node.js first.")
        sys.exit(1)

    # Check React dependencies
    if not os.path.exists('web/frontend/node_modules'):
        print("⚠️  React dependencies not found. Installing...")
        subprocess.run(['npm', 'install'], cwd='web/frontend', check=True)

def main():
    print("=" * 60)
    print("🕵️  Starting WiSpy Network Surveillance System")
    print("=" * 60)

    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Check dependencies
    check_dependencies()

    processes = []

    try:
        # Start Flask backend
        print("\n📡 Starting Flask backend...")
        python_exe = os.path.join('.venv', 'bin', 'python')
        flask_process = subprocess.Popen(
            [python_exe, 'web/app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(flask_process)

        # Wait for Flask to start
        print("⏳ Waiting for Flask to start...")
        time.sleep(3)

        # Start React frontend
        print("⚛️  Starting React frontend...")
        react_process = subprocess.Popen(
            ['npm', 'start'],
            cwd='web/frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(react_process)

        print("\n" + "=" * 60)
        print("✅ WiSpy Started!")
        print("=" * 60)
        print("Flask Backend:  http://localhost:5000")
        print("React Frontend: http://localhost:3001")
        print("\nPress Ctrl+C to stop both servers")
        print("=" * 60 + "\n")

        # Wait for both processes
        for process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping WiSpy...")
        for process in processes:
            process.terminate()

        # Wait for graceful shutdown
        time.sleep(2)

        # Force kill if still running
        for process in processes:
            if process.poll() is None:
                process.kill()

        print("✅ WiSpy stopped.")
        sys.exit(0)

if __name__ == '__main__':
    main()
