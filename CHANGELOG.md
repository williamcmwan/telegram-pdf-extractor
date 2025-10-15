# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-12-15

### Added
- **Telegram PDF Extractor**: Download PDFs from Telegram channels with date filtering
- **Folder Importer**: Import existing PDFs from local folders
- **Calibre Integration**: Automatic import with metadata extraction
- **Smart Metadata Extraction**:
  - Title from filename
  - Published date from filename (full, partial, or fallback to today)
  - Series detection from mapping file or filename
- **Series Mapping**: JSON-based series name mapping with fallback extraction
- **Date Handling**: Support for various date formats (YYYY-MM-DD, partial dates, year-only)
- **Automated Daily Runs**: Cron job setup with logging
- **NAS Support**: Special handling for network storage database locks
- **Ubuntu/Linux Optimizations**: Database lock handling and process management

### Features
- **Dual Source Support**: Both Telegram channels and local folders
- **Flexible Date Processing**: TODAY keyword, partial dates, automatic fallbacks
- **Progress Tracking**: Real-time download/import progress with ETA
- **Error Recovery**: Retry logic with exponential backoff
- **Network Storage**: Automatic NAS detection and optimization
- **Calibre Conflict Resolution**: Automatic handling of running Calibre instances
- **Comprehensive Logging**: Detailed logs with automatic cleanup

### Documentation
- Complete setup and usage guides
- Ubuntu-specific troubleshooting
- NAS setup and optimization guide
- Cron job automation instructions
- Series mapping examples

### Technical Details
- **Languages**: Python 3.7+
- **Dependencies**: telethon, python-dotenv, psutil
- **Platforms**: macOS, Ubuntu/Linux
- **Storage**: Local filesystem, NAS (NFS, SMB/CIFS)
- **Integration**: Calibre library management