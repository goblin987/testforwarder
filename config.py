"""
TgCF Pro - Configuration Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enterprise configuration management with environment variable validation,
security features, and professional deployment settings.

Features:
- Secure environment variable handling
- Configuration validation and error reporting
- Professional deployment configuration
- Enterprise security settings

Author: TgCF Pro Team
License: MIT
Version: 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Bot Owner Configuration (single user mode)
    OWNER_USER_ID = os.getenv('OWNER_USER_ID')  # Your Telegram user ID (optional)
    
    # Web Interface Configuration
    PASSWORD = os.getenv('PASSWORD', 'hocus pocus qwerty utopia')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Persistent Storage Configuration
    PERSISTENT_DISK_PATH = '/data'  # Render persistent disk mount point
    DATABASE_PATH = os.path.join(PERSISTENT_DISK_PATH, 'tgcf.db') if os.path.exists(PERSISTENT_DISK_PATH) else 'tgcf.db'
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Forwarding Configuration
    MAX_MESSAGES_PER_BATCH = 100
    DELAY_BETWEEN_MESSAGES = 0.1
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = ['BOT_TOKEN']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
