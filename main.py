#!/usr/bin/env python3
\"\"\"
TgCF Pro - Enterprise Telegram Automation Bot
?

Professional-grade Telegram automation solution for business messaging 
and advertising campaigns.

Main Application Entry Point

Author: TgCF Pro Team
License: MIT
Version: 1.0.0

\"\"\"

import asyncio
import logging
import signal
import sys
import threading
from aiohttp import web, web_runner
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

async def health_check(request):
    \"\"\"Health check endpoint for Render\"\"\"
    return web.json_response({
        'status': 'healthy',
        'service': 'TgCF Pro Bot',
        'version': '1.0.0'
    })

async def status(request):
    \"\"\"Status endpoint\"\"\"
    return web.json_response({
        'bot': 'running',
        'service': 'TgCF Pro - Enterprise Telegram Automation',
        'features': [
            'Multi-Account Management',
            'Smart Bump Service',
            'Message Forwarding',
            'Campaign Analytics'
        ]
    })

async def start_web_server():
    \"\"\"Start web server for Render port binding\"\"\"
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status)
    
    port = Config.WEB_PORT
    runner = web_runner.AppRunner(app)
    await runner.setup()
    
    site = web_runner.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f\"Web server started on port {port}\")
    return runner

def signal_handler(signum, frame):
    \"\"\"Handle shutdown signals\"\"\"
    logger.info(f\"Received signal {signum}, shutting down...\")
    sys.exit(0)

async def main_async():
    \"\"\"Main async application entry point\"\"\"
    try:
        # Validate configuration
        Config.validate()
        logger.info(\"Configuration validated successfully\")
        
        # Start web server for Render
        web_runner_instance = await start_web_server()
        
        # Create and start bot in a separate thread
        bot = TgcfBot()
        logger.info(\"Starting TgCF Bot...\")
        
        # Run bot in thread to avoid blocking
        def run_bot():
            bot.run()
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Keep the web server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info(\"Shutting down...\")
        finally:
            await web_runner_instance.cleanup()
            
    except Exception as e:
        logger.error(f\"Fatal error: {e}\")
        sys.exit(1)

def main():
    \"\"\"Main application entry point\"\"\"
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the async main function
    asyncio.run(main_async())

if __name__ == \"__main__\":
    main()
