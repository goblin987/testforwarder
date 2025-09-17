#!/usr/bin/env python3
"""
Check what campaigns exist in the database
"""

import logging
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_campaigns():
    """Check existing campaigns"""
    try:
        db = Database()
        
        # Get all campaigns
        campaigns = db.get_all_campaigns()
        print(f"📋 Found {len(campaigns)} campaigns:")
        
        for campaign in campaigns:
            print(f"  - ID: {campaign['id']}, Name: {campaign['campaign_name']}, Active: {campaign.get('is_active', False)}")
        
        # Get all accounts
        accounts = db.get_all_accounts()
        print(f"\n👤 Found {len(accounts)} accounts:")
        
        for account in accounts:
            print(f"  - ID: {account['id']}, Name: {account.get('account_name', 'Unknown')}, Has session: {bool(account.get('session_string'))}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_campaigns()
