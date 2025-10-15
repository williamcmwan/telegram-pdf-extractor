#!/bin/bash

# Setup script for Telegram PDF Extractor cron job

echo "Setting up daily cron job for Telegram PDF Extractor..."

# Get the current directory (project directory)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the cron job entry
CRON_JOB="0 12 * * * $PROJECT_DIR/run_extractor.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$PROJECT_DIR/run_extractor.sh"; then
    echo "Cron job already exists!"
    echo "Current cron jobs:"
    crontab -l | grep "$PROJECT_DIR/run_extractor.sh"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added successfully!"
    echo "The PDF extractor will run daily at 12:00 PM (noon)"
    echo ""
    echo "Cron job entry:"
    echo "$CRON_JOB"
fi

echo ""
echo "To verify the cron job was added, run:"
echo "crontab -l"
echo ""
echo "To remove the cron job later, run:"
echo "crontab -e"
echo "Then delete the line containing: $PROJECT_DIR/run_extractor.sh"
echo ""
echo "Logs will be stored in: $PROJECT_DIR/logs/"