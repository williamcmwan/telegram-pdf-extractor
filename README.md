# Telegram PDF Extractor

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/yourusername/telegram-pdf-extractor)

A comprehensive solution to extract PDF files from Telegram channels and import existing PDFs with automatic Calibre integration and intelligent metadata extraction.

## 🚀 Features

### Core Functionality
- **Dual Source Support**: Extract from Telegram channels OR import from local folders
- **Smart Date Filtering**: TODAY keyword, date ranges, partial dates with intelligent fallbacks
- **Automatic Organization**: Files organized by month with customizable folder structure
- **Progress Tracking**: Real-time progress with download speeds and ETA calculations

### Calibre Integration
- **Automatic Import**: Seamless integration with Calibre library management
- **Metadata Extraction**: Title, published date, and series from filename
- **Series Mapping**: JSON-based mapping with intelligent fallback detection
- **Conflict Resolution**: Handles running Calibre instances and database locks

### Advanced Features
- **NAS Support**: Special handling for network storage with database lock resolution
- **Automated Scheduling**: Cron job setup for daily automated runs
- **Error Recovery**: Retry logic with exponential backoff for network issues
- **Cross-Platform**: Full support for macOS and Ubuntu/Linux systems

## 📦 Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Get Telegram API credentials:**
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Note down your `api_id` and `api_hash`

3. **Install Calibre (optional but recommended):**
   - macOS: Download from https://calibre-ebook.com/
   - Ubuntu: `sudo apt install calibre` or use official binary

## 🎯 Quick Start

### Telegram Channel Extraction
```bash
python main.py
```

### Local Folder Import
```bash
python folder_importer.py
```

## ⚙️ Configuration

### Environment Variables (.env)

The application uses these environment variables:

```bash
# Telegram API (required for main.py)
API_ID=your_api_id_here
API_HASH=your_api_hash_here
CHANNEL_NAME=channel_name_without_at_symbol

# Storage settings
PDF_FOLDER=downloads
SOURCE_FOLDER=~/Downloads/PDFs  # For folder importer

# Date range (use "TODAY", leave empty, or YYYY-MM-DD)
START_DATE=TODAY
END_DATE=TODAY

# Calibre integration
CALIBRE_CLI_PATH=/Applications/calibre.app/Contents/MacOS/calibredb
ENABLE_CALIBRE_IMPORT=true
CALIBRE_LIBRARY_PATH=~/Documents/Calibre Library
```

### First Run Setup

On first run, the application will prompt you for missing configuration:
- API credentials (Telegram extractor only)
- Channel name (Telegram extractor only)
- Source folder (Folder importer only)
- PDF storage folder
- Calibre settings
- Date range (or press Enter for today)

All values are saved to `.env` file for future runs.

## 📅 Date Handling

### Supported Date Formats
- **Full dates**: `2024-01-15`, `15-01-2024`, `2024_01_15`
- **Partial dates**: `2025-10` → Published: October 1, 2025
- **Year only**: `2024` → Published: January 1, 2024
- **No date**: Uses today's date as fallback

### Date Options
- **Leave empty**: Will prompt for input (press Enter for today)
- **Set to `TODAY`**: Automatically uses current date without prompting
- **Set specific date**: Use YYYY-MM-DD format

## 📚 Calibre Integration

### Setup Calibre Integration

1. **Configure in .env:**
```bash
CALIBRE_CLI_PATH=/Applications/calibre.app/Contents/MacOS/calibredb  # macOS
# CALIBRE_CLI_PATH=/usr/bin/calibredb  # Ubuntu
ENABLE_CALIBRE_IMPORT=true
CALIBRE_LIBRARY_PATH=~/Documents/Calibre Library
```

### Metadata Extraction

The application automatically extracts:
- **Title**: Filename without extension
- **Published Date**: Date from filename with smart fallbacks
- **Series**: Matched from `series_mapping.json` or extracted from filename

### Series Mapping

