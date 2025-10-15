import os
import asyncio
import time
import json
import subprocess
import re
import signal
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from dotenv import load_dotenv

class TelegramPDFExtractor:
    def __init__(self):
        load_dotenv()
        self.api_id = None
        self.api_hash = None
        self.channel_name = None
        self.start_date = None
        self.end_date = None
        self.pdf_folder = None
        self.calibre_cli_path = None
        self.enable_calibre_import = False
        self.calibre_library_path = None
        self.series_mapping = {}
        self.client = None
        
    def get_user_input(self):
        """Get user input for missing environment variables"""
        env_updated = False
        
        # Check for API ID
        self.api_id = os.getenv('API_ID')
        if not self.api_id:
            self.api_id = input("Enter your Telegram API ID: ").strip()
            self._update_env_file('API_ID', self.api_id)
            env_updated = True
            
        # Check for API Hash
        self.api_hash = os.getenv('API_HASH')
        if not self.api_hash:
            self.api_hash = input("Enter your Telegram API Hash: ").strip()
            self._update_env_file('API_HASH', self.api_hash)
            env_updated = True
            
        # Check for Channel Name
        self.channel_name = os.getenv('CHANNEL_NAME')
        if not self.channel_name:
            self.channel_name = input("Enter the channel name (without @): ").strip()
            self._update_env_file('CHANNEL_NAME', self.channel_name)
            env_updated = True
            
        # Check for PDF Folder
        self.pdf_folder = os.getenv('PDF_FOLDER')
        if not self.pdf_folder:
            self.pdf_folder = input("Enter PDF storage folder (default: downloads): ").strip()
            if not self.pdf_folder:
                self.pdf_folder = 'downloads'
            self._update_env_file('PDF_FOLDER', self.pdf_folder)
            env_updated = True
            
        # Check for Calibre settings
        self.calibre_cli_path = os.getenv('CALIBRE_CLI_PATH')
        if not self.calibre_cli_path:
            self.calibre_cli_path = input("Enter Calibre CLI path (default: /Applications/calibre.app/Contents/MacOS/calibredb): ").strip()
            if not self.calibre_cli_path:
                self.calibre_cli_path = '/Applications/calibre.app/Contents/MacOS/calibredb'
            self._update_env_file('CALIBRE_CLI_PATH', self.calibre_cli_path)
            env_updated = True
            
        enable_calibre_str = os.getenv('ENABLE_CALIBRE_IMPORT')
        if enable_calibre_str is None:
            enable_input = input("Enable Calibre import? (y/n, default: y): ").strip().lower()
            enable_calibre_str = 'true' if enable_input in ['', 'y', 'yes'] else 'false'
            self._update_env_file('ENABLE_CALIBRE_IMPORT', enable_calibre_str)
            env_updated = True
        self.enable_calibre_import = enable_calibre_str.lower() in ['true', 'yes', '1']
        
        if self.enable_calibre_import:
            self.calibre_library_path = os.getenv('CALIBRE_LIBRARY_PATH')
            if not self.calibre_library_path:
                self.calibre_library_path = input("Enter Calibre library path (default: ~/Documents/Calibre Library): ").strip()
                if not self.calibre_library_path:
                    self.calibre_library_path = '~/Documents/Calibre Library'
                self._update_env_file('CALIBRE_LIBRARY_PATH', self.calibre_library_path)
                env_updated = True
            
        # Check for Start Date
        start_date_str = os.getenv('START_DATE')
        
        # Handle TODAY keyword
        if start_date_str and start_date_str.upper() == 'TODAY':
            today = datetime.now()
            start_date_str = today.strftime('%Y-%m-%d')
            print(f"START_DATE=TODAY detected, using: {start_date_str}")
        elif not start_date_str:
            start_date_str = input("Enter start date (YYYY-MM-DD, press Enter for today): ").strip()
            if not start_date_str:
                # Default to today
                today = datetime.now()
                start_date_str = today.strftime('%Y-%m-%d')
                print(f"Using today's date: {start_date_str}")
            self._update_env_file('START_DATE', start_date_str)
            env_updated = True
        
        # Handle empty start date from .env (default to today)
        if not start_date_str:
            today = datetime.now()
            start_date_str = today.strftime('%Y-%m-%d')
            print(f"Empty start date, using today: {start_date_str}")
            
        self.start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        # Check for End Date
        end_date_str = os.getenv('END_DATE')
        
        # Handle TODAY keyword
        if end_date_str and end_date_str.upper() == 'TODAY':
            today = datetime.now()
            end_date_str = today.strftime('%Y-%m-%d')
            print(f"END_DATE=TODAY detected, using: {end_date_str}")
        elif not end_date_str:
            end_date_str = input("Enter end date (YYYY-MM-DD, press Enter for today): ").strip()
            if not end_date_str:
                # Default to today
                today = datetime.now()
                end_date_str = today.strftime('%Y-%m-%d')
                print(f"Using today's date: {end_date_str}")
            self._update_env_file('END_DATE', end_date_str)
            env_updated = True
            
        # Handle empty end date from .env (default to today)
        if not end_date_str:
            today = datetime.now()
            end_date_str = today.strftime('%Y-%m-%d')
            print(f"Empty end date, using today: {end_date_str}")
            
        self.end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        if env_updated:
            print("Environment variables updated in .env file")
            
        # Load series mapping
        self._load_series_mapping()
        
        # Check Calibre status if enabled
        if self.enable_calibre_import:
            self._check_calibre_status()
            
    def _update_env_file(self, key, value):
        """Update or add environment variable to .env file"""
        env_file = Path('.env')
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
            
        # Check if key already exists
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                key_found = True
                break
                
        # If key not found, add it
        if not key_found:
            lines.append(f'{key}={value}\n')
            
        with open(env_file, 'w') as f:
            f.writelines(lines)
            
    def _load_series_mapping(self):
        """Load series mapping from JSON file"""
        mapping_file = Path('series_mapping.json')
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    self.series_mapping = json.load(f)
                print(f"Loaded {len(self.series_mapping)} series mappings")
            except Exception as e:
                print(f"Warning: Could not load series mapping: {e}")
                self.series_mapping = {}
        else:
            print("Warning: series_mapping.json not found. Series detection disabled.")
            self.series_mapping = {}
            
    def _kill_calibre_processes(self):
        """Kill any running Calibre processes that might lock the database"""
        try:
            calibre_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'calibre' in proc.info['name'].lower():
                        calibre_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if calibre_processes:
                print(f"Found {len(calibre_processes)} Calibre processes running")
                kill_input = input("Kill Calibre processes to unlock database? (y/n, default: n): ").strip().lower()
                
                if kill_input in ['y', 'yes']:
                    for proc in calibre_processes:
                        try:
                            print(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                            proc.terminate()
                            proc.wait(timeout=5)
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            try:
                                proc.kill()
                            except psutil.NoSuchProcess:
                                pass
                    print("✓ Calibre processes terminated")
                    time.sleep(2)  # Wait for database locks to clear
                else:
                    print("Calibre processes left running - may cause database lock issues")
                    
        except Exception as e:
            print(f"Warning: Could not check/kill Calibre processes: {e}")
            
    def _clear_calibre_locks(self):
        """Clear Calibre database lock files"""
        try:
            library_path = os.path.expanduser(self.calibre_library_path)
            
            # Check if this is a network path
            is_network = self._is_network_path(library_path)
            if is_network:
                print("📡 Detected network library path (NAS)")
            
            lock_files = [
                Path(library_path) / 'metadata.db-wal',
                Path(library_path) / 'metadata.db-shm',
                Path(library_path) / 'metadata_db_prefs_backup.json.lock',
                Path(library_path) / '.calibre_lock'  # Additional lock file
            ]
            
            cleared_locks = []
            for lock_file in lock_files:
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        cleared_locks.append(lock_file.name)
                        if is_network:
                            # Extra delay for network filesystems
                            time.sleep(0.5)
                    except OSError as e:
                        print(f"Could not remove {lock_file.name}: {e}")
                        if is_network:
                            print(f"  Network filesystem may require manual removal")
            
            if cleared_locks:
                print(f"✓ Cleared lock files: {', '.join(cleared_locks)}")
                if is_network:
                    print("  Waiting for network filesystem sync...")
                    time.sleep(2)  # Extra wait for NAS
            
        except Exception as e:
            print(f"Warning: Could not clear lock files: {e}")
            
    def _is_network_path(self, path):
        """Check if path is on a network filesystem"""
        try:
            # Check for common network mount indicators
            if path.startswith(('/mnt/', '/media/', '/net/')):
                return True
            
            # Check filesystem type
            import subprocess
            result = subprocess.run(['df', '-T', path], capture_output=True, text=True)
            if result.returncode == 0:
                # Look for network filesystem types
                network_fs = ['nfs', 'cifs', 'smb', 'smbfs', 'fuse']
                for line in result.stdout.split('\n'):
                    for fs_type in network_fs:
                        if fs_type in line.lower():
                            return True
            
            return False
        except:
            return False
    
    def _handle_nas_database_lock(self):
        """Special handling for NAS database locks"""
        library_path = os.path.expanduser(self.calibre_library_path)
        
        print("🔧 Attempting NAS-specific database lock fixes...")
        
        # 1. Try to copy database locally for operations
        local_temp_path = Path('/tmp/calibre_temp_lib')
        try:
            print("  1. Attempting to create local temporary library...")
            if local_temp_path.exists():
                import shutil
                shutil.rmtree(local_temp_path)
            
            local_temp_path.mkdir(parents=True)
            
            # Copy essential database files
            db_files = ['metadata.db', 'metadata_db_prefs_backup.json']
            for db_file in db_files:
                src = Path(library_path) / db_file
                dst = local_temp_path / db_file
                if src.exists():
                    import shutil
                    shutil.copy2(src, dst)
                    print(f"    Copied {db_file} to local temp")
            
            # Test local library
            test_cmd = [self.calibre_cli_path, 'list', '--library-path', str(local_temp_path), '--limit', '1']
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("  ✓ Local temporary library works")
                return str(local_temp_path)
            else:
                print("  ✗ Local temporary library failed")
                
        except Exception as e:
            print(f"  ✗ Could not create local temporary library: {e}")
        
        # 2. Try using --with-library with network path
        print("  2. Trying --with-library option for network access...")
        
        # 3. Suggest manual solutions
        print("  3. Manual NAS solutions:")
        print(f"     - Check NAS network connectivity")
        print(f"     - Ensure no other devices are accessing the library")
        print(f"     - Try mounting NAS with different options (e.g., vers=3.0 for SMB)")
        print(f"     - Consider using Calibre Content Server instead")
        
        return None
    
    def _check_calibre_status(self):
        """Check if Calibre is running and provide guidance"""
        try:
            # Clear any stale lock files first
            self._clear_calibre_locks()
            
            # Try a simple list command to test Calibre access
            library_path = os.path.expanduser(self.calibre_library_path)
            test_cmd = [self.calibre_cli_path, 'list', '--library-path', library_path, '--limit', '1']
            
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=15)  # Longer timeout for NAS
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "Another calibre program" in error_msg or "calibre-server" in error_msg:
                    print("⚠ Warning: Calibre application is currently running")
                    print("  This may cause import issues. The script will try to work around this.")
                    print("  For best results, consider closing Calibre before running this script.")
                    print()
                elif "database is locked" in error_msg.lower() or "busyerror" in error_msg.lower():
                    print("⚠ Warning: Calibre database is locked")
                    
                    if self._is_network_path(library_path):
                        print("  📡 Detected NAS library - this is common with network storage")
                        self._handle_nas_database_lock()
                    else:
                        print("  This usually means Calibre is running or crashed previously")
                        self._kill_calibre_processes()
                        self._clear_calibre_locks()
                    print()
                elif "No such file or directory" in error_msg or "not found" in error_msg:
                    print(f"⚠ Warning: Calibre CLI not found at: {self.calibre_cli_path}")
                    print("  Please check your CALIBRE_CLI_PATH setting")
                    print()
                else:
                    print(f"⚠ Warning: Calibre test failed: {error_msg}")
                    print()
            else:
                print("✓ Calibre connection test successful")
                
        except subprocess.TimeoutExpired:
            print("⚠ Warning: Calibre connection test timed out (common with NAS)")
            print("  Consider using a local library or Calibre Content Server")
        except Exception as e:
            print(f"⚠ Warning: Could not test Calibre connection: {e}")
            
    def _extract_metadata_from_filename(self, filename):
        """Extract title, published date, and series from filename"""
        # Remove file extension
        name_without_ext = Path(filename).stem
        
        # Title is the filename without extension
        title = name_without_ext
        
        # Try to extract date from filename (various formats)
        published_date = None
        date_match = None
        
        # Extended date patterns including partial dates
        date_patterns = [
            # Full dates
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),  # YYYY-MM-DD
            (r'(\d{4}_\d{2}_\d{2})', '%Y_%m_%d'),  # YYYY_MM_DD
            (r'(\d{2}-\d{2}-\d{4})', '%d-%m-%Y'),  # DD-MM-YYYY
            (r'(\d{2}_\d{2}_\d{4})', '%d_%m_%Y'),  # DD_MM_YYYY
            # Partial dates (year-month only)
            (r'(\d{4}-\d{2})', '%Y-%m'),           # YYYY-MM
            (r'(\d{4}_\d{2})', '%Y_%m'),           # YYYY_MM
            # Year only
            (r'(\d{4})', '%Y'),                    # YYYY
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, name_without_ext)
            if match:
                date_str = match.group(1)
                date_match = match
                try:
                    if date_format == '%Y-%m' or date_format == '%Y_%m':
                        # Partial date: YYYY-MM or YYYY_MM -> use first day of month
                        parsed_date = datetime.strptime(date_str, date_format)
                        published_date = parsed_date.replace(day=1).date()
                    elif date_format == '%Y':
                        # Year only -> use January 1st
                        parsed_date = datetime.strptime(date_str, date_format)
                        published_date = parsed_date.replace(month=1, day=1).date()
                    else:
                        # Full date
                        published_date = datetime.strptime(date_str, date_format).date()
                    break
                except ValueError:
                    continue
        
        # If no date found in filename, use today's date
        if not published_date:
            published_date = datetime.now().date()
            print(f"    No date found in filename, using today: {published_date}")
        
        # Detect series from filename
        series = None
        
        # First, try to find series from predefined mapping
        for key, series_name in self.series_mapping.items():
            if key.lower() in filename.lower():
                series = series_name
                break
        
        # If no mapping found and we have a date match, extract series from filename before the date
        if not series and date_match:
            # Get the part of filename before the date
            before_date = name_without_ext[:date_match.start()].strip()
            
            # Remove common separators at the end
            before_date = before_date.rstrip('-_. ')
            
            if before_date:
                series = before_date
        elif not series:
            # If no date match and no mapping, try to extract series from the whole filename
            # Remove common document-like suffixes
            clean_name = name_without_ext
            for suffix in ['_document', '_doc', '_file', '_pdf']:
                if clean_name.lower().endswith(suffix):
                    clean_name = clean_name[:-len(suffix)]
                    break
            
            if clean_name and clean_name != name_without_ext:
                series = clean_name
                
        return title, published_date, series
        
    def _import_to_calibre(self, file_path, title, published_date, series, max_retries=3):
        """Import PDF to Calibre with metadata"""
        if not self.enable_calibre_import:
            return False
            
        for attempt in range(max_retries):
            try:
                # Expand user path
                library_path = os.path.expanduser(self.calibre_library_path)
                
                # Step 1: Try to add the book to Calibre
                add_cmd = [
                    self.calibre_cli_path,
                    'add',
                    str(file_path),
                    '--library-path', library_path,
                    '--title', title
                ]
                
                # Run the add command
                result = subprocess.run(add_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip()
                    
                    # Check for database lock errors
                    if "database is locked" in error_msg.lower() or "busyerror" in error_msg.lower():
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * (2 if self._is_network_path(library_path) else 1)
                            print(f"    ⚠ Database locked, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                            
                            if self._is_network_path(library_path):
                                print(f"    📡 NAS detected - using longer delays and --with-library option")
                                # For NAS, try with --with-library option
                                add_cmd = [
                                    self.calibre_cli_path,
                                    'add',
                                    str(file_path),
                                    '--with-library', library_path,
                                    '--title', title
                                ]
                            
                            self._clear_calibre_locks()
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    ✗ Database still locked after {max_retries} attempts")
                            if self._is_network_path(library_path):
                                print(f"    💡 NAS solutions:")
                                print(f"       - Check network connectivity to NAS")
                                print(f"       - Ensure no other devices are using the library")
                                print(f"       - Try: calibre-server --library-path '{library_path}'")
                                print(f"       - Consider copying library locally temporarily")
                            else:
                                print(f"    💡 Try: sudo pkill -f calibre && rm -f '{library_path}/metadata.db-*'")
                            return False
                    
                    # Check if it's the "another calibre program running" error
                    elif "Another calibre program" in error_msg or "calibre-server" in error_msg:
                        print(f"    ⚠ Calibre is running - trying with --with-library option")
                        
                        # Try with --with-library to connect through running Calibre
                        add_cmd_with_server = [
                            self.calibre_cli_path,
                            'add',
                            str(file_path),
                            '--with-library', library_path,
                            '--title', title
                        ]
                        
                        result = subprocess.run(add_cmd_with_server, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode != 0:
                            print(f"    ✗ Calibre import failed (even with --with-library): {result.stderr}")
                            print(f"    💡 Try closing Calibre application and running again")
                            return False
                    else:
                        print(f"    ✗ Calibre add failed: {error_msg}")
                        return False
                
                # Extract book ID from output (usually in format "Added book ids: 123")
                book_id = None
                for line in result.stdout.split('\n'):
                    if 'Added book ids:' in line:
                        try:
                            book_id = line.split(':')[1].strip()
                            break
                        except:
                            pass
                
                if not book_id:
                    print(f"    ✓ Added to Calibre: {title} (couldn't get ID for metadata)")
                    return True
                
                # Step 2: Set metadata if we have additional info
                if published_date or series:
                    metadata_updates = []
                    
                    if published_date:
                        metadata_updates.extend(['--field', f'pubdate:{published_date.isoformat()}'])
                    
                    if series:
                        metadata_updates.extend(['--field', f'series:{series}'])
                    
                    if metadata_updates:
                        # Use the same connection method for metadata
                        library_option = '--with-library' if 'with-library' in ' '.join(add_cmd) else '--library-path'
                        
                        metadata_cmd = [
                            self.calibre_cli_path,
                            'set_metadata',
                            library_option, library_path,
                            book_id
                        ] + metadata_updates
                        
                        metadata_result = subprocess.run(metadata_cmd, capture_output=True, text=True, timeout=30)
                        
                        if metadata_result.returncode != 0:
                            print(f"    ⚠ Added to Calibre but metadata update failed: {title}")
                            print(f"      Error: {metadata_result.stderr}")
                        else:
                            print(f"    ✓ Imported to Calibre with metadata: {title}")
                            if series:
                                print(f"      Series: {series}")
                            if published_date:
                                print(f"      Published: {published_date}")
                    else:
                        print(f"    ✓ Added to Calibre: {title}")
                else:
                    print(f"    ✓ Added to Calibre: {title}")
                
                return True
                    
            except subprocess.TimeoutExpired:
                print(f"    ✗ Calibre import timeout for: {title}")
                if attempt < max_retries - 1:
                    print(f"    Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                return False
            except Exception as e:
                print(f"    ✗ Calibre import error: {e}")
                if attempt < max_retries - 1:
                    print(f"    Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                return False
        
        return False
            
    async def connect_to_telegram(self):
        """Initialize and connect to Telegram client"""
        self.client = TelegramClient('session', int(self.api_id), self.api_hash)
        await self.client.start()
        print("Connected to Telegram successfully!")
        
    async def extract_pdfs(self):
        """Extract PDF files from the specified channel"""
        try:
            # Get the channel entity
            channel = await self.client.get_entity(self.channel_name)
            print(f"Found channel: {channel.title}")
            
            # Create PDF storage directory
            downloads_dir = Path(self.pdf_folder)
            downloads_dir.mkdir(exist_ok=True)
            
            # First pass: collect all PDF messages
            print(f"Scanning for PDF files from {self.start_date.date()} to {self.end_date.date()}...")
            pdf_messages = []
            
            # Use offset_date to start from a day after end_date to ensure we capture all messages
            # Then iterate backwards through all messages until we go past start_date
            from datetime import timedelta
            search_start = self.end_date + timedelta(days=1)
            
            message_count = 0
            async for message in self.client.iter_messages(
                channel, 
                offset_date=search_start
            ):
                message_count += 1
                
                # Stop if we've gone past our start date
                if message.date.date() < self.start_date.date():
                    break
                    
                # Check if message is within our date range
                if self.start_date.date() <= message.date.date() <= self.end_date.date():
                    # Check if message has a document
                    if message.media and isinstance(message.media, MessageMediaDocument):
                        document = message.media.document
                        
                        # Check if it's a PDF file
                        if document.mime_type == 'application/pdf':
                            pdf_messages.append(message)
                            
                # Show progress every 100 messages
                if message_count % 100 == 0:
                    print(f"  Scanned {message_count} messages, found {len(pdf_messages)} PDFs so far...")
            
            print(f"Finished scanning {message_count} messages")
            
            total_pdfs = len(pdf_messages)
            print(f"Found {total_pdfs} PDF files to download")
            
            if total_pdfs == 0:
                print("No PDF files found in the specified date range")
                return
            
            # Download PDFs with progress tracking
            pdf_count = 0
            start_time = time.time()
            
            for i, message in enumerate(pdf_messages, 1):
                document = message.media.document
                
                # Get original filename or create one
                filename = None
                for attr in document.attributes:
                    if hasattr(attr, 'file_name'):
                        filename = attr.file_name
                        break
                        
                if not filename:
                    filename = f"document_{message.id}.pdf"
                    
                # Create month folder
                month_folder = downloads_dir / f"{message.date.year}-{message.date.month:02d}"
                month_folder.mkdir(exist_ok=True)
                
                # Check if file already exists
                file_path = month_folder / filename
                if file_path.exists():
                    print(f"[{i}/{total_pdfs}] File exists: {filename}")
                    # Still try to import to Calibre if enabled
                    if self.enable_calibre_import:
                        title, published_date, series = self._extract_metadata_from_filename(filename)
                        self._import_to_calibre(file_path, title, published_date, series)
                    pdf_count += 1
                    continue
                
                # Download the file with progress
                file_size_mb = document.size / (1024 * 1024) if document.size else 0
                print(f"[{i}/{total_pdfs}] Downloading: {filename} ({file_size_mb:.1f}MB)")
                
                download_start = time.time()
                await self.client.download_media(message, file_path)
                download_time = time.time() - download_start
                
                pdf_count += 1
                
                # Show download speed and ETA
                if download_time > 0:
                    speed_mbps = file_size_mb / download_time
                    elapsed = time.time() - start_time
                    avg_time_per_file = elapsed / i
                    eta_seconds = (total_pdfs - i) * avg_time_per_file
                    eta_minutes = eta_seconds / 60
                    
                    print(f"    ✓ Downloaded in {download_time:.1f}s ({speed_mbps:.1f}MB/s) - ETA: {eta_minutes:.1f}min")
                
                # Import to Calibre if enabled
                if self.enable_calibre_import:
                    title, published_date, series = self._extract_metadata_from_filename(filename)
                    self._import_to_calibre(file_path, title, published_date, series)
                
                # Small delay to be respectful to Telegram's servers
                await asyncio.sleep(0.5)
                        
            total_time = time.time() - start_time
            print(f"\n✅ Successfully downloaded {pdf_count} PDF files in {total_time/60:.1f} minutes!")
            
        except Exception as e:
            print(f"Error extracting PDFs: {e}")
            
    async def run(self):
        """Main execution method"""
        print("Telegram PDF Extractor")
        print("=" * 30)
        
        # Get user input for missing environment variables
        self.get_user_input()
        
        # Connect to Telegram
        await self.connect_to_telegram()
        
        # Extract PDFs
        await self.extract_pdfs()
        
        # Disconnect
        await self.client.disconnect()
        print("Disconnected from Telegram")

async def main():
    extractor = TelegramPDFExtractor()
    await extractor.run()

if __name__ == "__main__":
    asyncio.run(main())