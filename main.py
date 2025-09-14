#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from bot import TgcfBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tgcf.log')
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    # Clean up resources before exiting
    try:
        if 'bot' in globals():
            bot.cleanup_resources()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    sys.exit(0)

def main():
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and run bot
        bot = TgcfBot()
        logger.info("Starting TgCF Bot...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