Edit `series_mapping.json` to map filename patterns to series names:
```json
{
  "MoneyWeek": "MoneyWeek",
  "Economist": "The Economist",
  "Forbes": "Forbes Magazine",
  "經濟日報": "經濟日報"
}
```

**Series Detection Logic:**
1. **First**: Checks `series_mapping.json` for exact matches
2. **Fallback**: If no mapping found, uses filename before the date as series

**Examples:**
- `MoneyWeek-2024-01-15.pdf` → Series: "MoneyWeek", Published: 2024-01-15
- `經濟日報-2025-09-13.pdf` → Series: "經濟日報", Published: 2025-09-13
- `My Custom Publication-2024-01-15.pdf` → Series: "My Custom Publication", Published: 2024-01-15

## 🤖 Automated Daily Runs

### Quick Setup
1. **Configure for daily runs in .env:**
```bash
START_DATE=TODAY
END_DATE=TODAY
```

2. **Run the cron setup:**
```bash
./setup_cron.sh
```

### Manual Cron Setup
```bash
# Open crontab editor
crontab -e

# Add this line (replace path with your actual path)
0 12 * * * /path/to/your/tg-pdf-extractor/run_extractor.sh
```

### Cron Schedule Examples
- **Every day at 9 AM:** `0 9 * * *`
- **Every day at 6 PM:** `0 18 * * *`
- **Weekdays only at noon:** `0 12 * * 1-5`
- **Every 6 hours:** `0 */6 * * *`

### Logs and Monitoring
- **Log location:** `logs/extractor_YYYYMMDD_HHMMSS.log`
- **Log retention:** Automatically keeps last 30 days
- **View latest log:** `tail -f logs/extractor_*.log`

## 📁 Folder Importer

Import existing PDF files from local folders with the same metadata extraction.

### Features
- Import PDFs from any local folder (with recursive subdirectory support)
- Same metadata extraction and series mapping as Telegram extractor
- Progress tracking and statistics
- Handles Calibre conflicts automatically

### Usage
```bash
python folder_importer.py
# Enter folder: ~/Downloads/PDFs
# Recursive search: y
# Processes all PDFs in folder and subfolders
```

### Example Output
```
PDF Folder Importer
==============================
Found 156 PDF files to process

[1/156] Processing: MoneyWeek-2024-01-15.pdf
    Title: MoneyWeek-2024-01-15
    Published: 2024-01-15
    Series: MoneyWeek
    ✓ Imported to Calibre with metadata

✅ Processing completed in 3.2 minutes!
   📚 Imported: 154
   ❌ Failed: 2
```

## 🛠️ Troubleshooting

### Ubuntu/Linux Issues

#### Database Lock Errors (`apsw.BusyError: database is locked`)

**Automatic Solutions (Built-in):**
- Lock file cleanup: Removes stale lock files automatically
- Process detection: Finds running Calibre processes
- Retry logic: Attempts import up to 3 times with exponential backoff
- User prompts: Asks permission to kill Calibre processes

**Manual Solutions:**
```bash
# Kill Calibre processes
sudo pkill -f calibre

# Remove lock files
rm -f ~/Documents/Calibre\ Library/metadata.db-*

# One-liner fix
sudo pkill -f calibre && rm -f ~/Documents/Calibre\ Library/metadata.db-*
```

#### Installation Issues
```bash
# Update and install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-dev build-essential

# Install Calibre (official binary - recommended)
sudo -v && wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin

# Or via package manager
sudo apt install calibre

# Find Calibre CLI path
which calibredb
find /usr -name calibredb 2>/dev/null
find /opt -name calibredb 2>/dev/null
```

#### Permission Issues
```bash
# Fix library permissions
chmod -R 755 ~/Documents/Calibre\ Library/
chown -R $USER:$USER ~/Documents/Calibre\ Library/

# Make scripts executable
chmod +x main.py folder_importer.py run_extractor.sh setup_cron.sh
```

### NAS (Network Storage) Issues

