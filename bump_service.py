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
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    total_sends INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (account_id) REFERENCES telegram_accounts (id)
                )
            ''')
            
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
                    ad_content: str, target_chats: List[str], schedule_type: str, 
                    schedule_time: str) -> int:
        """Add new ad campaign"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ad_campaigns 
                (user_id, account_id, campaign_name, ad_content, target_chats, schedule_type, schedule_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, account_id, campaign_name, ad_content, 
                 json.dumps(target_chats), schedule_type, schedule_time))
            conn.commit()
            campaign_id = cursor.lastrowid
            
            # Schedule the campaign
            self.schedule_campaign(campaign_id)
            logger.info(f"Added campaign {campaign_id}: {campaign_name}")
            return campaign_id
    
    def get_user_campaigns(self, user_id: int) -> List[Dict]:
        """Get all campaigns for a user"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ac.*, ta.account_name 
                FROM ad_campaigns ac
                LEFT JOIN telegram_accounts ta ON ac.account_id = ta.id
                WHERE ac.user_id = ? AND ac.is_active = 1
                ORDER BY ac.created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            
            campaigns = []
            for row in rows:
                campaigns.append({
                    'id': row[0],
                    'user_id': row[1],
                    'account_id': row[2],
                    'campaign_name': row[3],
                    'ad_content': row[4],
                    'target_chats': json.loads(row[5]),
                    'schedule_type': row[6],
                    'schedule_time': row[7],
                    'is_active': row[8],
                    'created_at': row[9],
                    'last_run': row[10],
                    'total_sends': row[11],
                    'account_name': row[12]
                })
            return campaigns
    
    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get specific campaign by ID"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ac.*, ta.account_name 
                FROM ad_campaigns ac
                LEFT JOIN telegram_accounts ta ON ac.account_id = ta.id
                WHERE ac.id = ?
            ''', (campaign_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'account_id': row[2],
                    'campaign_name': row[3],
                    'ad_content': row[4],
                    'target_chats': json.loads(row[5]),
                    'schedule_type': row[6],
                    'schedule_time': row[7],
                    'is_active': row[8],
                    'created_at': row[9],
                    'last_run': row[10],
                    'total_sends': row[11],
                    'account_name': row[12]
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
        """Delete campaign"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE ad_campaigns SET is_active = 0 WHERE id = ?', (campaign_id,))
            conn.commit()
            
        # Remove from active campaigns
        if campaign_id in self.active_campaigns:
            del self.active_campaigns[campaign_id]
    
    async def initialize_telegram_client(self, account_id: int) -> Optional[TelegramClient]:
        """Initialize Telegram client for ad posting"""
        if account_id in self.telegram_clients:
            return self.telegram_clients[account_id]
        
        account = self.db.get_account(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return None
        
        try:
            session_name = f'bump_session_{account_id}'
            client = TelegramClient(session_name, account['api_id'], account['api_hash'])
            
            if account['session_string']:
                await client.start(session_string=account['session_string'])
            else:
                await client.start()
                # Save session string
                session_string = client.session.save()
                self.db.update_account_session(account_id, session_string)
            
            self.telegram_clients[account_id] = client
            logger.info(f"Telegram client initialized for bump service (Account: {account_id})")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize client for account {account_id}: {e}")
            return None
    
    async def send_ad(self, campaign_id: int):
        """Send ad for a specific campaign"""
        campaign = self.get_campaign(campaign_id)
        if not campaign or not campaign['is_active']:
            logger.warning(f"Campaign {campaign_id} not found or inactive")
            return
        
        client = await self.initialize_telegram_client(campaign['account_id'])
        if not client:
            logger.error(f"Failed to get client for campaign {campaign_id}")
            return
        
        ad_content = campaign['ad_content']
        target_chats = campaign['target_chats']
        sent_count = 0
        
        for chat in target_chats:
            try:
                # Send the ad
                message = await client.send_message(chat, ad_content)
                
                # Log the performance
                self.log_ad_performance(campaign_id, campaign['user_id'], chat, message.id)
                sent_count += 1
                
                logger.info(f"Ad sent to {chat} for campaign {campaign['campaign_name']}")
                
                # Add delay between sends
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to send ad to {chat}: {e}")
                self.log_ad_performance(campaign_id, campaign['user_id'], chat, None, 'failed')
        
        # Update campaign statistics
        self.update_campaign_stats(campaign_id, sent_count)
        logger.info(f"Campaign {campaign['campaign_name']} completed: {sent_count}/{len(target_chats)} ads sent")
    
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
            # Parse custom interval (e.g., "every 4 hours")
            if 'hour' in schedule_time:
                hours = int(schedule_time.split()[1])
                schedule.every(hours).hours.do(self.run_campaign_job, campaign_id)
            elif 'minute' in schedule_time:
                minutes = int(schedule_time.split()[1])
                schedule.every(minutes).minutes.do(self.run_campaign_job, campaign_id)
        
        self.active_campaigns[campaign_id] = campaign
        logger.info(f"Scheduled campaign {campaign_id} ({schedule_type} at {schedule_time})")
    
    def run_campaign_job(self, campaign_id: int):
        """Job wrapper to run campaign in async context"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_ad(campaign_id))
            loop.close()
        except Exception as e:
            logger.error(f"Error running campaign {campaign_id}: {e}")
    
    def start_scheduler(self):
        """Start the campaign scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def scheduler_loop():
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Bump service scheduler started")
        
        # Load existing campaigns
        self.load_existing_campaigns()
    
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
            cursor.execute('SELECT id FROM ad_campaigns WHERE is_active = 1')
            rows = cursor.fetchall()
            
            for row in rows:
                campaign_id = row[0]
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
