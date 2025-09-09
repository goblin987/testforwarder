import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Web Interface Configuration
    PASSWORD = os.getenv('PASSWORD', 'hocus pocus qwerty utopia')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
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
