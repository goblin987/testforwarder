#!/usr/bin/env python3
"""
Test script to manually trigger campaign execution
"""

import asyncio
import logging
from bump_service import BumpService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_campaign():
    """Test campaign execution manually"""
    try:
        # Initialize bump service
        bump_service = BumpService()
        
        # Get campaign 123 (from the logs)
        campaign = bump_service.get_campaign(123)
        if not campaign:
            print("❌ Campaign 123 not found!")
            return
        
        print(f"📋 Campaign found: {campaign['campaign_name']}")
        print(f"📅 Schedule: {campaign['schedule_type']} at {campaign['schedule_time']}")
        print(f"🔄 Active: {campaign.get('is_active', False)}")
        
        # Check account
        account = bump_service.db.get_account(campaign['account_id'])
        if not account:
            print("❌ Account not found!")
            return
        
        print(f"👤 Account: {account.get('account_name', 'Unknown')}")
        print(f"🔑 Has session: {bool(account.get('session_string'))}")
        
        # Execute campaign manually
        print("🚀 Executing campaign manually...")
        await bump_service._async_send_ad(123)
        print("✅ Campaign execution completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_campaign())
