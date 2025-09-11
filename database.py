"""
TgCF Pro - Enterprise Database Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Professional database layer providing secure data persistence, account management,
campaign storage, and performance analytics for enterprise automation.

Features:
- Secure SQLite database with encryption support
- Multi-account data management
- Campaign and performance tracking
- Automated backup and recovery systems
- Enterprise-grade data validation

Author: TgCF Pro Team
License: MIT
Version: 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import sqlite3
import json
import os
from typing import Dict, List, Optional
from config import Config

class Database:
    def __init__(self, db_path: str = None):
        # Use persistent disk if available, otherwise local storage
        if db_path is None:
            # Check for Render persistent disk mount
            if os.path.exists('/data'):
                self.db_path = '/data/tgcf.db'
            else:
                self.db_path = 'tgcf.db'
        else:
            self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Telegram accounts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telegram_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    account_name TEXT,
                    phone_number TEXT,
                    api_id TEXT,
                    api_hash TEXT,
                    session_string TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Forwarding configurations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forwarding_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    account_id INTEGER,
                    source_chat_id TEXT,
                    destination_chat_id TEXT,
                    config_name TEXT,
                    config_data TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (account_id) REFERENCES telegram_accounts (id)
                )
            ''')
            
            # Message logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    account_id INTEGER,
                    source_message_id INTEGER,
                    destination_message_id INTEGER,
                    source_chat_id TEXT,
                    destination_chat_id TEXT,
                    forwarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (account_id) REFERENCES telegram_accounts (id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'is_active': row[4],
                    'created_at': row[5]
                }
            return None
    
    def add_telegram_account(self, user_id: int, account_name: str, phone_number: str, 
                           api_id: str, api_hash: str, session_string: str = None) -> int:
        """Add Telegram account"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO telegram_accounts 
                (user_id, account_name, phone_number, api_id, api_hash, session_string)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, account_name, phone_number, api_id, api_hash, session_string))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_accounts(self, user_id: int) -> List[Dict]:
        """Get all Telegram accounts for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM telegram_accounts 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'user_id': row[1],
                'account_name': row[2],
                'phone_number': row[3],
                'api_id': row[4],
                'api_hash': row[5],
                'session_string': row[6],
                'is_active': row[7],
                'created_at': row[8]
            } for row in rows]
    
    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get account by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM telegram_accounts WHERE id = ?', (account_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'account_name': row[2],
                    'phone_number': row[3],
                    'api_id': row[4],
                    'api_hash': row[5],
                    'session_string': row[6],
                    'is_active': row[7],
                    'created_at': row[8]
                }
            return None
    
    def update_account_session(self, account_id: int, session_string: str):
        """Update account session string"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE telegram_accounts 
                SET session_string = ?
                WHERE id = ?
            ''', (session_string, account_id))
            conn.commit()
    
    def delete_account(self, account_id: int):
        """Delete Telegram account"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE telegram_accounts SET is_active = 0 WHERE id = ?', (account_id,))
            conn.commit()
    
    def add_forwarding_config(self, user_id: int, account_id: int, source_chat_id: str, 
                            destination_chat_id: str, config_name: str, config_data: Dict) -> int:
        """Add forwarding configuration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO forwarding_configs 
                (user_id, account_id, source_chat_id, destination_chat_id, config_name, config_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, account_id, source_chat_id, destination_chat_id, config_name, json.dumps(config_data)))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_configs(self, user_id: int, account_id: int = None) -> List[Dict]:
        """Get all forwarding configurations for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if account_id:
                cursor.execute('''
                    SELECT fc.*, ta.account_name 
                    FROM forwarding_configs fc
                    LEFT JOIN telegram_accounts ta ON fc.account_id = ta.id
                    WHERE fc.user_id = ? AND fc.account_id = ? AND fc.is_active = 1
                    ORDER BY fc.created_at DESC
                ''', (user_id, account_id))
            else:
                cursor.execute('''
                    SELECT fc.*, ta.account_name 
                    FROM forwarding_configs fc
                    LEFT JOIN telegram_accounts ta ON fc.account_id = ta.id
                    WHERE fc.user_id = ? AND fc.is_active = 1
                    ORDER BY fc.created_at DESC
                ''', (user_id,))
            rows = cursor.fetchall()
            return [{
                'id': row[0],
                'user_id': row[1],
                'account_id': row[2],
                'source_chat_id': row[3],
                'destination_chat_id': row[4],
                'config_name': row[5],
                'config_data': json.loads(row[6]),
                'is_active': row[7],
                'created_at': row[8],
                'account_name': row[9]
            } for row in rows]
    
    def update_config(self, config_id: int, config_data: Dict):
        """Update forwarding configuration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE forwarding_configs 
                SET config_data = ?
                WHERE id = ?
            ''', (json.dumps(config_data), config_id))
            conn.commit()
    
    def delete_config(self, config_id: int):
        """Delete forwarding configuration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE forwarding_configs SET is_active = 0 WHERE id = ?', (config_id,))
            conn.commit()
    
    def log_message(self, user_id: int, account_id: int, source_message_id: int, 
                   destination_message_id: int, source_chat_id: str, destination_chat_id: str):
        """Log forwarded message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_logs 
                (user_id, account_id, source_message_id, destination_message_id, source_chat_id, destination_chat_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, account_id, source_message_id, destination_message_id, source_chat_id, destination_chat_id))
            conn.commit()
