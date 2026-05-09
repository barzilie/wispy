#!/bin/bash

# WiSpy Startup Script
# Starts both Flask backend and React frontend

echo "============================================================"
echo "🕵️  Starting WiSpy Network Surveillance System"
echo "============================================================"

# Check if we're in the right directory
if [ ! -f "web/app.py" ]; then
    echo "❌ Error: Must run from wispy project root"
    exit 1
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found. Install Node.js first."
    exit 1
fi

# Check if React dependencies are installed
if [ ! -d "web/frontend/node_modules" ]; then
    echo "⚠️  React dependencies not found. Installing..."
    cd web/frontend
    npm install
    cd ../..
fi

echo ""
echo "Starting Flask backend..."
source .venv/bin/activate
python web/app.py &
FLASK_PID=$!

echo "Waiting for Flask to start..."
sleep 3

echo "Starting React frontend..."
cd web/frontend
npm start &
REACT_PID=$!
cd ../..

echo ""
echo "============================================================"
echo "✅ WiSpy Started!"
echo "============================================================"
echo "Flask Backend:  http://localhost:5000"
echo "React Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "============================================================"

# Wait for both processes
wait $FLASK_PID $REACT_PID
