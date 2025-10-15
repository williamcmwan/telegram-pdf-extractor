#!/bin/bash

# Telegram PDF Extractor Daily Runner
# This script runs the PDF extractor and logs the output

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate log filename with current date
LOG_FILE="logs/extractor_$(date +%Y%m%d_%H%M%S).log"

# Run the Python script and capture output
echo "Starting Telegram PDF Extractor at $(date)" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment" >> "$LOG_FILE"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated virtual environment" >> "$LOG_FILE"
fi

# Run the extractor
python3 main.py >> "$LOG_FILE" 2>&1

# Log completion
echo "=========================================" >> "$LOG_FILE"
echo "Completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Keep only last 30 days of logs
find logs -name "extractor_*.log" -mtime +30 -delete

echo "PDF extraction completed. Check $LOG_FILE for details."