#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Navigate to project root
cd "$PROJECT_ROOT"

# Check if we are running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo)"
  exit 1
fi

echo "Starting Pi AI Keyboard in background..."
echo "Logs will be written to: $PROJECT_ROOT/keyboard.log"

# Run with nohup to ignore hangup signals (when SSH disconnects)
# Redirect stdout and stderr to log file
nohup .venv/bin/python3 src/main.py > keyboard.log 2>&1 &

echo "Started! PID: $!"
echo "Run 'tail -f keyboard.log' to see output."