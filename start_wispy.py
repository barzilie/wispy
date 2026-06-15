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
    # venv check
    if not os.path.exists('.venv'):
        print("error: no venv found")
        print("run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)

    # need npm for the react app
    try:
        subprocess.run(['npm', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("error: npm not found, install node.js first")
        sys.exit(1)

    # install frontend deps if missing
    if not os.path.exists('web/frontend/node_modules'):
        print("react deps missing, installing...")
        subprocess.run(['npm', 'install'], cwd='web/frontend', check=True)

def main():
    print("=" * 60)
    print("starting wispy")
    print("=" * 60)

    # cd to repo root
    proj_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(proj_root)

    check_dependencies()

    procs = []

    try:
        # flask first
        print("\nstarting flask backend...")
        py_bin = os.path.join('.venv', 'bin', 'python')
        flask_proc = subprocess.Popen(
            [py_bin, 'web/app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        procs.append(flask_proc)

        print("waiting a few sec for flask...")
        time.sleep(3)

        # then react
        print("starting react frontend...")
        react_proc = subprocess.Popen(
            ['npm', 'start'],
            cwd='web/frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        procs.append(react_proc)

        print("\n" + "=" * 60)
        print("wispy is up")
        print("=" * 60)
        print("flask:  http://localhost:5000")
        print("react:  http://localhost:3001")
        print("\nctrl+c to stop both")
        print("=" * 60 + "\n")

        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\n\nstopping wispy...")
        for p in procs:
            p.terminate()

        time.sleep(2)

        # kill if they didnt exit cleanly
        for p in procs:
            if p.poll() is None:
                p.kill()

        print("done, wispy stopped")
        sys.exit(0)

if __name__ == '__main__':
    main()
