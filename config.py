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
    
    # Storage Channel Configuration (for persistent media storage)
    STORAGE_CHANNEL_ID = os.getenv('STORAGE_CHANNEL_ID')  # Private channel for storing media files
    
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
    
    # Error Handling Configuration - YOLO MODE OPTIMIZED
    MAX_RETRY_ATTEMPTS = 5  # More aggressive retries
    RETRY_DELAY_BASE = 1.5  # Faster retry intervals
    CLIENT_VALIDATION_TIMEOUT = 15  # Faster validation
    CONNECTION_TIMEOUT = 30  # Faster timeouts
    
    # Session Management - YOLO MODE
    SESSION_VALIDATION_INTERVAL = 120  # 2 minutes - more frequent validation
    AUTO_RECONNECT_ENABLED = True
    AGGRESSIVE_MODE = True  # YOLO MODE FLAG
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🚀 SCALING CONFIGURATION for 50+ Accounts
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Campaign Execution Queue Settings
    MAX_CONCURRENT_CAMPAIGNS = int(os.getenv('MAX_CONCURRENT_CAMPAIGNS', 5))  # Max campaigns running at once
    EXECUTION_QUEUE_SIZE = int(os.getenv('EXECUTION_QUEUE_SIZE', 100))  # Max campaigns in queue
    EXECUTION_WORKER_THREADS = int(os.getenv('EXECUTION_WORKER_THREADS', 5))  # Worker threads
    
    # Client Memory Management
    CLIENT_IDLE_TIMEOUT = int(os.getenv('CLIENT_IDLE_TIMEOUT', 300))  # Close clients idle for 5 min
    CLIENT_CLEANUP_INTERVAL = int(os.getenv('CLIENT_CLEANUP_INTERVAL', 60))  # Check every 1 min
    ENABLE_CLIENT_CLEANUP = os.getenv('ENABLE_CLIENT_CLEANUP', 'true').lower() == 'true'
    
    # Resource Monitoring
    ENABLE_RESOURCE_MONITORING = os.getenv('ENABLE_RESOURCE_MONITORING', 'true').lower() == 'true'
    RESOURCE_LOG_INTERVAL = int(os.getenv('RESOURCE_LOG_INTERVAL', 60))  # Log every 1 min
    MEMORY_WARNING_THRESHOLD_MB = int(os.getenv('MEMORY_WARNING_THRESHOLD_MB', 4096))  # Warn at 4GB
    
    # Campaign Schedule Staggering
    ENABLE_AUTO_STAGGER = os.getenv('ENABLE_AUTO_STAGGER', 'true').lower() == 'true'
    STAGGER_SECONDS_PER_CAMPAIGN = int(os.getenv('STAGGER_SECONDS_PER_CAMPAIGN', 10))  # 10s between each
    
    # Database Connection Pooling
    DB_CONNECTION_POOL_SIZE = int(os.getenv('DB_CONNECTION_POOL_SIZE', 10))
    DB_MAX_RETRIES = int(os.getenv('DB_MAX_RETRIES', 5))
    DB_RETRY_DELAY = float(os.getenv('DB_RETRY_DELAY', 1.0))
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🛡️ ANTI-BAN SYSTEM - Telegram Account Protection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Message Sending Delays (CRITICAL FOR AVOIDING BANS)
    # OPTIMIZED FOR MATURE ACCOUNTS (2023): Fast burst sending with LONG breaks
    MIN_DELAY_BETWEEN_MESSAGES = int(os.getenv('MIN_DELAY_BETWEEN_MESSAGES', 30))  # 30 seconds (burst mode)
    MAX_DELAY_BETWEEN_MESSAGES = int(os.getenv('MAX_DELAY_BETWEEN_MESSAGES', 90))  # 90 seconds (1.5 min)
    
    # Account Daily Limits (DISABLED for mature accounts from 2023)
    MAX_MESSAGES_PER_DAY_NEW_ACCOUNT = int(os.getenv('MAX_MESSAGES_PER_DAY_NEW_ACCOUNT', 20))  # First 2 weeks (conservative)
    MAX_MESSAGES_PER_DAY_WARMED_ACCOUNT = int(os.getenv('MAX_MESSAGES_PER_DAY_WARMED_ACCOUNT', 60))  # After 2 weeks (realistic)
    MAX_MESSAGES_PER_DAY_MATURE_ACCOUNT = int(os.getenv('MAX_MESSAGES_PER_DAY_MATURE_ACCOUNT', 9999))  # Unlimited for mature accounts (2023)
    DISABLE_DAILY_LIMITS_FOR_MATURE = os.getenv('DISABLE_DAILY_LIMITS_FOR_MATURE', 'true').lower() == 'true'  # No cap for 2023 accounts
    
    # Account Warm-Up Period (days)
    ACCOUNT_WARM_UP_DAYS = int(os.getenv('ACCOUNT_WARM_UP_DAYS', 14))  # 2 weeks
    ACCOUNT_MATURE_DAYS = int(os.getenv('ACCOUNT_MATURE_DAYS', 30))  # 1 month
    
    # Session Cooldown (Every ~1 hour with randomization for unpredictable timing)
    MIN_COOLDOWN_BETWEEN_CAMPAIGNS_MINUTES = int(os.getenv('MIN_COOLDOWN_BETWEEN_CAMPAIGNS_MINUTES', 60))  # 1 hour base
    MAX_COOLDOWN_BETWEEN_CAMPAIGNS_MINUTES = int(os.getenv('MAX_COOLDOWN_BETWEEN_CAMPAIGNS_MINUTES', 84))  # 1.4 hours max
    # Random between 60-84 minutes = 1.0 to 1.4 hours (unpredictable!)
    
    # Break Simulation (NIGHT SLEEP ONLY - Lithuanian timezone)
    ENABLE_RANDOM_BREAKS = os.getenv('ENABLE_RANDOM_BREAKS', 'true').lower() == 'true'
    NIGHT_BREAK_START_HOUR = int(os.getenv('NIGHT_BREAK_START_HOUR', 3))  # 3:00 AM Lithuanian time
    NIGHT_BREAK_END_HOUR = int(os.getenv('NIGHT_BREAK_END_HOUR', 6))  # 6:00 AM Lithuanian time
    NIGHT_BREAK_TIMEZONE = os.getenv('NIGHT_BREAK_TIMEZONE', 'Europe/Vilnius')  # Lithuanian timezone
    MIN_BREAK_DURATION_MINUTES = int(os.getenv('MIN_BREAK_DURATION_MINUTES', 120))  # 2 hour sleep
    MAX_BREAK_DURATION_MINUTES = int(os.getenv('MAX_BREAK_DURATION_MINUTES', 180))  # 3 hour sleep
    BREAK_PROBABILITY = float(os.getenv('BREAK_PROBABILITY', 1.0))  # 100% chance during night hours (simulate sleep)
    
    # Account Age Tracking
    ENABLE_ACCOUNT_AGE_LIMITS = os.getenv('ENABLE_ACCOUNT_AGE_LIMITS', 'true').lower() == 'true'
    
    # Human Activity Simulation (appear more natural)
    ENABLE_HUMAN_ACTIVITY_SIMULATION = os.getenv('ENABLE_HUMAN_ACTIVITY_SIMULATION', 'true').lower() == 'true'
    HUMAN_ACTIVITY_PROBABILITY = float(os.getenv('HUMAN_ACTIVITY_PROBABILITY', 0.10))  # 10% chance to send normal message
    HUMAN_ACTIVITY_MESSAGES = [
        "👍", "Thanks!", "Interesting", "Good point", "Agreed", "Nice!", 
        "Cool", "👏", "Great!", "Awesome"
    ]
    
    # Warm-Up Mode (for account recovery after bans)
    ENABLE_WARMUP_MODE = os.getenv('ENABLE_WARMUP_MODE', 'false').lower() == 'true'  # Enable manually when recovering
    WARMUP_DURATION_DAYS = int(os.getenv('WARMUP_DURATION_DAYS', 7))  # 1 week warm-up
    WARMUP_MAX_MESSAGES_PER_DAY = int(os.getenv('WARMUP_MAX_MESSAGES_PER_DAY', 10))  # Very conservative
    WARMUP_MIN_DELAY_MINUTES = int(os.getenv('WARMUP_MIN_DELAY_MINUTES', 30))  # 30 min delays in warm-up
    
    # Safety Mode (enforces all limits strictly)
    SAFETY_MODE = os.getenv('SAFETY_MODE', 'burst').lower()  # 'strict', 'moderate', 'burst' (for mature accounts)
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = ['BOT_TOKEN']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
