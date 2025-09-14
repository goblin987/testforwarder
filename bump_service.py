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

logger = logging.getLogger(__name__)

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
        self.init_bump_database()
    
    def init_bump_database(self):
        """Initialize bump service database tables"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        
        # Convert ad_content to JSON string if it's a list or dict
        if isinstance(ad_content, (list, dict)):
            ad_content_str = json.dumps(ad_content)
        else:
            ad_content_str = str(ad_content)
        
        # Convert target_chats to JSON string
        target_chats_str = json.dumps(target_chats) if isinstance(target_chats, list) else str(target_chats)
        
        # Convert buttons to JSON string
        buttons_str = json.dumps(buttons) if buttons else None
        
        with sqlite3.connect(self.db.db_path) as conn:
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
            logger.info(f"Added campaign {campaign_id}: {campaign_name} with content type: {type(ad_content)}, buttons: {len(buttons) if buttons else 0}")
            return campaign_id
    
    def get_user_campaigns(self, user_id: int) -> List[Dict]:
        """Get all campaigns for a user"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        """Update campaign details"""
        import sqlite3
        
        allowed_fields = ['campaign_name', 'ad_content', 'target_chats', 
                         'schedule_type', 'schedule_time', 'is_active']
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'target_chats':
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                values.append(value)
        
        if updates:
            values.append(campaign_id)
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE ad_campaigns 
                    SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                conn.commit()
    
    def delete_campaign(self, campaign_id: int):
        """Permanently delete campaign from database and clean up scheduler"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
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
    
    async def initialize_telegram_client(self, account_id: int) -> Optional[TelegramClient]:
        """Initialize Telegram client for ad posting"""
        if account_id in self.telegram_clients:
            return self.telegram_clients[account_id]
        
        account = self.db.get_account(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return None
        
        try:
            # Handle uploaded sessions (no API credentials needed)
            if account['api_id'] == 'uploaded' or account['api_hash'] == 'uploaded':
                api_id = 123456  # Dummy API ID
                api_hash = 'dummy_hash_for_uploaded_sessions'  # Dummy API Hash
            else:
                try:
                    api_id = int(account['api_id'])
                    api_hash = account['api_hash']
                except ValueError:
                    logger.error(f"Invalid API credentials for account {account_id}: api_id={account['api_id']}, api_hash={account['api_hash']}")
                    return None
            
            session_name = f'bump_session_{account_id}'
            client = TelegramClient(session_name, api_id, api_hash)
            
            if account['session_string']:
                # Use the same session handling logic as bot.py for consistency
                try:
                    import base64
                    import os
                    session_file = f"{session_name}.session"
                    
                    # Handle uploaded sessions vs API credential sessions (same as bot.py)
                    if account['api_id'] == 'uploaded' or account['api_hash'] == 'uploaded':
                        # For uploaded sessions, decode and save the session file
                        session_data = base64.b64decode(account['session_string'])
                        with open(session_file, "wb") as f:
                            f.write(session_data)
                    else:
                        # For API credential accounts with authenticated sessions
                        # Session string is base64 encoded session file data
                        session_data = base64.b64decode(account['session_string'])
                        with open(session_file, "wb") as f:
                            f.write(session_data)
                    
                    # Start the client with the session file
                    await client.start()
                    
                    # Verify the session is valid (same as bot.py)
                    me = await client.get_me()
                    if not me:
                        logger.error(f"Session invalid for account {account_id}")
                        await client.disconnect()
                        return None
                        
                    logger.info(f"Successfully authenticated as {me.username or me.phone}")
                    
                except Exception as e:
                    logger.error(f"Failed to start session for account {account_id}: {e}")
                    logger.error(f"Account {account_id} needs to be re-added with fresh credentials")
                    
                    # Clean up corrupted session file
                    try:
                        if os.path.exists(session_file):
                            os.remove(session_file)
                            logger.info(f"Cleaned up corrupted session file for account {account_id}")
                    except:
                        pass
                    
                    return None
            else:
                logger.error(f"Account {account_id} has no session string. Please authenticate the account.")
                return None
            
            self.telegram_clients[account_id] = client
            logger.info(f"Telegram client initialized for bump service (Account: {account_id})")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize client for account {account_id}: {e}")
            return None
    
    async def send_ad(self, campaign_id: int):
        """Send ad for a specific campaign with button support"""
        campaign = self.get_campaign(campaign_id)
        if not campaign or not campaign['is_active']:
            logger.warning(f"Campaign {campaign_id} not found or inactive")
            return
        
        # Get account info for logging
        account = self.db.get_account(campaign['account_id'])
        account_name = account['account_name'] if account else f"Account_{campaign['account_id']}"
        
        logger.info(f"🚀 Starting campaign {campaign['campaign_name']} using {account_name}")
        
        client = await self.initialize_telegram_client(campaign['account_id'])
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
                    # Multiple messages (forwarded content)
                    for i, message_data in enumerate(ad_content):
                        # Only add buttons to the last message
                        buttons_for_message = telethon_buttons if i == len(ad_content) - 1 else None
                        
                        if message_data.get('media_type'):
                            # Send media message
                            message = await client.send_file(
                                chat_entity,
                                message_data['file_id'],
                                caption=message_data.get('caption', message_data.get('text', '')),
                                buttons=buttons_for_message
                            )
                        else:
                            # Send text message with buttons
                            message = await client.send_message(
                                chat_entity,
                                message_data.get('text', ''),
                                buttons=buttons_for_message
                            )
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
    
    def log_ad_performance(self, campaign_id: int, user_id: int, target_chat: str, 
                          message_id: Optional[int], status: str = 'sent'):
        """Log ad performance"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        
        with sqlite3.connect(self.db.db_path) as conn:
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
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: self.run_campaign_job(campaign_id), daemon=True).start()
                    
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
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: self.run_campaign_job(campaign_id), daemon=True).start()
                    
                    logger.info(f"📅 Campaign {campaign_id} scheduled every {minutes} minutes")
                elif schedule_time.isdigit():
                    # If just a number, assume minutes
                    minutes = int(schedule_time)
                    job = schedule.every(minutes).minutes.do(self.run_campaign_job, campaign_id)
                    
                    # IMPORTANT: Run the job immediately for the first time if campaign is active
                    campaign = self.get_campaign(campaign_id)
                    if campaign and campaign.get('is_active', False):
                        logger.info(f"🚀 Running campaign {campaign_id} immediately on schedule activation")
                        # Run in a separate thread to avoid blocking
                        import threading
                        threading.Thread(target=lambda: self.run_campaign_job(campaign_id), daemon=True).start()
                    
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
            
            # Initialize Telegram client
            client = await self.initialize_telegram_client(campaign['account_id'])
            if not client:
                logger.error(f"Failed to initialize client for scheduled campaign {campaign_id}")
                logger.error(f"Account '{account.get('account_name', 'Unknown')}' needs to be deleted and re-added with phone verification")
                return False
            
            # Send the ad (send_ad method doesn't need client parameter)
            await self.send_ad(campaign_id)
            logger.info(f"✅ Scheduled campaign {campaign_id} executed successfully")
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing scheduled campaign {campaign_id}: {e}")
            return False
    
    def start_scheduler(self):
        """Start the campaign scheduler with proper background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🚀 Bump service scheduler started (automatic execution mode)")
        
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
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        
        with sqlite3.connect(self.db.db_path) as conn:
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
        
        client = await self.initialize_telegram_client(campaign['account_id'])
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
