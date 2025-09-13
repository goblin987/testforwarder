#!/usr/bin/env python3
"""
Test script to verify the campaign scheduling and button fixes
"""

import asyncio
import logging
import time
from datetime import datetime
from bump_service import BumpService
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_button_creation():
    """Test button creation logic"""
    logger.info("🧪 Testing button creation...")
    
    bump_service = BumpService()
    
    # Test button parsing
    test_buttons = [
        {"text": "Visit Website", "url": "https://example.com"},
        {"text": "Contact Us", "url": "https://t.me/support"}
    ]
    
    # Create a test campaign
    try:
        campaign_id = bump_service.add_campaign(
            user_id=12345,
            account_id=1,
            campaign_name="Test Campaign",
            ad_content="This is a test message with buttons!",
            target_chats=["@testchannel"],
            schedule_type="custom",
            schedule_time="3 minutes",
            buttons=test_buttons,
            target_mode="specific"
        )
        
        logger.info(f"✅ Test campaign created with ID: {campaign_id}")
        
        # Retrieve the campaign to verify button storage
        campaign = bump_service.get_campaign(campaign_id)
        if campaign:
            logger.info(f"✅ Campaign retrieved successfully")
            logger.info(f"📋 Campaign buttons: {campaign['buttons']}")
            logger.info(f"📅 Schedule: {campaign['schedule_type']} - {campaign['schedule_time']}")
        else:
            logger.error("❌ Failed to retrieve test campaign")
            
        # Clean up
        bump_service.delete_campaign(campaign_id)
        logger.info("🗑️ Test campaign deleted")
        
    except Exception as e:
        logger.error(f"❌ Error testing button creation: {e}")

def test_scheduler():
    """Test scheduler functionality"""
    logger.info("🧪 Testing scheduler functionality...")
    
    bump_service = BumpService()
    
    # Start the scheduler
    bump_service.start_scheduler()
    
    # Check if scheduler is running
    if bump_service.is_running:
        logger.info("✅ Scheduler is running")
        
        # Check if scheduler thread exists
        if bump_service.scheduler_thread and bump_service.scheduler_thread.is_alive():
            logger.info("✅ Scheduler thread is active")
        else:
            logger.warning("⚠️ Scheduler thread not found or not alive")
    else:
        logger.error("❌ Scheduler is not running")
    
    # Stop the scheduler
    bump_service.stop_scheduler()
    logger.info("🛑 Scheduler stopped")

async def main():
    """Run all tests"""
    logger.info("🚀 Starting fix verification tests...")
    
    # Test button functionality
    await test_button_creation()
    
    # Test scheduler functionality
    test_scheduler()
    
    logger.info("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
