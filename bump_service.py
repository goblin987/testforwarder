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
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from telethon import TelegramClient
from telethon.tl.custom import Button
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButtonUrl, KeyboardButtonRow
from database import Database
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.constants import ParseMode
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
    
    async def _process_bridge_channel_message(self, client, chat_entity, ad_content, telethon_reply_markup):
        """Process bridge channel message with premium emoji preservation"""
        try:
            bridge_channel_entity = ad_content.get('bridge_channel_entity')
            bridge_message_id = ad_content.get('bridge_message_id')
            
            logger.info(f"🔗 Bridge channel: {bridge_channel_entity}, Message ID: {bridge_message_id}")
            
            # Step 1: Get the bridge channel entity (join if needed)
            try:
                bridge_entity = await client.get_entity(bridge_channel_entity)
                logger.info(f"✅ Bridge channel entity resolved: {getattr(bridge_entity, 'title', bridge_channel_entity)}")
                
                # Try to join the channel (if it's public and we're not already in it)
                try:
                    from telethon.tl.functions.channels import JoinChannelRequest
                    await client(JoinChannelRequest(bridge_entity))
                    logger.info(f"✅ Joined bridge channel {bridge_channel_entity}")
                except Exception as join_error:
                    logger.info(f"Already in bridge channel or can't join: {join_error}")
                
            except Exception as entity_error:
                logger.error(f"❌ Could not resolve bridge channel {bridge_channel_entity}: {entity_error}")
                return
            
            # Step 2: Get the original message from bridge channel (preserves all entities)
            try:
                original_message = await client.get_messages(bridge_entity, ids=bridge_message_id)
                if not original_message:
                    logger.error(f"❌ Message {bridge_message_id} not found in {bridge_channel_entity}")
                    return
                
                logger.info(f"✅ Retrieved original message from bridge channel with all entities intact")
                logger.info(f"Message has media: {bool(original_message.media)}")
                logger.info(f"Message text length: {len(original_message.message or '')}")
                
                # Step 3: Forward the message with all entities preserved + add buttons
                if original_message.media:
                    # Forward media with preserved entities and add buttons
                    message = await client.send_file(
                        chat_entity,
                        original_message.media,
                        caption=original_message.message,
                        reply_markup=telethon_reply_markup
                    )
                    logger.info(f"✅ Bridge channel media forwarded with PREMIUM EMOJIS and buttons to {chat_entity.title}")
                else:
                    # Forward text with preserved entities and add buttons
                    message = await client.send_message(
                        chat_entity,
                        original_message.message,
                        reply_markup=telethon_reply_markup
                    )
                    logger.info(f"✅ Bridge channel text forwarded with PREMIUM EMOJIS and buttons to {chat_entity.title}")
                
            except Exception as message_error:
                logger.error(f"❌ Could not retrieve/forward message from bridge channel: {message_error}")
                return
                
        except Exception as e:
            logger.error(f"❌ Bridge channel processing failed: {e}")
            return
    
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
    
    # Removed _format_buttons_as_text - now using inline buttons only
    
    def _reconstruct_text_with_entities(self, text, entities):
        """Reconstruct text with custom emojis using entity data"""
        if not text or not entities:
            return text or ""
        
        logger.info(f"Reconstructing text with {len(entities)} entities")
        
        # Sort entities by offset to process them in order
        sorted_entities = sorted(entities, key=lambda x: x.get('offset', 0))
        
        reconstructed = ""
        last_offset = 0
        
        for entity in sorted_entities:
            entity_type = entity.get('type', '')
            offset = entity.get('offset', 0)
            length = entity.get('length', 0)
            
            # Add text before this entity
            if offset > last_offset:
                reconstructed += text[last_offset:offset]
            
            # Get the entity text
            entity_text = text[offset:offset + length]
            
            if entity_type == 'custom_emoji' and entity.get('custom_emoji_id'):
                # For custom emojis, we'll use a special format that Telethon can understand
                custom_emoji_id = entity.get('custom_emoji_id')
                # Use the original text but mark it for custom emoji
                reconstructed += entity_text  # Keep original emoji text
                logger.info(f"Preserved custom emoji: {entity_text} (ID: {custom_emoji_id})")
            else:
                # For other entities, just add the text
                reconstructed += entity_text
            
            last_offset = offset + length
        
        # Add remaining text
        if last_offset < len(text):
            reconstructed += text[last_offset:]
        
        logger.info(f"Text reconstruction complete: {len(reconstructed)} chars")
        return reconstructed
    
    def _convert_to_telethon_entities(self, entities, text):
        """Convert Bot API entities to Telethon entities for premium emoji support"""
        if not entities:
            return []
        
        try:
            from telethon.tl.types import (
                MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic,
                MessageEntityTextUrl, MessageEntityHashtag
            )
            
            telethon_entities = []
            
            for entity in entities:
                entity_type = entity.get('type', '')
                offset = entity.get('offset', 0)
                length = entity.get('length', 0)
                
                # Skip if offset/length would be out of bounds
                if offset + length > len(text):
                    continue
                
                if entity_type == 'custom_emoji' and entity.get('custom_emoji_id'):
                    # This is the key for premium emojis!
                    custom_emoji_id = int(entity.get('custom_emoji_id'))
                    telethon_entity = MessageEntityCustomEmoji(
                        offset=offset,
                        length=length,
                        document_id=custom_emoji_id
                    )
                    telethon_entities.append(telethon_entity)
                    logger.info(f"Converted custom emoji entity: offset={offset}, length={length}, id={custom_emoji_id}")
                
                elif entity_type == 'bold':
                    telethon_entities.append(MessageEntityBold(offset=offset, length=length))
                
                elif entity_type == 'italic':
                    telethon_entities.append(MessageEntityItalic(offset=offset, length=length))
                
                elif entity_type == 'text_link' and entity.get('url'):
                    telethon_entities.append(MessageEntityTextUrl(
                        offset=offset, length=length, url=entity.get('url')
                    ))
                
                elif entity_type == 'hashtag':
                    telethon_entities.append(MessageEntityHashtag(offset=offset, length=length))
            
            logger.info(f"Converted {len(telethon_entities)} entities for Telethon")
            return telethon_entities
            
        except Exception as e:
            logger.error(f"Failed to convert entities to Telethon format: {e}")
            return []
    
    # Removed _add_buttons_to_text - now using inline buttons directly
    
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
                    schedule_time: str, buttons=None, target_mode='specific', immediate_start=False) -> int:
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
                
                # Execute immediately if requested
                if immediate_start:
                    logger.info(f"🚀 Running campaign {campaign_id} immediately on creation")
                    # Run the campaign execution in a separate thread to not block
                    threading.Thread(
                        target=self._run_campaign_immediately, 
                        args=(campaign_id,),
                        daemon=True
                    ).start()
                
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
    
    def _run_campaign_immediately(self, campaign_id: int):
        """Run campaign immediately in a separate thread"""
        try:
            logger.info(f"🚀 Starting immediate execution of campaign {campaign_id}")
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the campaign execution
                loop.run_until_complete(self._execute_campaign_async(campaign_id))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Immediate campaign execution failed for {campaign_id}: {e}")
    
    async def _execute_campaign_async(self, campaign_id: int):
        """Execute campaign asynchronously - same logic as scheduled execution"""
        try:
            # Get campaign data
            campaign = self.db.get_campaign(campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"🚀 Executing immediate campaign {campaign_id}: {campaign['campaign_name']}")
            
            # Use the existing campaign execution logic
            await self._async_send_ad(campaign_id)
            
            logger.info(f"✅ Immediate campaign {campaign_id} executed successfully")
            
        except Exception as e:
            logger.error(f"❌ Immediate campaign execution failed for {campaign_id}: {e}")
    
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
        
        # 🎯 AUTO-JOIN STORAGE CHANNEL: Ensure worker account can access storage channel
        try:
            from config import Config
            storage_channel_id = Config.STORAGE_CHANNEL_ID
            
            if storage_channel_id:
                logger.info(f"🔄 AUTO-JOIN: Ensuring worker account has access to storage channel {storage_channel_id}")
                
                # Convert string ID to integer for Telethon
                try:
                    if isinstance(storage_channel_id, str):
                        if storage_channel_id.startswith('-100'):
                            # Full channel ID format: -1001234567890
                            channel_id_int = int(storage_channel_id)
                        elif storage_channel_id.startswith('-'):
                            # Short format: -1234567890, convert to full format
                            channel_id_int = int('-100' + storage_channel_id[1:])
                        else:
                            # Positive number, convert to negative channel ID
                            channel_id_int = int('-100' + storage_channel_id)
                    else:
                        channel_id_int = int(storage_channel_id)
                    
                    logger.info(f"🔄 Using channel ID: {channel_id_int}")
                    
                    # Try to get channel info
                    storage_channel = await client.get_entity(channel_id_int)
                    logger.info(f"✅ Storage channel access confirmed: {storage_channel.title}")
                    
                except Exception as access_error:
                    logger.warning(f"⚠️ Cannot access storage channel with ID {channel_id_int}: {access_error}")
                    
                    # 🔄 TELETHON SESSION REFRESH: If worker is member but Telethon can't find channel, refresh session
                    if "Cannot find any entity" in str(access_error):
                        logger.warning(f"🔄 TELETHON SESSION ISSUE: Worker is member but session cache is stale")
                        logger.warning(f"💡 SOLUTION: Force session refresh by getting dialogs")
                        
                        try:
                            # Force Telethon to refresh its entity cache by getting dialogs
                            logger.info(f"🔄 Refreshing Telethon session cache...")
                            dialogs = await client.get_dialogs(limit=50)
                            logger.info(f"✅ Session refreshed: Found {len(dialogs)} dialogs")
                            
                            # Try accessing storage channel again after refresh
                            storage_channel = await client.get_entity(channel_id_int)
                            logger.info(f"✅ Storage channel access confirmed after session refresh: {storage_channel.title}")
                            
                        except Exception as refresh_error:
                            logger.warning(f"❌ Session refresh failed: {refresh_error}")
                            
                            # Try alternative ID formats as fallback
                            alternative_ids = []
                            if isinstance(storage_channel_id, str) and storage_channel_id.startswith('-100'):
                                # Try without -100 prefix
                                alt_id = int(storage_channel_id[4:])  # Remove -100 prefix
                                alternative_ids.append(alt_id)
                                alternative_ids.append(-alt_id)  # Try negative version
                            
                            for alt_id in alternative_ids:
                                try:
                                    logger.info(f"🔄 Trying alternative channel ID after refresh: {alt_id}")
                                    storage_channel = await client.get_entity(alt_id)
                                    logger.info(f"✅ Storage channel access confirmed with alternative ID {alt_id}: {storage_channel.title}")
                                    break
                                except Exception as alt_error:
                                    logger.warning(f"❌ Alternative ID {alt_id} failed: {alt_error}")
                            else:
                                logger.warning(f"❌ All channel access methods failed")
                                logger.warning(f"💡 If worker account is a member, this is a Telethon session cache issue")
                                logger.warning(f"💡 Consider restarting the service to refresh session files")
                    else:
                        logger.warning(f"❌ Channel access failed with non-entity error: {access_error}")
            else:
                logger.info(f"⚠️ STORAGE_CHANNEL_ID not configured - skipping auto-join")
                
        except Exception as storage_setup_error:
            logger.error(f"❌ Storage channel setup failed: {storage_setup_error}")
            # Continue anyway - this is not critical for basic functionality
        
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
        logger.info(f"🚀 Starting _async_send_ad for campaign {campaign_id}")
        
        try:
            campaign = self.get_campaign(campaign_id)
            if not campaign or not campaign['is_active']:
                logger.warning(f"Campaign {campaign_id} not found or inactive")
                return
        except Exception as e:
            logger.error(f"🚨 Failed to get campaign {campaign_id}: {e}")
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
        buttons_sent_count = 0
        
        # Handle ALL_WORKER_GROUPS - get actual groups
        if target_chats == ['ALL_WORKER_GROUPS']:
            logger.info("Getting all groups for scheduled campaign " + str(campaign_id))
            dialogs = await client.get_dialogs()
            target_entities = []
            for dialog in dialogs:
                if dialog.is_group and not dialog.is_channel:
                    target_entities.append(dialog.entity)
                    logger.info(f"Found group for scheduled send: {dialog.title}")
        else:
            # Convert target chat IDs to entities
            target_entities = []
            for chat_id in target_chats:
                try:
                    entity = await client.get_entity(int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id)
                    target_entities.append(entity)
                except Exception as e:
                    logger.error(f"Failed to get entity for {chat_id}: {e}")
        
        if not target_entities:
            logger.warning(f"No valid target groups found for campaign {campaign_id}")
            await client.disconnect()
            return
        
        # Get caption text once
        caption_text = ad_content.get('caption') or ad_content.get('text', '')

        # Convert DB buttons to Telethon buttons once
        telethon_buttons = None
        if buttons and len(buttons) > 0:
            telethon_buttons = []
            current_row = []
            for i, button_data in enumerate(buttons):
                if button_data.get('url'):
                    current_row.append(Button.url(button_data['text'], button_data['url']))
                    if len(current_row) == 2 or i == len(buttons) - 1:
                        telethon_buttons.append(current_row)
                        current_row = []
            logger.info(f"✅ Constructed {len(buttons)} Telethon buttons from database")

        # Convert database entities to Telethon entities for premium emojis once
        telethon_entities = []
        if ad_content.get('caption_entities'):
            for entity in ad_content.get('caption_entities', []):
                try:
                    entity_type = str(entity.get('type')).lower().replace('messageentitytype.', '')
                    
                    if entity_type == 'custom_emoji' and entity.get('custom_emoji_id'):
                        from telethon.tl.types import MessageEntityCustomEmoji
                        telethon_entities.append(MessageEntityCustomEmoji(
                            offset=entity['offset'],
                            length=entity['length'],
                            document_id=int(entity['custom_emoji_id'])
                        ))
                    elif entity_type == 'bold':
                        from telethon.tl.types import MessageEntityBold
                        telethon_entities.append(MessageEntityBold(
                            offset=entity['offset'],
                            length=entity['length']
                        ))
                    elif entity_type == 'italic':
                        from telethon.tl.types import MessageEntityItalic
                        telethon_entities.append(MessageEntityItalic(
                            offset=entity['offset'],
                            length=entity['length']
                        ))
                    elif entity_type == 'mention':
                        from telethon.tl.types import MessageEntityMention
                        telethon_entities.append(MessageEntityMention(
                            offset=entity['offset'],
                            length=entity['length']
                        ))
                except Exception as entity_error:
                    logger.warning(f"Failed to convert entity {entity}: {entity_error}")
            logger.info(f"✅ Converted {len(telethon_entities)} Telethon entities from database")

        # Main loop for sending messages to target groups
        for chat_entity in target_entities:
            try:
                # Get the media message from storage channel
                storage_message_id = ad_content.get('storage_message_id')
                storage_chat_id = ad_content.get('storage_chat_id')
                storage_chat_id_int = int(storage_chat_id) if isinstance(storage_chat_id, str) else storage_chat_id
                storage_message = await client.get_messages(storage_chat_id_int, ids=storage_message_id)

                if not storage_message or not storage_message.media:
                    logger.error(f"❌ Could not retrieve media from storage for chat {getattr(chat_entity, 'title', 'Unknown')}. Skipping.")
                    continue
                
                logger.info(f"📤 Sending message with all components to {getattr(chat_entity, 'title', 'Unknown')}")

                # Send a NEW message with all components
                logger.info(f"🔍 DEBUG: Sending with {len(telethon_buttons) if telethon_buttons else 0} button rows")
                logger.info(f"🔍 DEBUG: Button data: {telethon_buttons}")
                
                # Try using the storage message's text and entities directly
                # This should preserve premium emojis from the storage message
                if hasattr(storage_message, 'text') and storage_message.text:
                    # Storage message has text (caption stored as text)
                    sent_msg = await client.send_file(
                        chat_entity,
                        storage_message.media,
                        caption=storage_message.text,
                        caption_entities=storage_message.entities,
                        buttons=telethon_buttons,
                        parse_mode=None,
                        link_preview=False
                    )
                else:
                    # Fallback: use plain caption with buttons
                    sent_msg = await client.send_file(
                        chat_entity,
                        storage_message.media,
                        caption=caption_text,
                        buttons=telethon_buttons,
                        parse_mode=None,
                        link_preview=False
                    )
                
                # Check if the sent message actually has buttons
                if hasattr(sent_msg, 'reply_markup') and sent_msg.reply_markup:
                    logger.info(f"✅ SUCCESS: Sent message to {getattr(chat_entity, 'title', 'Unknown')} WITH buttons!")
                    logger.info(f"🔍 DEBUG: Reply markup type: {type(sent_msg.reply_markup)}")
                else:
                    logger.warning(f"⚠️ Message sent to {getattr(chat_entity, 'title', 'Unknown')} but NO buttons in final message!")
                    logger.info(f"🔍 DEBUG: sent_msg attributes: {dir(sent_msg)}")
                
                sent_count += 1
                if telethon_buttons:
                    buttons_sent_count += 1

            except Exception as e:
                logger.error(f"Failed to send scheduled ad to {getattr(chat_entity, 'title', 'Unknown')}: {e}")
                self.log_ad_performance(campaign_id, campaign['user_id'], str(chat_entity.id) if hasattr(chat_entity, 'id') else 'unknown', None, 'failed')
        
        # Update campaign statistics
        self.update_campaign_stats(campaign_id, sent_count)
        logger.info(f"Scheduled campaign {campaign['campaign_name']} completed: {buttons_sent_count}/{len(target_chats)} ads sent with buttons")
        
        # Disconnect client after scheduled execution
        await client.disconnect()
        logger.info(f"Disconnected client for scheduled campaign {campaign_id}")
        
        return
        
    def _get_schedule_func(self, schedule_type: str, schedule_time: str) -> Optional[callable]:
        """Helper to get the appropriate schedule function based on type."""
        if schedule_type == 'daily':
            return schedule.every().day.at(schedule_time).do
        elif schedule_type == 'weekly':
            # Assuming format like "Monday 14:30"
            day, time_str = schedule_time.split(' ')
            return getattr(schedule.every(), day.lower()).at(time_str).do
        elif schedule_type == 'hourly':
            return schedule.every().hour.do
        elif schedule_type == 'custom':
            # Parse custom interval (e.g., "every 3 minutes", "every 4 hours")
            try:
                if 'hour' in schedule_time.lower():
                    hours = int(schedule_time.split()[1])
                    return schedule.every(hours).hours.do
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
                    
                    return schedule.every(minutes).minutes.do
                elif schedule_time.isdigit():
                    # If just a number, assume minutes
                    minutes = int(schedule_time)
                    return schedule.every(minutes).minutes.do
                else:
                    logger.warning(f"⚠️ Unknown custom schedule format: {schedule_time}")
                    return None
            except (ValueError, IndexError) as e:
                logger.error(f"❌ Error parsing custom schedule '{schedule_time}': {e}")
                # Default to 10 minutes if parsing fails
                return schedule.every(10).minutes.do
        return None
        
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
        
        schedule_func = self._get_schedule_func(schedule_type, schedule_time)
        
        if not schedule_func:
            logger.warning(f"⚠️ Could not determine schedule function for campaign {campaign_id} ({schedule_type} at {schedule_time})")
            return
        
        job = schedule_func(self.run_campaign_job, campaign_id)
        
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
        
        logger.info(f"📅 Campaign {campaign_id} scheduled ({schedule_type} at {schedule_time})")
        
        self.active_campaigns[campaign_id] = campaign
    
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