#### Why NAS Causes Problems
SQLite databases (like Calibre's) don't work well over network filesystems because:
- File locking mechanisms differ between network protocols
- Network latency causes timeout issues
- Concurrent access from multiple devices creates conflicts
- Cache inconsistencies between local and network storage

#### Automatic NAS Detection
The scripts automatically detect NAS paths and apply special handling:
- Longer timeouts (15s instead of 10s)
- Extended delays for network filesystem sync
- Automatic use of `--with-library` option
- Clear additional network-specific lock files

#### NAS Solutions

**Option 1: Calibre Content Server (Recommended)**
```bash
# On your NAS or dedicated machine
calibre-server --library-path /path/to/nas/library --port 8080 --daemonize

# Update .env to use Content Server
CALIBRE_LIBRARY_PATH=http://nas-ip:8080
```

**Option 2: Local Sync Approach**
```bash
# Create sync script
#!/bin/bash
NAS_PATH="/mnt/nas/calibre-library"
LOCAL_PATH="$HOME/calibre-library-local"

# Sync from NAS to local
rsync -av --delete "$NAS_PATH/" "$LOCAL_PATH/"

# Run extractor
python3 main.py

# Sync back to NAS
rsync -av --delete "$LOCAL_PATH/" "$NAS_PATH/"

# Use local path in .env
CALIBRE_LIBRARY_PATH=~/calibre-library-local
```

**Option 3: Optimized Direct NAS**
```bash
# Better mount options for SMB/CIFS
sudo mount -t cifs //nas-ip/share /mnt/nas -o vers=3.0,cache=strict

# For NFS
sudo mount -t nfs nas-ip:/path /mnt/nas -o vers=4,hard,intr

# Use NAS path in .env (scripts will auto-optimize)
CALIBRE_LIBRARY_PATH=/mnt/nas/calibre-library
```

#### NAS Troubleshooting
```bash
# Test connectivity
ping nas-ip
telnet nas-ip 445  # SMB
telnet nas-ip 2049 # NFS

# Check mount status
mount | grep nas
df -h /mnt/nas

# Manual lock cleanup
rm -f /mnt/nas/calibre-library/metadata.db-*
```

### Common Issues

#### "Another calibre program is running"
- Close the main Calibre application before running the script
- Script will automatically try using `--with-library` option
- For automated runs, ensure Calibre is not running

#### "Calibre CLI not found"
- Verify `CALIBRE_CLI_PATH` points to the correct location
- Common paths:
  - macOS: `/Applications/calibre.app/Contents/MacOS/calibredb`
  - Ubuntu: `/usr/bin/calibredb` or `/opt/calibre/calibredb`

#### "No such file or directory"
- Check file paths in .env
- Use absolute paths instead of ~ shortcuts
- Verify files exist: `ls -la /path/to/file`

#### "Permission denied"
- Run with appropriate user permissions
- Check file/directory ownership
- Don't run as root unless necessary

### Performance Optimization

#### For Large Libraries
- Increase timeout values if needed
- Add more delay between operations
- Process files in smaller batches

#### For Slow Systems
- Reduce concurrent operations
- Increase retry delays
- Use SSD storage for Calibre library

## 📁 Project Structure

```
telegram-pdf-extractor/
├── main.py                     # Telegram channel extractor
├── folder_importer.py          # Local folder importer
├── requirements.txt            # Python dependencies
├── series_mapping.json         # Series name mappings
├── .env.example               # Environment variables template
├── run_extractor.sh           # Automated run script
├── setup_cron.sh              # Cron job setup
├── .gitignore                 # Git ignore rules
├── README.md                  # This comprehensive guide
├── LICENSE                    # MIT License
└── CHANGELOG.md               # Version history
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
git clone https://github.com/yourusername/telegram-pdf-extractor.git
cd telegram-pdf-extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram API integration
- [Calibre](https://calibre-ebook.com/) for ebook library management
- Community contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/telegram-pdf-extractor/issues)
- **Documentation**: This README contains comprehensive guides
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/telegram-pdf-extractor/discussions)