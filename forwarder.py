import asyncio
import logging
from typing import Dict, List, Optional, Any
from telethon import TelegramClient, events
from telethon.tl.types import Message
from config import Config
from database import Database
from plugins import PluginManager
import time

logger = logging.getLogger(__name__)

class MessageForwarder:
    def __init__(self):
        self.clients = {}  # Store multiple clients by account_id
        self.db = Database()
        self.plugin_manager = PluginManager()
        self.active_forwardings = {}
        self.is_running = False
    
    async def initialize_client(self, account_id: int, api_id: str, api_hash: str, session_string: str = None):
        """Initialize Telegram client for specific account"""
        if account_id not in self.clients:
            session_name = f'tgcf_session_{account_id}'
            client = TelegramClient(session_name, api_id, api_hash)
            
            if session_string:
                # Use existing session string
                await client.start(session_string=session_string)
            else:
                # Start with phone number authentication
                await client.start()
                # Save session string for future use
                session_string = client.session.save()
                self.db.update_account_session(account_id, session_string)
            
            self.clients[account_id] = client
            logger.info(f"Telegram client initialized for account {account_id}")
        
        return self.clients[account_id]
    
    async def start_forwarding(self, config_id: int, user_id: int):
        """Start forwarding for a specific configuration"""
        configs = self.db.get_user_configs(user_id)
        config = next((c for c in configs if c['id'] == config_id), None)
        
        if not config:
            logger.error(f"Configuration {config_id} not found for user {user_id}")
            return False
        
        account_id = config['account_id']
        account = self.db.get_account(account_id)
        
        if not account:
            logger.error(f"Account {account_id} not found")
            return False
        
        # Initialize client for this account
        client = await self.initialize_client(
            account_id, 
            account['api_id'], 
            account['api_hash'], 
            account['session_string']
        )
        
        source_chat_id = config['source_chat_id']
        destination_chat_id = config['destination_chat_id']
        config_data = config['config_data']
        
        # Store forwarding info
        self.active_forwardings[config_id] = {
            'user_id': user_id,
            'account_id': account_id,
            'source_chat_id': source_chat_id,
            'destination_chat_id': destination_chat_id,
            'config_data': config_data,
            'last_message_id': 0
        }
        
        # Set up event handler for this specific forwarding
        @client.on(events.NewMessage(chats=source_chat_id))
        async def handler(event):
            await self.handle_new_message(event, config_id)
        
        logger.info(f"Started forwarding for config {config_id}: {source_chat_id} -> {destination_chat_id} (Account: {account['account_name']})")
        return True
    
    async def stop_forwarding(self, config_id: int):
        """Stop forwarding for a specific configuration"""
        if config_id in self.active_forwardings:
            del self.active_forwardings[config_id]
            logger.info(f"Stopped forwarding for config {config_id}")
            return True
        return False
    
    async def handle_new_message(self, event, config_id: int):
        """Handle new message from source chat"""
        if config_id not in self.active_forwardings:
            return
        
        forwarding_info = self.active_forwardings[config_id]
        message = event.message
        
        try:
            # Process message through plugins
            processed_message = await self.plugin_manager.process_message(
                message, forwarding_info['config_data']
            )
            
            if processed_message is None:
                logger.info(f"Message filtered out for config {config_id}")
                return
            
            # Forward the message
            await self.forward_message(
                processed_message,
                forwarding_info['destination_chat_id'],
                config_id,
                forwarding_info['user_id'],
                forwarding_info['account_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling message for config {config_id}: {e}")
    
    async def forward_message(self, message: Message, destination_chat_id: str, 
                            config_id: int, user_id: int, account_id: int):
        """Forward a single message"""
        try:
            # Add delay between messages
            await asyncio.sleep(Config.DELAY_BETWEEN_MESSAGES)
            
            # Get the client for this account
            client = self.clients.get(account_id)
            if not client:
                logger.error(f"No client found for account {account_id}")
                return
            
            # Forward the message
            forwarded_message = await client.forward_messages(
                destination_chat_id,
                message,
                from_peer=message.peer_id
            )
            
            # Log the forwarded message
            self.db.log_message(
                user_id,
                account_id,
                message.id,
                forwarded_message.id if hasattr(forwarded_message, 'id') else message.id,
                str(message.peer_id),
                destination_chat_id
            )
            
            logger.info(f"Forwarded message {message.id} to {destination_chat_id} (Account: {account_id})")
            
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
    
    async def forward_past_messages(self, config_id: int, user_id: int, 
                                  limit: int = 100):
        """Forward past messages from source to destination"""
        configs = self.db.get_user_configs(user_id)
        config = next((c for c in configs if c['id'] == config_id), None)
        
        if not config:
            logger.error(f"Configuration {config_id} not found for user {user_id}")
            return False
        
        account_id = config['account_id']
        account = self.db.get_account(account_id)
        
        if not account:
            logger.error(f"Account {account_id} not found")
            return False
        
        # Initialize client for this account
        client = await self.initialize_client(
            account_id, 
            account['api_id'], 
            account['api_hash'], 
            account['session_string']
        )
        
        source_chat_id = config['source_chat_id']
        destination_chat_id = config['destination_chat_id']
        config_data = config['config_data']
        
        try:
            # Get past messages
            messages = []
            async for message in client.iter_messages(source_chat_id, limit=limit):
                messages.append(message)
            
            # Process and forward messages in reverse order (oldest first)
            for message in reversed(messages):
                # Process message through plugins
                processed_message = await self.plugin_manager.process_message(
                    message, config_data
                )
                
                if processed_message is None:
                    continue
                
                # Forward the message
                await self.forward_message(
                    processed_message,
                    destination_chat_id,
                    config_id,
                    user_id,
                    account_id
                )
                
                # Add delay between messages
                await asyncio.sleep(Config.DELAY_BETWEEN_MESSAGES)
            
            logger.info(f"Forwarded {len(messages)} past messages for config {config_id} (Account: {account['account_name']})")
            return True
            
        except Exception as e:
            logger.error(f"Error forwarding past messages: {e}")
            return False
    
    async def get_chat_info(self, chat_id: str, account_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a chat using specific account"""
        client = self.clients.get(account_id)
        if not client:
            logger.error(f"No client found for account {account_id}")
            return None
        
        try:
            entity = await client.get_entity(chat_id)
            return {
                'id': entity.id,
                'title': getattr(entity, 'title', None),
                'username': getattr(entity, 'username', None),
                'type': type(entity).__name__
            }
        except Exception as e:
            logger.error(f"Error getting chat info for {chat_id}: {e}")
            return None
    
    async def test_forwarding(self, source_chat_id: str, destination_chat_id: str, account_id: int) -> bool:
        """Test if forwarding is possible between two chats using specific account"""
        client = self.clients.get(account_id)
        if not client:
            logger.error(f"No client found for account {account_id}")
            return False
        
        try:
            # Check if we can access both chats
            source_entity = await client.get_entity(source_chat_id)
            dest_entity = await client.get_entity(destination_chat_id)
            
            # Check if we can send messages to destination
            await client.send_message(destination_chat_id, "Test message - TgCF Bot")
            
            logger.info(f"Test forwarding successful: {source_chat_id} -> {destination_chat_id} (Account: {account_id})")
            return True
            
        except Exception as e:
            logger.error(f"Test forwarding failed: {e}")
            return False
    
    async def get_active_forwardings(self) -> Dict[int, Dict[str, Any]]:
        """Get all active forwarding configurations"""
        return self.active_forwardings.copy()
    
    async def stop_all_forwardings(self):
        """Stop all active forwardings"""
        self.active_forwardings.clear()
        logger.info("Stopped all forwardings")
    
    async def close(self):
        """Close all Telegram clients"""
        for account_id, client in self.clients.items():
            await client.disconnect()
            logger.info(f"Telegram client disconnected for account {account_id}")
        self.clients.clear()
