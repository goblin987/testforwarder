"""
TgCF Pro - Smart Bump Service Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enterprise-grade automated advertising and campaign management system.
Provides intelligent scheduling, multi-target broadcasting, and comprehensive
performance analytics for business communication automation.

Features:
- Advanced campaign scheduling with multiple patterns
- Multi-account campaign management
- Real-time performance tracking and analytics
- Intelligent retry mechanisms and error handling
- Professional campaign templates and A/B testing

Author: TgCF Pro Team
License: MIT
Version: 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from telethon import TelegramClient
from database import Database
import json
import threading
import traceback

# Configure structured logging
logger = logging.getLogger(__name__)

class StructuredLogger:
    """Enhanced logging with structured data and context"""
    
    @staticmethod
    def log_operation(operation: str, user_id: int = None, campaign_id: int = None, 
                     account_id: int = None, success: bool = None, details: str = None):
        """Log operation with structured context"""
        context = {
            'operation': operation,
            'user_id': user_id,
            'campaign_id': campaign_id,
            'account_id': account_id,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        if success is True:
            logger.info(f"✅ {operation} completed successfully", extra=context)
        elif success is False:
            logger.error(f"❌ {operation} failed", extra=context)
        else:
            logger.info(f"🔄 {operation} in progress", extra=context)
    
    @staticmethod
    def log_error(operation: str, error: Exception, user_id: int = None, 
                 campaign_id: int = None, account_id: int = None):
        """Log error with full context and stack trace"""
        context = {
            'operation': operation,
            'user_id': user_id,
            'campaign_id': campaign_id,
            'account_id': account_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'stack_trace': traceback.format_exc()
        }
        
        logger.error(f"💥 {operation} failed: {error}", extra=context, exc_info=True)
    
    @staticmethod
    def log_performance(operation: str, duration: float, user_id: int = None, 
                       campaign_id: int = None, details: str = None):
        """Log performance metrics"""
        context = {
            'operation': operation,
            'duration_seconds': duration,
            'user_id': user_id,
            'campaign_id': campaign_id,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        if duration > 10:
            logger.warning(f"⚠️ {operation} took {duration:.2f}s (slow)", extra=context)
        else:
            logger.info(f"⏱️ {operation} completed in {duration:.2f}s", extra=context)

@dataclass
class AdCampaign:
    """Represents an advertising campaign"""
    id: int
    user_id: int
    account_id: int
    campaign_name: str
    ad_content: str
    target_chats: List[str]
    schedule_type: str  # 'once', 'daily', 'weekly', 'custom'
    schedule_time: str  # Format: "HH:MM" or cron-like
    is_active: bool
    created_at: str
    last_run: Optional[str] = None
    total_sends: int = 0

class BumpService:
    """Service for managing automated ad bumping/posting"""
    
    def __init__(self):
        self.db = Database()
        self.active_campaigns = {}
        self.scheduler_thread = None
        self.is_running = False
        self.telegram_clients = {}
        self.client_init_semaphore = threading.Semaphore(1)  # Thread-safe semaphore
        self.temp_files = set()  # Track temporary files for cleanup
        self.init_bump_database()
    
    def _get_db_connection(self):
        """Get database connection with proper configuration"""
        return self.db._get_connection()
    
    def _register_temp_file(self, file_path: str):
        """Register a temporary file for cleanup"""
        self.temp_files.add(file_path)
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up a temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {e}")
        finally:
            self.temp_files.discard(file_path)
    
    def cleanup_all_resources(self):
        """Clean up all resources (clients, temp files, etc.)"""
        logger.info("Starting comprehensive resource cleanup...")
        
        # Clean up all Telegram clients
        for account_id, client in list(self.telegram_clients.items()):
            try:
                if hasattr(client, 'disconnect'):
                    # Run disconnect in a separate thread to avoid blocking
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(self._sync_disconnect_client, client)
                        future.result(timeout=5)  # 5 second timeout
                logger.info(f"Disconnected client for account {account_id}")
            except Exception as e:
                logger.error(f"Error disconnecting client {account_id}: {e}")
            finally:
                del self.telegram_clients[account_id]
        
        # Clean up all temporary files
        for temp_file in list(self.temp_files):
            self._cleanup_temp_file(temp_file)
        
        # Clean up any remaining session files
        self._cleanup_session_files()
        
        logger.info("Resource cleanup completed")
    
    def _sync_disconnect_client(self, client):
        """Synchronously disconnect a client"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client.disconnect())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to disconnect client: {e}")
    
    def _cleanup_session_files(self):
        """Clean up all session files"""
        import glob
        try:
            # Find all session files
            session_files = glob.glob("bump_session_*.session")
            for session_file in session_files:
                try:
                    if os.path.exists(session_file):
                        os.remove(session_file)
                        logger.debug(f"Cleaned up session file: {session_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up session file {session_file}: {e}")
        except Exception as e:
            logger.error(f"Error during session file cleanup: {e}")
    
    def _format_buttons_as_text(self, telethon_buttons):
        """Format Telethon buttons as text for fallback display with enhanced styling"""
        if not telethon_buttons:
            return ""
        
        button_text = "🔗 **Links:**\n"
        for row in telethon_buttons:
            for button in row:
                if hasattr(button, 'text') and hasattr(button, 'url'):
                    # Enhanced formatting to look more like inline buttons
                    button_text += f"🔸 **{button.text}**\n   {button.url}\n\n"
        
        return button_text.strip()
    
    def _add_buttons_to_text(self, text, telethon_buttons):
        """Add button text to message text"""
        if not text:
            return ""
        
        if telethon_buttons:
            button_text = self._format_buttons_as_text(telethon_buttons)
            if button_text:
                return text + "\n\n" + button_text
        
        return text
    
    def init_bump_database(self):
        """Initialize bump service database tables"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Ad campaigns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ad_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    account_id INTEGER,
                    campaign_name TEXT,
                    ad_content TEXT,
                    target_chats TEXT,
                    schedule_type TEXT,
                    schedule_time TEXT,
                    buttons TEXT,
                    target_mode TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    total_sends INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (account_id) REFERENCES telegram_accounts (id)
                )
            ''')
            
            # Add buttons column to existing tables if it doesn't exist
            cursor.execute("PRAGMA table_info(ad_campaigns)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'buttons' not in columns:
                cursor.execute('ALTER TABLE ad_campaigns ADD COLUMN buttons TEXT')
                logger.info("Added buttons column to ad_campaigns table")
            if 'target_mode' not in columns:
                cursor.execute('ALTER TABLE ad_campaigns ADD COLUMN target_mode TEXT')
                logger.info("Added target_mode column to ad_campaigns table")
            
            # Update existing campaigns with default button data and ensure they're active
            cursor.execute("UPDATE ad_campaigns SET buttons = ? WHERE buttons IS NULL", (json.dumps([{"text": "Shop Now", "url": "https://t.me/testukassdfdds"}]),))
            cursor.execute("UPDATE ad_campaigns SET target_mode = 'all_groups' WHERE target_mode IS NULL")
            cursor.execute("UPDATE ad_campaigns SET is_active = 1 WHERE is_active IS NULL OR is_active = 0")
            
            updated_count = cursor.rowcount
            if updated_count > 0:
                logger.info(f"Updated {updated_count} existing campaigns with default button data and activated them")
            
            # Ad performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ad_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    user_id INTEGER,
                    target_chat TEXT,
                    message_id INTEGER,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'sent',
                    FOREIGN KEY (campaign_id) REFERENCES ad_campaigns (id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def add_campaign(self, user_id: int, account_id: int, campaign_name: str, 
                    ad_content, target_chats: List[str], schedule_type: str, 
                    schedule_time: str, buttons=None, target_mode='specific') -> int:
        """Add new ad campaign with support for complex content types and buttons"""
        import sqlite3
        start_time = time.time()
        
        try:
            StructuredLogger.log_operation(
                "add_campaign", 
                user_id=user_id, 
                campaign_id=None, 
                account_id=account_id,
                success=None,
                details=f"Creating campaign '{campaign_name}' with {len(target_chats)} targets"
            )
            
            # Convert ad_content to JSON string if it's a list or dict
            if isinstance(ad_content, (list, dict)):
                ad_content_str = json.dumps(ad_content)
            else:
                ad_content_str = str(ad_content)
            
            # Convert target_chats to JSON string
            target_chats_str = json.dumps(target_chats) if isinstance(target_chats, list) else str(target_chats)
            
            # Convert buttons to JSON string
            buttons_str = json.dumps(buttons) if buttons else None
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ad_campaigns 
                    (user_id, account_id, campaign_name, ad_content, target_chats, schedule_type, schedule_time, buttons, target_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, account_id, campaign_name, ad_content_str, 
                     target_chats_str, schedule_type, schedule_time, buttons_str, target_mode))
                conn.commit()
                campaign_id = cursor.lastrowid
                
                # Schedule the campaign
                self.schedule_campaign(campaign_id)
                
                duration = time.time() - start_time
                StructuredLogger.log_performance(
                    "add_campaign", 
                    duration, 
                    user_id=user_id, 
                    campaign_id=campaign_id,
                    details=f"Campaign '{campaign_name}' created and scheduled"
                )
                
                StructuredLogger.log_operation(
                    "add_campaign", 
                    user_id=user_id, 
                    campaign_id=campaign_id, 
                    account_id=account_id,
                    success=True,
                    details=f"Campaign '{campaign_name}' successfully created"
                )
                
                return campaign_id
                
        except Exception as e:
            StructuredLogger.log_error(
                "add_campaign", 
                e, 
                user_id=user_id, 
                account_id=account_id,
                details=f"Failed to create campaign '{campaign_name}'"
            )
            raise
    
    def get_user_campaigns(self, user_id: int) -> List[Dict]:
        """Get all campaigns for a user"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ac.id, ac.user_id, ac.account_id, ac.campaign_name, ac.ad_content, 
                       ac.target_chats, ac.schedule_type, ac.schedule_time, ac.buttons, 
                       ac.target_mode, ac.is_active, ac.created_at, ac.last_run, 
                       ac.total_sends, ta.account_name
                FROM ad_campaigns ac
                LEFT JOIN telegram_accounts ta ON ac.account_id = ta.id
                WHERE ac.user_id = ?
                ORDER BY ac.created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            
            campaigns = []
            for row in rows:
                # Parse ad_content (could be JSON string or plain string) - safer parsing
                try:
                    if row[4] and isinstance(row[4], str) and row[4].startswith(('[', '{')):
                        ad_content = json.loads(row[4])
                    else:
                        ad_content = str(row[4]) if row[4] else ""
                except (json.JSONDecodeError, AttributeError, TypeError):
                    ad_content = str(row[4]) if row[4] else ""
                
                # Parse target_chats (should be JSON string) - safer parsing
                try:
                    if row[5] and isinstance(row[5], str):
                        target_chats = json.loads(row[5])
                    elif isinstance(row[5], list):
                        target_chats = row[5]
                    else:
                        target_chats = [str(row[5])] if row[5] else []
                except (json.JSONDecodeError, TypeError):
                    target_chats = [str(row[5])] if row[5] else []
                
                # Parse buttons if they exist - much safer parsing
                buttons = []
                try:
                    if len(row) > 8 and row[8] is not None:
                        if isinstance(row[8], str) and row[8]:
                            buttons = json.loads(row[8])
                        elif isinstance(row[8], list):
                            buttons = row[8]
                except (json.JSONDecodeError, IndexError, TypeError):
                    buttons = []
                
                # Parse target_mode if it exists - safer parsing
                try:
                    target_mode = str(row[9]) if len(row) > 9 and row[9] else 'specific'
                except (IndexError, TypeError):
                    target_mode = 'specific'
                
                campaigns.append({
                    'id': row[0],                    # ac.id
                    'user_id': row[1],               # ac.user_id  
                    'account_id': row[2],            # ac.account_id
                    'campaign_name': row[3],         # ac.campaign_name
                    'ad_content': ad_content,        # ac.ad_content (parsed)
                    'target_chats': target_chats,    # ac.target_chats (parsed)
                    'schedule_type': row[6],         # ac.schedule_type
                    'schedule_time': row[7],         # ac.schedule_time
                    'buttons': buttons,              # ac.buttons (parsed)
                    'target_mode': target_mode,      # ac.target_mode (parsed)
                    'is_active': bool(row[10]),      # ac.is_active
                    'created_at': row[11],           # ac.created_at
                    'last_run': row[12],             # ac.last_run
                    'total_sends': row[13] or 0,     # ac.total_sends
                    'account_name': row[14]          # ta.account_name
                })
            return campaigns
    
    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get specific campaign by ID"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ac.id, ac.user_id, ac.account_id, ac.campaign_name, ac.ad_content, 
                       ac.target_chats, ac.schedule_type, ac.schedule_time, ac.buttons, 
                       ac.target_mode, ac.is_active, ac.created_at, ac.last_run, 
                       ac.total_sends, ta.account_name
                FROM ad_campaigns ac
                LEFT JOIN telegram_accounts ta ON ac.account_id = ta.id
                WHERE ac.id = ?
            ''', (campaign_id,))
            row = cursor.fetchone()
            
            if row:
                # Parse ad_content (could be JSON string or plain string) - safer parsing
                try:
                    if row[4] and isinstance(row[4], str) and row[4].startswith(('[', '{')):
                        ad_content = json.loads(row[4])
                    else:
                        ad_content = str(row[4]) if row[4] else ""
                except (json.JSONDecodeError, AttributeError, TypeError):
                    ad_content = str(row[4]) if row[4] else ""
                
                # Parse target_chats (should be JSON string) - safer parsing
                try:
                    if row[5] and isinstance(row[5], str):
                        target_chats = json.loads(row[5])
                    elif isinstance(row[5], list):
                        target_chats = row[5]
                    else:
                        target_chats = [str(row[5])] if row[5] else []
                except (json.JSONDecodeError, TypeError):
                    target_chats = [str(row[5])] if row[5] else []
                
                # Parse buttons if they exist - much safer parsing
                buttons = []
                try:
                    if len(row) > 8 and row[8] is not None:
                        if isinstance(row[8], str) and row[8]:
                            buttons = json.loads(row[8])
                        elif isinstance(row[8], list):
                            buttons = row[8]
                except (json.JSONDecodeError, IndexError, TypeError):
                    buttons = []
                
                # Parse target_mode if it exists - safer parsing
                try:
                    target_mode = str(row[9]) if len(row) > 9 and row[9] else 'specific'
                except (IndexError, TypeError):
                    target_mode = 'specific'
                
                return {
                    'id': row[0],                    # ac.id
                    'user_id': row[1],               # ac.user_id  
                    'account_id': row[2],            # ac.account_id
                    'campaign_name': row[3],         # ac.campaign_name
                    'ad_content': ad_content,        # ac.ad_content (parsed)
                    'target_chats': target_chats,    # ac.target_chats (parsed)
                    'schedule_type': row[6],         # ac.schedule_type
                    'schedule_time': row[7],         # ac.schedule_time
                    'buttons': buttons,              # ac.buttons (parsed)
                    'target_mode': target_mode,      # ac.target_mode (parsed)
                    'is_active': bool(row[10]),      # ac.is_active
                    'created_at': row[11],           # ac.created_at
                    'last_run': row[12],             # ac.last_run
                    'total_sends': row[13] or 0,     # ac.total_sends
                    'account_name': row[14]          # ta.account_name
                }
            return None
    
    def update_campaign(self, campaign_id: int, **kwargs):
        """Update campaign details with SQL injection protection"""
        import sqlite3
        
        # Strictly validate allowed fields to prevent SQL injection
        allowed_fields = {
            'campaign_name': str,
            'ad_content': (str, dict, list),
            'target_chats': (str, list),
            'schedule_type': str,
            'schedule_time': str,
            'is_active': bool
        }
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            # Validate field name
            if field not in allowed_fields:
                logger.warning(f"Attempted to update invalid field '{field}' for campaign {campaign_id}")
                continue
            
            # Validate field type
            expected_type = allowed_fields[field]
            if not isinstance(value, expected_type):
                logger.warning(f"Invalid type for field '{field}': expected {expected_type}, got {type(value)}")
                continue
            
            # Sanitize and prepare value
            if field == 'target_chats' and isinstance(value, list):
                value = json.dumps(value)
            elif field == 'ad_content' and isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif field == 'is_active' and not isinstance(value, bool):
                value = bool(value)
            
            updates.append(f"{field} = ?")
            values.append(value)
        
        if not updates:
            logger.warning(f"No valid updates provided for campaign {campaign_id}")
            return False
        
        try:
            values.append(campaign_id)
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                # Use parameterized query to prevent SQL injection
                cursor.execute(f'''
                    UPDATE ad_campaigns 
                    SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"No campaign found with ID {campaign_id}")
                    return False
                
                logger.info(f"Successfully updated campaign {campaign_id} with fields: {', '.join([u.split(' = ')[0] for u in updates])}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update campaign {campaign_id}: {e}")
            return False
    
    def delete_campaign(self, campaign_id: int):
        """Permanently delete campaign from database and clean up scheduler"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Delete from ad_performance table first (foreign key constraint)
            cursor.execute('DELETE FROM ad_performance WHERE campaign_id = ?', (campaign_id,))
            
            # Delete from ad_campaigns table
            cursor.execute('DELETE FROM ad_campaigns WHERE id = ?', (campaign_id,))
            
            conn.commit()
            logger.info(f"Permanently deleted campaign {campaign_id} from database")
            
        # Remove from active campaigns
        if campaign_id in self.active_campaigns:
            del self.active_campaigns[campaign_id]
            logger.info(f"Removed campaign {campaign_id} from active campaigns")
        
        # Clean up scheduled jobs for this campaign
        import schedule
        jobs_to_remove = []
        for job in schedule.jobs:
            if hasattr(job, 'job_func') and hasattr(job.job_func, 'args') and job.job_func.args and job.job_func.args[0] == campaign_id:
                jobs_to_remove.append(job)
        
        for job in jobs_to_remove:
            schedule.cancel_job(job)
            logger.info(f"Cancelled scheduled job for campaign {campaign_id}")
        
        logger.info(f"Campaign {campaign_id} completely cleaned up")
    
    def initialize_telegram_client(self, account_id: int, cache_client: bool = False) -> Optional[TelegramClient]:
        """Initialize Telegram client - Thread-safe version for scheduler"""
        # Use thread-safe semaphore to prevent simultaneous client initialization
        with self.client_init_semaphore:
            try:
                # Always run in a separate thread to avoid event loop conflicts
                import concurrent.futures
                import threading
                
                # Check if we're in the main thread (where the bot runs)
                current_thread = threading.current_thread()
                is_main_thread = current_thread == threading.main_thread()
                
                if is_main_thread:
                    # We're in the main thread - use ThreadPoolExecutor to avoid blocking
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(self._sync_initialize_client, account_id, cache_client)
                        return future.result(timeout=30)  # 30 second timeout
                else:
                    # We're already in a background thread - run directly
                    return self._sync_initialize_client(account_id, cache_client)
                    
            except Exception as e:
                logger.error(f"Failed to initialize client for account {account_id}: {e}")
                return None
    
    def _sync_initialize_client(self, account_id: int, cache_client: bool = False) -> Optional[TelegramClient]:
        """Synchronous wrapper for client initialization in a new thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._async_initialize_client(account_id, cache_client))
        finally:
            loop.close()
    
    async def _async_initialize_client(self, account_id: int, cache_client: bool = False) -> Optional[TelegramClient]:
        """Async helper for client initialization with improved session validation"""
        # For scheduled executions, always create fresh client to avoid asyncio loop issues
        if cache_client and account_id in self.telegram_clients:
            return self.telegram_clients[account_id]
        
        account = self.db.get_account(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return None
        
        # Use EXACT same session handling as bot.py execute_immediate_campaign
        from telethon import TelegramClient
        import base64
        import os
        import time
        import random
        
        # Small delay to ensure clean separation between initializations
        await asyncio.sleep(0.2)
        
        # Handle session creation (same as bot.py)
        temp_session_path = f"bump_session_{account_id}"
        session_file_path = f"{temp_session_path}.session"
        
        # Register for cleanup
        self._register_temp_file(session_file_path)
        
        # Check if we have a valid session (same as bot.py)
        if not account.get('session_string'):
            logger.error(f"Account {account_id} has no session string. Please re-authenticate the account.")
            self._cleanup_temp_file(session_file_path)
            return None
        
        # Clean up any existing session file first
        self._cleanup_temp_file(session_file_path)
        
        # Handle uploaded sessions vs API credential sessions (EXACT SAME as bot.py)
        if account['api_id'] == 'uploaded' or account['api_hash'] == 'uploaded':
            # For uploaded sessions, decode and save the session file
            try:
                session_data = base64.b64decode(account['session_string'])
                with open(f"{temp_session_path}.session", "wb") as f:
                    f.write(session_data)
                # Use dummy credentials for uploaded sessions
                api_id = 123456  
                api_hash = 'dummy_hash_for_uploaded_sessions'
            except Exception as e:
                logger.error(f"Failed to decode uploaded session for account {account_id}: {e}")
                return None
        else:
            # For API credential accounts with authenticated sessions (EXACT SAME as bot.py)
            try:
                api_id = int(account['api_id'])
                api_hash = account['api_hash']
                
                # Session string is base64 encoded session file data
                # Decode and write it as the session file
                session_data = base64.b64decode(account['session_string'])
                with open(f"{temp_session_path}.session", "wb") as f:
                    f.write(session_data)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid API credentials for account {account_id}: {e}")
                return None
            except Exception as e:
                logger.error(f"Failed to decode session for account {account_id}: {e}")
                return None
        
        # Validate session file was created and has content
        if not os.path.exists(f"{temp_session_path}.session"):
            logger.error(f"Session file not created for account {account_id}")
            return None
        
        if os.path.getsize(f"{temp_session_path}.session") == 0:
            logger.error(f"Session file is empty for account {account_id}")
            try:
                os.remove(f"{temp_session_path}.session")
            except:
                pass
            return None
        
        # Initialize and start client with retry logic for database locks
        max_retries = 3
        client = None
        for attempt in range(max_retries):
            try:
                client = TelegramClient(temp_session_path, api_id, api_hash)
                await client.start()
                
                # Verify the session is valid (EXACT SAME as bot.py)
                me = await client.get_me()
                if not me:
                    logger.error(f"Session invalid for account {account_id}")
                    await client.disconnect()
                    return None
                    
                logger.info(f"Successfully authenticated as {me.username or me.phone}")
                break  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e).lower()
                if "database is locked" in error_msg and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2 + random.uniform(0.5, 1.5)
                    logger.warning(f"Database locked during client start, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    
                    # Clean up any partial session files
                    try:
                        if os.path.exists(f"{temp_session_path}.session"):
                            os.remove(f"{temp_session_path}.session")
                    except:
                        pass
                    continue
                elif "eof when reading a line" in error_msg:
                    logger.error(f"Session file corrupted for account {account_id}: {e}")
                    logger.error(f"💡 Solution: Re-add {account.get('username', 'this account')} with API credentials instead of uploaded session")
                    # Clean up corrupted session file
                    try:
                        if os.path.exists(f"{temp_session_path}.session"):
                            os.remove(f"{temp_session_path}.session")
                    except:
                        pass
                    return None
                else:
                    logger.error(f"Failed to start client for account {account_id}: {e}")
                    # Clean up session file on failure (EXACT SAME as bot.py)
                    try:
                        if os.path.exists(f"{temp_session_path}.session"):
                            os.remove(f"{temp_session_path}.session")
                    except:
                        pass
                    return None
        
        if client is None:
            logger.error(f"Failed to initialize client for account {account_id} after {max_retries} attempts")
            return None
        
        # Only cache client if requested (not for scheduled executions)
        if cache_client:
            self.telegram_clients[account_id] = client
        logger.info(f"Telegram client initialized for bump service (Account: {account_id})")
        return client
    
    def send_ad(self, campaign_id: int):
        """Send ad for a specific campaign with button support - Thread-safe version"""
        try:
            import threading
            
            # Check if we're in the main thread
            current_thread = threading.current_thread()
            is_main_thread = current_thread == threading.main_thread()
            
            if is_main_thread:
                # We're in the main thread - use ThreadPoolExecutor to avoid blocking
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._sync_send_ad, campaign_id)
                    return future.result(timeout=60)  # 60 second timeout for sending ads
            else:
                # We're already in a background thread - run directly
                return self._sync_send_ad(campaign_id)
                
        except Exception as e:
            logger.error(f"Failed to send ad for campaign {campaign_id}: {e}")
            return False
    
    def _sync_send_ad(self, campaign_id: int):
        """Synchronous wrapper for send_ad in a new thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._async_send_ad(campaign_id))
        finally:
            loop.close()
    
    async def _async_send_ad(self, campaign_id: int):
        """Async helper for send_ad"""
        campaign = self.get_campaign(campaign_id)
        if not campaign or not campaign['is_active']:
            logger.warning(f"Campaign {campaign_id} not found or inactive")
            return
        
        # Get account info for logging
        account = self.db.get_account(campaign['account_id'])
        account_name = account['account_name'] if account else f"Account_{campaign['account_id']}"
        
        logger.info(f"🚀 Starting campaign {campaign['campaign_name']} using {account_name}")
        
        # Use fresh client for scheduled execution to avoid asyncio loop issues
        # Note: We need to call the async version here since we're in async context
        client = await self._async_initialize_client(campaign['account_id'], cache_client=False)
        if not client:
            logger.error(f"❌ Failed to initialize {account_name} for campaign {campaign_id}")
            logger.error(f"💡 Solution: Re-add {account_name} with API credentials instead of uploaded session")
            return
        
        ad_content = campaign['ad_content']
        target_chats = campaign['target_chats']
        buttons = campaign.get('buttons', [])
        sent_count = 0
        
        # Create buttons from campaign data or use default
        from telethon import Button
        telethon_buttons = None
        
        if buttons and len(buttons) > 0:
            # Convert stored button data to Telethon buttons
            try:
                button_rows = []
                current_row = []
                
                for i, button in enumerate(buttons):
                    if button.get('url'):
                        # URL button
                        telethon_button = Button.url(button['text'], button['url'])
                    else:
                        # Regular callback button (for inline responses)
                        telethon_button = Button.inline(button['text'], f"btn_{campaign_id}_{i}")
                    
                    current_row.append(telethon_button)
                    
                    # Create new row every 2 buttons or at the end
                    if len(current_row) == 2 or i == len(buttons) - 1:
                        button_rows.append(current_row)
                        current_row = []
                
                telethon_buttons = button_rows
                logger.info(f"✅ Created {len(buttons)} buttons in {len(button_rows)} rows for campaign {campaign_id}")
            except Exception as e:
                logger.error(f"❌ Error creating buttons for campaign {campaign_id}: {e}")
                # Fallback to default button
                telethon_buttons = [[Button.url("Shop Now", "https://t.me/testukassdfdds")]]
        else:
            # Default button if none specified
            telethon_buttons = [[Button.url("Shop Now", "https://t.me/testukassdfdds")]]
            logger.info(f"Using default Shop Now button for campaign {campaign_id}")
        
        # Get all groups if target_mode is all_groups
        if campaign.get('target_mode') == 'all_groups' or target_chats == ['ALL_WORKER_GROUPS']:
            logger.info(f"Getting all groups for scheduled campaign {campaign_id}")
            dialogs = await client.get_dialogs()
            target_entities = []
            for dialog in dialogs:
                if dialog.is_group:
                    target_entities.append(dialog.entity)
                    logger.info(f"Found group for scheduled send: {dialog.name}")
        else:
            # Convert chat IDs to entities
            target_entities = []
            for chat_id in target_chats:
                try:
                    entity = await client.get_entity(chat_id)
                    target_entities.append(entity)
                except Exception as e:
                    logger.error(f"Failed to get entity for {chat_id}: {e}")
        
        for chat_entity in target_entities:
            message = None
            try:
                # Handle different content types
                if isinstance(ad_content, list) and ad_content:
                    # Find the main media message and combine all text content
                    media_message = None
                    combined_text = ""
                    
                    for message_data in ad_content:
                        if message_data.get('media_type') and not media_message:
                            # Use the first media message as the main one
                            media_message = message_data
                        elif message_data.get('text'):
                            # Collect all text content
                            if combined_text:
                                combined_text += "\n\n" + message_data.get('text', '')
                            else:
                                combined_text = message_data.get('text', '')
                    
                    if media_message:
                        # Send ONE message with media + combined text + buttons
                        try:
                            # Combine caption with additional text
                            caption_text = media_message.get('caption', '')
                            if caption_text and combined_text:
                                final_caption = caption_text + "\n\n" + combined_text
                            elif combined_text:
                                final_caption = combined_text
                            else:
                                final_caption = caption_text
                            
                            # ALWAYS add button URLs as text for media messages (inline buttons don't work in regular groups)
                            button_text = ""
                            for button_row in telethon_buttons:
                                for button in button_row:
                                    if hasattr(button, 'url'):
                                        button_text += f"\n\n🔗 {button.text}: {button.url}"
                            
                            # Combine caption with button text
                            final_caption = (final_caption or "") + button_text
                            
                            # Try to preserve custom emojis by using the original message approach
                            try:
                                # First, try to forward the original message to preserve all entities
                                if 'original_message_id' in media_message and 'original_chat_id' in media_message:
                                    try:
                                        # Get the original message and forward it
                                        original_chat = await client.get_entity(media_message['original_chat_id'])
                                        original_message = await client.get_messages(original_chat, ids=media_message['original_message_id'])
                                        
                                        if original_message:
                                            # Forward the original message to preserve all entities including custom emojis
                                            message = await client.forward_messages(
                                                chat_entity,
                                                original_message,
                                                silent=True
                                            )
                                            
                                            # If we have additional text or buttons, send a follow-up message
                                            if final_caption and final_caption.strip():
                                                # Send the caption as a separate message with buttons
                                                follow_up_text = final_caption
                                                if telethon_buttons:
                                                    follow_up_text += "\n\n" + self._format_buttons_as_text(telethon_buttons)
                                                
                                                await client.send_message(
                                                    chat_entity,
                                                    follow_up_text,
                                                    reply_to=message.id,
                                                    parse_mode='html'
                                                )
                                            
                                            logger.info(f"✅ Forwarded original message with preserved entities to {chat_entity.title}")
                                            continue
                                    except Exception as forward_error:
                                        logger.warning(f"Failed to forward original message, falling back to download: {forward_error}")
                                
                                # Fallback: Download and re-upload (loses custom emojis but preserves basic content)
                                media_file = await client.download_media(media_message['file_id'])
                                
                                if media_file and os.path.exists(media_file):
                                    # Register for cleanup
                                    self._register_temp_file(media_file)
                                    
                                    # Send the downloaded media file with inline buttons (try first, fallback to text)
                                    try:
                                        # Try with inline buttons first (works in channels and some groups)
                                        message = await client.send_file(
                                            chat_entity,
                                            media_file,
                                            caption=final_caption,
                                            buttons=telethon_buttons,
                                            parse_mode='html'
                                        )
                                        logger.info(f"✅ Media sent with inline buttons to {chat_entity.title}")
                                    except Exception as button_error:
                                        # Fallback: Send without buttons, then send buttons as text
                                        logger.warning(f"Inline buttons failed, using text fallback: {button_error}")
                                        message = await client.send_file(
                                            chat_entity,
                                            media_file,
                                            caption=final_caption,
                                            parse_mode='html'
                                        )
                                        
                                        # Send buttons as a follow-up message
                                        if telethon_buttons:
                                            button_text = self._format_buttons_as_text(telethon_buttons)
                                            if button_text:
                                                await client.send_message(
                                                    chat_entity,
                                                    button_text,
                                                    reply_to=message.id,
                                                    parse_mode='html'
                                                )
                                    logger.info(f"✅ Combined media+text sent via download ({media_message['media_type']}) to {chat_entity.title}")
                                    
                                    # Clean up downloaded file
                                    self._cleanup_temp_file(media_file)
                                else:
                                    # Fallback to text if media download fails
                                    if final_caption:
                                        # Add buttons as text to the message
                                        final_caption_with_buttons = final_caption
                                        if telethon_buttons:
                                            final_caption_with_buttons += "\n\n" + self._format_buttons_as_text(telethon_buttons)
                                        
                                        message = await client.send_message(
                                            chat_entity,
                                            final_caption_with_buttons,
                                            parse_mode='html'
                                        )
                                        logger.warning(f"⚠️ Media download failed, sent as text to {chat_entity.title}")
                                    else:
                                        continue  # Skip if no text content
                                    
                            except Exception as media_error:
                                logger.error(f"❌ Failed to send combined media+text to {chat_entity.title}: {media_error}")
                                # Fallback to text message
                                if final_caption:
                                    # Add buttons as text to the message
                                    final_caption_with_buttons = final_caption
                                    if telethon_buttons:
                                        final_caption_with_buttons += "\n\n" + self._format_buttons_as_text(telethon_buttons)
                                    
                                    message = await client.send_message(
                                        chat_entity,
                                        final_caption_with_buttons,
                                        parse_mode='html'
                                    )
                                    logger.info(f"📝 Sent as text fallback to {chat_entity.title}")
                                else:
                                    continue  # Skip if no text content
                        except Exception as e:
                            logger.error(f"❌ Failed to send combined media+text to {chat_entity.title}: {e}")
                            # Fallback to text message
                            if combined_text:
                                # Try with inline buttons first, fallback to text
                                try:
                                    message = await client.send_message(
                                        chat_entity,
                                        combined_text,
                                        buttons=telethon_buttons,
                                        parse_mode='html'
                                    )
                                    logger.info(f"✅ Text sent with inline buttons to {chat_entity.title}")
                                except Exception as button_error:
                                    # Fallback: Send with buttons as text
                                    logger.warning(f"Inline buttons failed for text, using text fallback: {button_error}")
                                    message = await client.send_message(
                                        chat_entity,
                                        self._add_buttons_to_text(combined_text, telethon_buttons),
                                        parse_mode='html'
                                    )
                                logger.info(f"📝 Sent as text fallback to {chat_entity.title}")
                            else:
                                continue  # Skip if no text content
                    else:
                        # No media, just send combined text as one message
                        try:
                            if combined_text:
                                # Add buttons as text to the message
                                combined_text_with_buttons = combined_text
                                if telethon_buttons:
                                    combined_text_with_buttons += "\n\n" + self._format_buttons_as_text(telethon_buttons)
                                
                                message = await client.send_message(
                                    chat_entity,
                                    combined_text_with_buttons,
                                    parse_mode='html'
                                )
                                logger.info(f"✅ Combined text message sent to {chat_entity.title}")
                            else:
                                continue  # Skip if no content
                        except Exception as e:
                            logger.error(f"❌ Failed to send text message to {chat_entity.title}: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"❌ Failed to send combined media+text to {chat_entity.title}: {e}")
                            # Fallback to text message
                            if combined_text:
                                # Try with inline buttons first, fallback to text
                                try:
                                    message = await client.send_message(
                                        chat_entity,
                                        combined_text,
                                        buttons=telethon_buttons,
                                        parse_mode='html'
                                    )
                                    logger.info(f"✅ Text sent with inline buttons to {chat_entity.title}")
                                except Exception as button_error:
                                    # Fallback: Send with buttons as text
                                    logger.warning(f"Inline buttons failed for text, using text fallback: {button_error}")
                                    message = await client.send_message(
                                        chat_entity,
                                        self._add_buttons_to_text(combined_text, telethon_buttons),
                                        parse_mode='html'
                                    )
                                logger.info(f"📝 Sent as text fallback to {chat_entity.title}")
                            else:
                                continue  # Skip if no text content
                else:
                    # Single message - check if it has media or is just text
                    if isinstance(ad_content, dict) and ad_content.get('media_type'):
                        # Single message with media - send as ONE combined message
                        try:
                            caption_text = ad_content.get('caption', ad_content.get('text', ''))
                            
                            # ALWAYS add button URLs as text for single media messages (inline buttons don't work in regular groups)
                            button_text = ""
                            for button_row in telethon_buttons:
                                for button in button_row:
                                    if hasattr(button, 'url'):
                                        button_text += f"\n\n🔗 {button.text}: {button.url}"
                            
                            # Combine caption with button text
                            caption_text = (caption_text or "") + button_text

                            # Download the media file (Bot API file_id not compatible with Telethon)
                            try:
                                # Download the media file from the original message
                                media_file = await client.download_media(ad_content['file_id'])
                                
                                if media_file and os.path.exists(media_file):
                                    # Register for cleanup
                                    self._register_temp_file(media_file)
                                    
                                    # Try with inline buttons first, fallback to text
                                    try:
                                        message = await client.send_file(
                                            chat_entity,
                                            media_file,
                                            caption=caption_text,
                                            buttons=telethon_buttons,
                                            parse_mode='html'
                                        )
                                        logger.info(f"✅ Single media sent with inline buttons to {chat_entity.title}")
                                    except Exception as button_error:
                                        # Fallback: Send without buttons, then send buttons as text
                                        logger.warning(f"Inline buttons failed for single media, using text fallback: {button_error}")
                                        message = await client.send_file(
                                            chat_entity,
                                            media_file,
                                            caption=caption_text,
                                            parse_mode='html'
                                        )
                                        
                                        # Send buttons as a follow-up message
                                        if telethon_buttons:
                                            button_text = self._format_buttons_as_text(telethon_buttons)
                                            if button_text:
                                                await client.send_message(
                                                    chat_entity,
                                                    button_text,
                                                    reply_to=message.id,
                                                    parse_mode='html'
                                                )
                                    logger.info(f"✅ Single media+text sent via download ({ad_content['media_type']}) to {chat_entity.title}")
                                    
                                    # Clean up downloaded file
                                    self._cleanup_temp_file(media_file)
                                else:
                                    # Fallback to text if media download fails
                                    if caption_text:
                                        # Try with inline buttons first, fallback to text
                                        try:
                                            message = await client.send_message(
                                                chat_entity,
                                                caption_text,
                                                buttons=telethon_buttons,
                                                parse_mode='html'
                                            )
                                            logger.info(f"✅ Caption sent with inline buttons to {chat_entity.title}")
                                        except Exception as button_error:
                                            # Fallback: Send with buttons as text
                                            logger.warning(f"Inline buttons failed for caption, using text fallback: {button_error}")
                                            message = await client.send_message(
                                                chat_entity,
                                                self._add_buttons_to_text(caption_text, telethon_buttons),
                                                parse_mode='html'
                                            )
                                        logger.warning(f"⚠️ Single media download failed, sent as text to {chat_entity.title}")
                                    else:
                                        continue
                            except Exception as e:
                                logger.error(f"❌ Failed to download media for single message: {e}")
                                # Fallback to text if media download fails
                                if caption_text:
                                    message = await client.send_message(
                                        chat_entity,
                                        caption_text,
                                        parse_mode='html'
                                    )
                                    logger.warning(f"⚠️ Single media download failed, sent as text to {chat_entity.title}")
                                else:
                                    continue
                        except Exception as media_error:
                            logger.error(f"❌ Failed to send single media to {chat_entity.title}: {media_error}")
                            # Fallback to text message
                            caption_text = ad_content.get('caption', ad_content.get('text', ''))
                            if caption_text:
                                # Try with inline buttons first, fallback to text
                                try:
                                    message = await client.send_message(
                                        chat_entity,
                                        caption_text,
                                        buttons=telethon_buttons,
                                        parse_mode='html'
                                    )
                                    logger.info(f"✅ Caption sent with inline buttons to {chat_entity.title}")
                                except Exception as button_error:
                                    # Fallback: Send with buttons as text
                                    logger.warning(f"Inline buttons failed for caption, using text fallback: {button_error}")
                                    message = await client.send_message(
                                        chat_entity,
                                        self._add_buttons_to_text(caption_text, telethon_buttons),
                                        parse_mode='html'
                                    )
                                logger.info(f"📝 Single media sent as text fallback to {chat_entity.title}")
                            else:
                                continue
                    else:
                        # Single text message with buttons
                        message_text = ad_content if isinstance(ad_content, str) else str(ad_content)
                        
                        # ALWAYS add button URLs as text for groups (inline buttons don't work in regular groups)
                        button_text = ""
                        for button_row in telethon_buttons:
                            for button in button_row:
                                if hasattr(button, 'url'):
                                    button_text += f"\n\n🔗 {button.text}: {button.url}"
                        
                        # Combine message with button text
                        final_message = message_text + button_text
                        
                        # Try sending with both inline buttons AND text
                        try:
                            message = await client.send_message(
                                chat_entity,
                                final_message,  # Message includes button URLs as text
                                buttons=telethon_buttons  # Also try inline buttons for channels
                            )
                            logger.info(f"✅ Message sent with buttons (inline + text) to {chat_entity.title}")
                        except Exception as send_error:
                            # If that fails, try without inline buttons
                            message = await client.send_message(chat_entity, final_message)
                            logger.info(f"✅ Message sent with text buttons to {chat_entity.title}")
                
                # Log the performance
                if message:
                    self.log_ad_performance(campaign_id, campaign['user_id'], str(chat_entity.id), message.id)
                    sent_count += 1
                    logger.info(f"Scheduled ad sent to {chat_entity.title} ({chat_entity.id}) for campaign {campaign['campaign_name']}")
                
                # Add delay between sends
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to send scheduled ad to {chat_entity.title if hasattr(chat_entity, 'title') else 'Unknown'}: {e}")
                self.log_ad_performance(campaign_id, campaign['user_id'], str(chat_entity.id) if hasattr(chat_entity, 'id') else 'unknown', None, 'failed')
        
        # Update campaign statistics
        self.update_campaign_stats(campaign_id, sent_count)
        logger.info(f"Scheduled campaign {campaign['campaign_name']} completed: {sent_count}/{len(target_entities)} ads sent with buttons")
        
        # Disconnect client after scheduled execution to prevent asyncio loop issues
        try:
            await client.disconnect()
            logger.info(f"Disconnected client for scheduled campaign {campaign_id}")
        except Exception as e:
            logger.warning(f"Failed to disconnect client for campaign {campaign_id}: {e}")
    
    def log_ad_performance(self, campaign_id: int, user_id: int, target_chat: str, 
                          message_id: Optional[int], status: str = 'sent'):
        """Log ad performance"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ad_performance 
                (campaign_id, user_id, target_chat, message_id, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (campaign_id, user_id, target_chat, message_id, status))
            conn.commit()
    
    def update_campaign_stats(self, campaign_id: int, sent_count: int):
        """Update campaign statistics"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ad_campaigns 
                SET last_run = CURRENT_TIMESTAMP, total_sends = total_sends + ?
                WHERE id = ?
            ''', (sent_count, campaign_id))
            conn.commit()
    
    def schedule_campaign(self, campaign_id: int):
        """Schedule a campaign based on its schedule type"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return
        
        schedule_type = campaign['schedule_type']
        schedule_time = campaign['schedule_time']
        
        if schedule_type == 'daily':
            schedule.every().day.at(schedule_time).do(self.run_campaign_job, campaign_id)
        elif schedule_type == 'weekly':
            # Assuming format like "Monday 14:30"
            day, time_str = schedule_time.split(' ')
            getattr(schedule.every(), day.lower()).at(time_str).do(self.run_campaign_job, campaign_id)
        elif schedule_type == 'hourly':
            schedule.every().hour.do(self.run_campaign_job, campaign_id)
        elif schedule_type == 'custom':
            # Parse custom interval (e.g., "every 3 minutes", "every 4 hours")
            try:
                if 'hour' in schedule_time.lower():
                    hours = int(schedule_time.split()[1])
                    job = schedule.every(hours).hours.do(self.run_campaign_job, campaign_id)
                    
                    # IMPORTANT: Run the job immediately for the first time if campaign is active
                    campaign = self.get_campaign(campaign_id)
                    if campaign and campaign.get('is_active', False):
                        logger.info(f"🚀 Running campaign {campaign_id} immediately on schedule activation")
                        # Add staggered delay to prevent database conflicts
                        import random
                        delay = random.uniform(0.5, 2.0)  # Random delay between 0.5-2 seconds
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: (time.sleep(delay), self.run_campaign_job(campaign_id)), daemon=True).start()
                    
                    logger.info(f"📅 Campaign {campaign_id} scheduled every {hours} hours")
                elif 'minute' in schedule_time.lower():
                    # Handle formats like "3 minutes", "every 3 minutes"
                    parts = schedule_time.split()
                    if len(parts) >= 2:
                        # Find the number in the string
                        for part in parts:
                            if part.isdigit():
                                minutes = int(part)
                                break
                        else:
                            minutes = 10  # default
                    else:
                        minutes = 10  # default
                    
                    # Schedule the job to run every X minutes
                    job = schedule.every(minutes).minutes.do(self.run_campaign_job, campaign_id)
                    
                    # IMPORTANT: Run the job immediately for the first time if campaign is active
                    campaign = self.get_campaign(campaign_id)
                    if campaign and campaign.get('is_active', False):
                        logger.info(f"🚀 Running campaign {campaign_id} immediately on schedule activation")
                        # Add staggered delay to prevent database conflicts
                        import random
                        delay = random.uniform(0.5, 2.0)  # Random delay between 0.5-2 seconds
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: (time.sleep(delay), self.run_campaign_job(campaign_id)), daemon=True).start()
                    
                    logger.info(f"📅 Campaign {campaign_id} scheduled every {minutes} minutes")
                elif schedule_time.isdigit():
                    # If just a number, assume minutes
                    minutes = int(schedule_time)
                    job = schedule.every(minutes).minutes.do(self.run_campaign_job, campaign_id)
                    
                    # IMPORTANT: Run the job immediately for the first time if campaign is active
                    campaign = self.get_campaign(campaign_id)
                    if campaign and campaign.get('is_active', False):
                        logger.info(f"🚀 Running campaign {campaign_id} immediately on schedule activation")
                        # Add staggered delay to prevent database conflicts
                        import random
                        delay = random.uniform(0.5, 2.0)  # Random delay between 0.5-2 seconds
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: (time.sleep(delay), self.run_campaign_job(campaign_id)), daemon=True).start()
                    
                    logger.info(f"📅 Campaign {campaign_id} scheduled every {minutes} minutes")
                else:
                    logger.warning(f"⚠️ Unknown custom schedule format: {schedule_time}")
            except (ValueError, IndexError) as e:
                logger.error(f"❌ Error parsing custom schedule '{schedule_time}': {e}")
                # Default to 10 minutes if parsing fails
                schedule.every(10).minutes.do(self.run_campaign_job, campaign_id)
                logger.info(f"📅 Campaign {campaign_id} defaulted to every 10 minutes")
        
        self.active_campaigns[campaign_id] = campaign
        logger.info(f"Scheduled campaign {campaign_id} ({schedule_type} at {schedule_time})")
    
    def run_campaign_job(self, campaign_id: int):
        """Execute scheduled campaign automatically"""
        try:
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🔄 Scheduler executing campaign {campaign_id} at {current_time}")
            
            # Get campaign from database
            campaign = self.get_campaign(campaign_id)
            if not campaign:
                logger.warning(f"Campaign {campaign_id} not found for scheduled execution - removing from active campaigns")
                # Remove from active campaigns if campaign doesn't exist
                if campaign_id in self.active_campaigns:
                    del self.active_campaigns[campaign_id]
                return
                
            if not campaign.get('is_active', False):
                logger.warning(f"Campaign {campaign_id} is not active, removing from active campaigns")
                # Remove inactive campaigns from active campaigns
                if campaign_id in self.active_campaigns:
                    del self.active_campaigns[campaign_id]
                return
            
            # Log next scheduled run
            logger.info(f"📅 Next run for campaign {campaign_id} will be in {campaign['schedule_time']}")
            
            # Execute campaign in new thread to avoid blocking scheduler
            def execute_async():
                try:
                    import asyncio
                    # Run the campaign asynchronously
                    asyncio.run(self.execute_scheduled_campaign(campaign_id, campaign))
                except Exception as e:
                    logger.error(f"Error executing scheduled campaign {campaign_id}: {e}")
            
            # Start execution in separate thread
            execution_thread = threading.Thread(target=execute_async, daemon=True)
            execution_thread.start()
            logger.info(f"✅ Campaign {campaign_id} scheduled execution started")
            
        except Exception as e:
            logger.error(f"Error in campaign scheduler for {campaign_id}: {e}")
    
    async def execute_scheduled_campaign(self, campaign_id: int, campaign: dict):
        """Execute a scheduled campaign automatically"""
        try:
            logger.info(f"🚀 Executing scheduled campaign {campaign_id}: {campaign['campaign_name']}")
            
            # Check account status first
            account = self.db.get_account(campaign['account_id'])
            if not account:
                logger.error(f"Account {campaign['account_id']} not found for campaign {campaign_id}")
                return False
            
            if not account.get('session_string'):
                logger.error(f"Account {campaign['account_id']} ({account.get('account_name', 'Unknown')}) has no session string")
                logger.error(f"Please re-add account '{account.get('account_name', 'Unknown')}' with phone verification")
                return False
            
            # Send the ad using the async version directly
            await self._async_send_ad(campaign_id)
            logger.info(f"✅ Scheduled campaign {campaign_id} executed successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing scheduled campaign {campaign_id}: {e}")
            return False
    
    def cleanup_corrupted_sessions(self):
        """Clean up any corrupted session files"""
        import os
        import glob
        
        try:
            # Find all bump session files
            session_files = glob.glob("bump_session_*.session")
            cleaned_count = 0
            
            for session_file in session_files:
                try:
                    # Check if file is empty or corrupted
                    if os.path.getsize(session_file) == 0:
                        os.remove(session_file)
                        cleaned_count += 1
                        logger.info(f"Cleaned up empty session file: {session_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up session file {session_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} corrupted session files")
                
        except Exception as e:
            logger.warning(f"Error during session cleanup: {e}")

    def start_scheduler(self):
        """Start the campaign scheduler with proper background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🚀 Bump service scheduler started (automatic execution mode)")
        
        # Clean up any corrupted session files
        self.cleanup_corrupted_sessions()
        
        # Load existing campaigns into memory
        self.load_existing_campaigns()
        
        # Start background scheduler thread
        def scheduler_worker():
            """Background worker that runs scheduled campaigns"""
            logger.info("📅 Scheduler worker thread started")
            last_log_time = time.time()
            while self.is_running:
                try:
                    # Log scheduler status every 60 seconds
                    current_time = time.time()
                    if current_time - last_log_time >= 60:
                        jobs = schedule.get_jobs()
                        logger.info(f"⏰ Scheduler status: {len(jobs)} active jobs, {len(self.active_campaigns)} active campaigns")
                        # Log details about each job
                        for job in jobs:
                            next_run = job.next_run.strftime("%H:%M:%S") if job.next_run else "Not scheduled"
                            logger.info(f"  📅 Job scheduled for: {next_run}")
                        last_log_time = current_time
                    
                    # Run pending scheduled jobs
                    schedule.run_pending()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logger.error(f"Error in scheduler worker: {e}")
                    time.sleep(5)  # Wait 5 seconds on error
            logger.info("📅 Scheduler worker thread stopped")
        
        # Start the scheduler thread
        self.scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
        self.scheduler_thread.start()
        logger.info("✅ Background scheduler thread started successfully")
    
    def stop_scheduler(self):
        """Stop the campaign scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        logger.info("Bump service scheduler stopped")
    
    def load_existing_campaigns(self):
        """Load and schedule existing active campaigns"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, campaign_name, schedule_time FROM ad_campaigns WHERE is_active = 1')
            rows = cursor.fetchall()
            
            for row in rows:
                campaign_id = row[0]
                campaign_name = row[1]
                schedule_time = row[2]
                logger.info(f"Loading campaign {campaign_id}: {campaign_name} (schedule: {schedule_time})")
                self.schedule_campaign(campaign_id)
        
        logger.info(f"Loaded {len(rows)} existing campaigns")
    
    def get_campaign_performance(self, campaign_id: int) -> Dict[str, Any]:
        """Get performance statistics for a campaign"""
        import sqlite3
        
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful_sends,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sends
                FROM ad_performance 
                WHERE campaign_id = ?
            ''', (campaign_id,))
            row = cursor.fetchone()
            
            return {
                'total_attempts': row[0] or 0,
                'successful_sends': row[1] or 0,
                'failed_sends': row[2] or 0,
                'success_rate': (row[1] / row[0] * 100) if row[0] > 0 else 0
            }
    
    async def test_campaign(self, campaign_id: int, test_chat: str) -> bool:
        """Test campaign by sending to a single chat"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return False
        
        # Use fresh client for scheduled execution to avoid asyncio loop issues
        client = self.initialize_telegram_client(campaign['account_id'], cache_client=False)
        if not client:
            return False
        
        try:
            test_content = f"🧪 **TEST AD**\n\n{campaign['ad_content']}\n\n_This is a test message for campaign: {campaign['campaign_name']}_"
            await client.send_message(test_chat, test_content)
            logger.info(f"Test ad sent for campaign {campaign_id}")
            return True
        except Exception as e:
            logger.error(f"Test ad failed for campaign {campaign_id}: {e}")
            return False
        finally:
            # Always disconnect client after test
            try:
                await client.disconnect()
                logger.info(f"Disconnected test client for campaign {campaign_id}")
            except Exception as e:
                logger.warning(f"Failed to disconnect test client for campaign {campaign_id}: {e}")
    
    async def close(self):
        """Close all connections"""
        self.stop_scheduler()
        
        for account_id, client in self.telegram_clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected bump service client for account {account_id}")
            except Exception as e:
                logger.error(f"Error disconnecting client {account_id}: {e}")
        
        self.telegram_clients.clear()
