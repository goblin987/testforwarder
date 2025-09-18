"""
Unified Telethon Client Manager
Handles both storage creation and message forwarding with proper session management
"""

import asyncio
import logging
import os
import time
from typing import Optional, Dict, Any, List
from telethon import TelegramClient
from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityItalic, MessageEntityMention
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

logger = logging.getLogger(__name__)

class TelethonManager:
    """Unified Telethon client manager for storage and forwarding operations"""
    
    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}
        self.session_dir = "sessions"
        os.makedirs(self.session_dir, exist_ok=True)
    
    async def get_client(self, account_data: Dict[str, Any]) -> Optional[TelegramClient]:
        """Get or create a Telethon client for the given account"""
        account_id = str(account_data['id'])
        
        if account_id in self.clients:
            return self.clients[account_id]
        
        try:
            # Check if we have a stored session string
            if account_data.get('session_string'):
                # Use StringSession for headless environments
                from telethon.sessions import StringSession
                client = TelegramClient(
                    StringSession(account_data['session_string']),
                    account_data['api_id'],
                    account_data['api_hash']
                )
            elif account_data.get('session_data'):
                # Use existing session file
                import base64
                session_name = f"unified_{account_id}"
                session_path = os.path.join(self.session_dir, f"{session_name}.session")
                
                # Write session data to file
                session_data = base64.b64decode(account_data['session_data'])
                with open(session_path, 'wb') as f:
                    f.write(session_data)
                
                client = TelegramClient(
                    session_path.replace('.session', ''),
                    account_data['api_id'],
                    account_data['api_hash']
                )
            else:
                # This won't work in headless environment!
                logger.error(f"❌ No session data available for account {account_id} - cannot authenticate in headless environment")
                return None
            
            # Connect without prompting for input
            await client.connect()
            
            # Check if already authorized
            if not await client.is_user_authorized():
                logger.error(f"❌ Account {account_id} is not authorized - cannot authenticate in headless environment")
                await client.disconnect()
                return None
            
            # Store client for reuse
            self.clients[account_id] = client
            logger.info(f"✅ Created unified Telethon client for account {account_data['account_name']}")
            
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to create Telethon client for account {account_id}: {e}")
            return None
    
    async def create_storage_message(self, account_data: Dict[str, Any], storage_channel_id: int, 
                                   media_data: Dict[str, Any], bot_instance=None) -> Optional[Dict[str, Any]]:
        """Create a storage message using Telethon with proper custom emoji handling"""
        try:
            client = await self.get_client(account_data)
            if not client:
                return None
            
            # Convert Bot API entities to Telethon entities
            telethon_entities = self._convert_entities_to_telethon(media_data.get('caption_entities', []))
            
            # For now, let's use a simpler approach - forward the original message
            # This preserves all entities and custom emojis perfectly
            if media_data.get('original_message_id') and media_data.get('original_chat_id'):
                # Forward the original message to storage channel
                original_chat = await client.get_entity(media_data['original_chat_id'])
                sent_message = await client.forward_messages(
                    entity=storage_channel_id,
                    messages=media_data['original_message_id'],
                    from_peer=original_chat
                )
                
                if sent_message:
                    message = sent_message[0] if isinstance(sent_message, list) else sent_message
                    logger.info(f"✅ Forwarded original message to storage: ID {message.id}")
                    
                    return {
                        'storage_message_id': message.id,
                        'storage_chat_id': storage_channel_id,
                        'client': client
                    }
            
            # Fallback: Create new message (this won't preserve custom emojis perfectly)
            logger.warning("⚠️ Using fallback message creation - custom emojis may not be preserved")
            
            # Send text message with entities
            sent_message = await client.send_message(
                entity=storage_channel_id,
                message=media_data.get('caption', ''),
                formatting_entities=telethon_entities,
                parse_mode=None
            )
            
            logger.info(f"✅ Created storage message with Telethon: ID {sent_message.id}")
            
            return {
                'storage_message_id': sent_message.id,
                'storage_chat_id': storage_channel_id,
                'client': client
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create storage message with Telethon: {e}")
            return None
    
    async def forward_storage_message(self, client: TelegramClient, target_chat_id: int, 
                                    storage_message_id: int, storage_channel_id: int) -> bool:
        """Forward a storage message to target chat using the same client"""
        try:
            # Get storage channel entity
            storage_channel = await client.get_entity(storage_channel_id)
            
            # Forward the message
            forwarded_messages = await client.forward_messages(
                entity=target_chat_id,
                messages=storage_message_id,
                from_peer=storage_channel
            )
            
            if forwarded_messages:
                logger.info(f"✅ Forwarded storage message {storage_message_id} to {target_chat_id}")
                return True
            else:
                logger.warning(f"❌ No messages forwarded from storage")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to forward storage message: {e}")
            return False
    
    def _convert_entities_to_telethon(self, bot_entities: List[Dict[str, Any]]) -> List:
        """Convert Bot API entities to Telethon entities"""
        telethon_entities = []
        
        for entity_data in bot_entities:
            try:
                entity_type = entity_data['type']
                if hasattr(entity_type, 'value'):
                    entity_type = entity_type.value
                elif hasattr(entity_type, 'name'):
                    entity_type = entity_type.name.lower()
                
                if entity_type == 'custom_emoji':
                    entity = MessageEntityCustomEmoji(
                        offset=entity_data['offset'],
                        length=entity_data['length'],
                        document_id=int(entity_data['custom_emoji_id'])
                    )
                elif entity_type == 'bold':
                    entity = MessageEntityBold(
                        offset=entity_data['offset'],
                        length=entity_data['length']
                    )
                elif entity_type == 'italic':
                    entity = MessageEntityItalic(
                        offset=entity_data['offset'],
                        length=entity_data['length']
                    )
                elif entity_type == 'mention':
                    entity = MessageEntityMention(
                        offset=entity_data['offset'],
                        length=entity_data['length']
                    )
                else:
                    continue
                
                telethon_entities.append(entity)
                
            except Exception as e:
                logger.warning(f"Failed to convert entity: {e}")
                continue
        
        return telethon_entities
    
    async def _get_media_file(self, media_data: Dict[str, Any]) -> Optional[str]:
        """Download media file for Telethon upload"""
        try:
            # For now, we'll use the Bot API to download the file
            # In a full implementation, we'd need to pass the bot instance
            # This is a simplified version that returns the file_id for now
            return media_data.get('file_id')
        except Exception as e:
            logger.error(f"Failed to get media file: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup all clients"""
        for client in self.clients.values():
            try:
                await client.disconnect()
            except:
                pass
        self.clients.clear()

# Global instance
telethon_manager = TelethonManager()
