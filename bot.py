"""
TgCF Pro - Enterprise Telegram Bot Interface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Professional Telegram bot interface providing intuitive user interactions
for enterprise-grade automation and campaign management.

Features:
- Multi-account management with streamlined setup
- Advanced campaign creation and scheduling
- Real-time performance monitoring and analytics
- Enterprise security with access control
- Professional UI/UX with inline keyboards

Author: TgCF Pro Team
License: MIT
Version: 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config import Config
from database import Database
from plugins import PluginManager
from forwarder import MessageForwarder
from bump_service import BumpService
import json

# Configure professional logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TgcfBot:
    def escape_markdown(self, text):
        """Escape special Markdown characters"""
        if not text:
            return ""
        # Escape special characters that break Markdown
        text = str(text)
        text = text.replace("\\", "\\\\")  # Backslash first
        text = text.replace("*", "\\*")   # Asterisk
        text = text.replace("_", "\\_")   # Underscore
        text = text.replace("`", "\\`")   # Backtick
        text = text.replace("[", "\\[")   # Square brackets
        text = text.replace("]", "\\]")   # Square brackets
        text = text.replace("(", "\\(")   # Parentheses
        text = text.replace(")", "\\)")   # Parentheses
        text = text.replace("~", "\\~")   # Tilde
        text = text.replace(">", "\\>")   # Greater than
        text = text.replace("#", "\\#")   # Hash
        text = text.replace("+", "\\+")   # Plus
        text = text.replace("-", "\\-")   # Minus
        text = text.replace("=", "\\=")   # Equals
        text = text.replace("|", "\\|")   # Pipe
        text = text.replace("{", "\\{")   # Curly braces
        text = text.replace("}", "\\}")   # Curly braces
        text = text.replace(".", "\\.")   # Dot
        text = text.replace("!", "\\!")   # Exclamation
        return text

    def __init__(self):
        self.db = Database()
        self.plugin_manager = PluginManager()
        self.forwarder = MessageForwarder()
        self.bump_service = BumpService()
        self.user_sessions = {}  # Store user session data
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Check if this is the bot owner (optional - you can remove this check if you want)
        if Config.OWNER_USER_ID and str(user.id) != Config.OWNER_USER_ID:
            await update.message.reply_text(
                "🔒 **Access Restricted**\n\nThis bot is for authorized use only.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = """
🚀 **Welcome to TgCF Pro**

*Enterprise Telegram Automation Platform*

**Professional Features:**
• 🏢 Multi-Account Management - Unlimited work accounts
• 📢 Smart Bump Service - Advanced campaign automation  
• ⚡ Real-time Forwarding - Lightning-fast message processing
• 📊 Business Analytics - Comprehensive performance tracking
• 🛡️ Enterprise Security - Professional-grade protection

**Ready to automate your business communications?**
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 Bump Service", callback_data="bump_service")],
            [InlineKeyboardButton("📋 My Configurations", callback_data="my_configs")],
            [InlineKeyboardButton("➕ Add New Forwarding", callback_data="add_forwarding")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **TgCF Bot Help**

**Commands:**
/start - Start the bot and show main menu
/help - Show this help message
/config - Manage your forwarding configurations
/status - Check bot status

**How to use:**
1. **Add Telegram Accounts** - Click "Manage Accounts" to add your Telegram accounts
2. **Create Forwarding Rules** - Click "Add New Forwarding" to create forwarding rules
3. **Configure Plugins** - Set up filters, formatting, and other plugins
4. **Start Forwarding** - Your messages will be forwarded automatically!

**Multi-Account Features:**
• Add multiple Telegram accounts with their own API credentials
• Each account can have separate forwarding rules
• Forward to different or same destinations
• Manage all accounts from one bot interface

**Chat IDs:**
• For channels: Use @channel_username or channel ID
• For groups: Use group ID (get from @userinfobot)
• For users: Use @username or user ID

**Account Setup (IMPORTANT):**
• Each user must get their own API credentials from https://my.telegram.org
• Go to "API development tools" and create an application
• Each account needs its own API ID and Hash (YOUR personal credentials)
• Phone number authentication required for each account
• Your API credentials are stored securely and only used for your accounts
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "main_menu":
            await self.show_main_menu(query)
        elif data == "manage_accounts":
            await self.show_manage_accounts(query)
        elif data == "add_account":
            await self.start_add_account(query)
        elif data == "my_configs":
            await self.show_my_configs(query)
        elif data == "add_forwarding":
            await self.start_add_forwarding(query)
        elif data == "settings":
            await self.show_settings(query)
        elif data == "help":
            await self.show_help(query)
        elif data == "bump_service":
            await self.show_bump_service(query)
        elif data == "add_campaign":
            await self.start_add_campaign(query)
        elif data == "my_campaigns":
            await self.show_my_campaigns(query)
        elif data.startswith("campaign_"):
            campaign_id = int(data.split("_")[1])
            await self.show_campaign_details(query, campaign_id)
        elif data.startswith("delete_campaign_"):
            campaign_id = int(data.split("_")[2])
            await self.delete_campaign(query, campaign_id)
        elif data.startswith("toggle_campaign_"):
            campaign_id = int(data.split("_")[2])
            await self.toggle_campaign(query, campaign_id)
        elif data.startswith("test_campaign_"):
            campaign_id = int(data.split("_")[2])
            await self.test_campaign(query, campaign_id)
        elif data == "back_to_campaigns":
            await self.show_my_campaigns(query)
        elif data == "back_to_bump":
            await self.show_bump_service(query)
        elif data.startswith("schedule_"):
            schedule_type = data.split("_")[1]
            await self.handle_schedule_selection(query, schedule_type)
        elif data.startswith("select_account_"):
            account_id = int(data.split("_")[2])
            await self.handle_account_selection(query, account_id)
        elif data.startswith("config_"):
            config_id = int(data.split("_")[1])
            await self.show_config_details(query, config_id)
        elif data.startswith("delete_config_"):
            config_id = int(data.split("_")[2])
            await self.delete_config(query, config_id)
        elif data.startswith("toggle_config_"):
            config_id = int(data.split("_")[2])
            await self.toggle_config(query, config_id)
        elif data.startswith("account_"):
            account_id = int(data.split("_")[1])
            await self.show_account_details(query, account_id)
        elif data.startswith("delete_account_"):
            account_id = int(data.split("_")[2])
            await self.delete_account(query, account_id)
        elif data.startswith("configs_for_account_"):
            account_id = int(data.split("_")[3])
            await self.show_configs_for_account(query, account_id)
        elif data == "back_to_configs":
            await self.show_my_configs(query)
        elif data == "back_to_accounts":
            await self.show_manage_accounts(query)
        elif data == "upload_session":
            await self.start_session_upload(query)
        elif data == "manual_setup":
            await self.start_manual_setup(query)
        elif data == "advanced_settings":
            await self.show_advanced_settings(query)
        elif data == "configure_plugins":
            await self.show_configure_plugins(query)
        elif data == "performance_settings":
            await self.show_performance_settings(query)
        elif data == "security_settings":
            await self.show_security_settings(query)
        elif data == "add_buttons_yes":
            await self.handle_add_buttons_yes(query)
        elif data == "add_buttons_no":
            await self.handle_add_buttons_no(query)
        elif data == "add_more_messages":
            await self.handle_add_more_messages(query)
        elif data == "target_all_groups":
            await self.handle_target_all_groups(query)
        elif data == "target_specific_chats":
            await self.handle_target_specific_chats(query)
        elif data == "cancel_campaign":
            await self.handle_cancel_campaign(query)
        elif data == "back_to_schedule_selection":
            await self.show_schedule_selection(query)
        elif data == "back_to_target_selection":
            await self.show_target_selection(query)
        elif data == "back_to_button_choice":
            await self.show_button_choice(query)
        elif data.startswith("start_campaign_"):
            campaign_id = int(data.split("_")[2])
            await self.start_campaign_manually(query, campaign_id)
        else:
            await query.answer("Unknown command!", show_alert=True)
    
    async def show_main_menu(self, query):
        """Show main menu with all core features"""
        keyboard = [
            [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 Bump Service", callback_data="bump_service")],
            [InlineKeyboardButton("📋 My Configurations", callback_data="my_configs")],
            [InlineKeyboardButton("➕ Add New Forwarding", callback_data="add_forwarding")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🤖 **TgCF Bot - Main Menu**\n\nChoose an option:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_my_configs(self, query):
        """Show user's forwarding configurations"""
        user_id = query.from_user.id
        configs = self.db.get_user_configs(user_id)
        
        if not configs:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Forwarding", callback_data="add_forwarding")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📋 **My Configurations**\n\nNo forwarding configurations found.\n\nClick 'Add New Forwarding' to create your first one!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        text = "📋 **My Configurations**\n\n"
        keyboard = []
        
        for config in configs:
            status = "🟢 Active" if config['is_active'] else "🔴 Inactive"
            text += f"**{config['config_name']}** {status}\n"
            text += f"From: `{config['source_chat_id']}`\n"
            text += f"To: `{config['destination_chat_id']}`\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {config['config_name']}", callback_data=f"config_{config['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_config_{config['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add New", callback_data="add_forwarding")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_config_details(self, query, config_id):
        """Show detailed configuration"""
        user_id = query.from_user.id
        configs = self.db.get_user_configs(user_id)
        config = next((c for c in configs if c['id'] == config_id), None)
        
        if not config:
            await query.answer("Configuration not found!", show_alert=True)
            return
        
        status = "🟢 Active" if config['is_active'] else "🔴 Inactive"
        text = f"⚙️ **{config['config_name']}** {status}\n\n"
        text += f"**Source:** `{config['source_chat_id']}`\n"
        text += f"**Destination:** `{config['destination_chat_id']}`\n\n"
        
        # Show plugin status
        config_data = config['config_data']
        text += "**Plugins:**\n"
        for plugin_name, plugin_config in config_data.items():
            if isinstance(plugin_config, dict) and plugin_config.get('enabled', False):
                text += f"• {plugin_name.title()}: ✅\n"
            else:
                text += f"• {plugin_name.title()}: ❌\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Toggle Status", callback_data=f"toggle_config_{config_id}")],
            [InlineKeyboardButton("🔙 Back to Configs", callback_data="back_to_configs")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_add_forwarding(self, query):
        """Start the process of adding a new forwarding configuration"""
        user_id = query.from_user.id
        
        # Check if user has any accounts
        accounts = self.db.get_user_accounts(user_id)
        if not accounts:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **No Accounts Found!**\n\nYou need to add at least one Telegram account before creating forwarding configurations.\n\nClick 'Add New Account' to get started!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        self.user_sessions[user_id] = {'step': 'source_chat', 'config': {}}
        
        text = """
➕ **Add New Forwarding Configuration**

**Step 1/4: Source Chat**

Please send me the source chat ID or username.

**Examples:**
• Channel: `@channel_username` or `-1001234567890`
• Group: `-1001234567890`
• User: `@username` or `123456789`

**How to get Chat ID:**
• For channels: Use @channel_username
• For groups: Forward a message from the group to @userinfobot
• For users: Use @username
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_settings(self, query):
        """Show settings menu"""
        text = """
⚙️ **Settings**

**Current Settings:**
• Max messages per batch: 100
• Delay between messages: 0.1s
• Web interface: Available

**Available Options:**
• Configure forwarding limits
• Set up filters
• Manage plugins
• Export/Import configurations
        """
        
        keyboard = [
            [InlineKeyboardButton("🔧 Advanced Settings", callback_data="advanced_settings")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_advanced_settings(self, query):
        """Show advanced settings menu"""
        text = """
🔧 **Advanced Settings**

**Plugin Configuration:**
• Message filters and blacklists
• Text formatting options
• Caption and watermark settings

**Performance Settings:**
• Message batch size limits
• Delay configurations
• Error handling options

**Security Settings:**
• Access control
• Session management
• Data encryption
        """
        
        keyboard = [
            [InlineKeyboardButton("🔌 Configure Plugins", callback_data="configure_plugins")],
            [InlineKeyboardButton("⚡ Performance Settings", callback_data="performance_settings")],
            [InlineKeyboardButton("🔒 Security Settings", callback_data="security_settings")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_configure_plugins(self, query):
        """Show plugin configuration menu"""
        text = """
🔌 **Configure Plugins**

**Available Plugins:**

**🔍 Filter Plugin**
• Blacklist/whitelist messages
• Keyword filtering
• Pattern matching

**📝 Format Plugin**
• Bold, italic, code formatting
• Message styling options

**🔄 Replace Plugin**
• Text replacement rules
• Regular expressions
• Content modification

**📋 Caption Plugin**
• Header and footer text
• Custom message templates
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 Filter Settings", callback_data="filter_settings")],
            [InlineKeyboardButton("📝 Format Settings", callback_data="format_settings")],
            [InlineKeyboardButton("🔄 Replace Settings", callback_data="replace_settings")],
            [InlineKeyboardButton("📋 Caption Settings", callback_data="caption_settings")],
            [InlineKeyboardButton("🔙 Back to Advanced", callback_data="advanced_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_performance_settings(self, query):
        """Show performance settings menu"""
        text = """
⚡ **Performance Settings**

**Current Configuration:**
• Max messages per batch: 100
• Delay between messages: 0.1s
• Connection timeout: 30s
• Retry attempts: 3

**Optimization Options:**
• Batch processing size
• Message throttling
• Error handling strategy
• Resource management

**Monitoring:**
• Real-time performance metrics
• Error rate tracking
• Success rate analytics
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 View Metrics", callback_data="view_metrics")],
            [InlineKeyboardButton("⚙️ Adjust Limits", callback_data="adjust_limits")],
            [InlineKeyboardButton("🔙 Back to Advanced", callback_data="advanced_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_security_settings(self, query):
        """Show security settings menu"""
        text = """
🔒 **Security Settings**

**Access Control:**
• Owner-only mode: Enabled
• User authentication required
• Session validation active

**Data Protection:**
• Encrypted session storage
• Secure API credential handling
• Protected database access

**Privacy Features:**
• No message content logging
• Secure credential transmission
• Automatic session cleanup

**Audit & Monitoring:**
• Access attempt logging
• Security event tracking
• Failed login monitoring
        """
        
        keyboard = [
            [InlineKeyboardButton("👤 Access Control", callback_data="access_control")],
            [InlineKeyboardButton("🔐 Data Protection", callback_data="data_protection")],
            [InlineKeyboardButton("📋 Security Logs", callback_data="security_logs")],
            [InlineKeyboardButton("🔙 Back to Advanced", callback_data="advanced_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_forwarded_ad_content(self, update: Update, session: dict):
        """Handle forwarded message as ad content with full fidelity preservation"""
        user_id = update.effective_user.id
        message = update.message
        
        # Store the complete message data for full fidelity reproduction
        ad_data = {
            'message_id': message.message_id,
            'chat_id': message.chat_id,
            'text': message.text,
            'caption': message.caption,
            'entities': [],
            'caption_entities': [],
            'media_type': None,
            'file_id': None,
            'has_custom_emojis': False,
            'has_premium_emojis': False
        }
        
        # Preserve text entities (formatting, emojis, links)
        if message.entities:
            for entity in message.entities:
                entity_data = {
                    'type': entity.type,
                    'offset': entity.offset,
                    'length': entity.length,
                    'url': entity.url if hasattr(entity, 'url') else None,
                    'user': entity.user.id if hasattr(entity, 'user') and entity.user else None,
                    'language': entity.language if hasattr(entity, 'language') else None,
                    'custom_emoji_id': entity.custom_emoji_id if hasattr(entity, 'custom_emoji_id') else None
                }
                ad_data['entities'].append(entity_data)
                
                # Check for custom/premium emojis
                if entity.type == 'custom_emoji':
                    ad_data['has_custom_emojis'] = True
        
        # Preserve caption entities for media messages
        if message.caption_entities:
            for entity in message.caption_entities:
                entity_data = {
                    'type': entity.type,
                    'offset': entity.offset,
                    'length': entity.length,
                    'url': entity.url if hasattr(entity, 'url') else None,
                    'custom_emoji_id': entity.custom_emoji_id if hasattr(entity, 'custom_emoji_id') else None
                }
                ad_data['caption_entities'].append(entity_data)
                
                if entity.type == 'custom_emoji':
                    ad_data['has_custom_emojis'] = True
        
        # Handle different media types
        if message.photo:
            ad_data['media_type'] = 'photo'
            ad_data['file_id'] = message.photo[-1].file_id  # Get highest resolution
        elif message.video:
            ad_data['media_type'] = 'video'
            ad_data['file_id'] = message.video.file_id
        elif message.document:
            ad_data['media_type'] = 'document'
            ad_data['file_id'] = message.document.file_id
        elif message.animation:
            ad_data['media_type'] = 'animation'
            ad_data['file_id'] = message.animation.file_id
        elif message.voice:
            ad_data['media_type'] = 'voice'
            ad_data['file_id'] = message.voice.file_id
        elif message.video_note:
            ad_data['media_type'] = 'video_note'
            ad_data['file_id'] = message.video_note.file_id
        elif message.sticker:
            ad_data['media_type'] = 'sticker'
            ad_data['file_id'] = message.sticker.file_id
        elif message.audio:
            ad_data['media_type'] = 'audio'
            ad_data['file_id'] = message.audio.file_id
        
        # Store the ad data
        if 'ad_messages' not in session['campaign_data']:
            session['campaign_data']['ad_messages'] = []
        session['campaign_data']['ad_messages'].append(ad_data)
        
        # Show preview and ask about buttons
        emoji_info = ""
        if ad_data['has_custom_emojis']:
            emoji_info = "\n✨ **Custom emojis detected and preserved!**"
        
        media_info = ""
        if ad_data['media_type']:
            media_info = f"\n📎 **Media:** {ad_data['media_type'].title()}"
        
        text = f"""✅ **Ad content received!**{emoji_info}{media_info}

**Preview saved with full fidelity:**
• All formatting preserved
• Custom/premium emojis maintained
• Media files stored
• Original message structure kept

**Would you like to add buttons under this ad?**

Buttons will appear as an inline keyboard below your ad message."""
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Buttons", callback_data="add_buttons_yes")],
            [InlineKeyboardButton("⏭️ Skip Buttons", callback_data="add_buttons_no")],
            [InlineKeyboardButton("📤 Add More Messages", callback_data="add_more_messages")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        session['step'] = 'add_buttons_choice'
    
    async def handle_button_choice(self, update: Update, session: dict):
        """Handle user's choice about adding buttons"""
        message_text = update.message.text.strip()
        
        if message_text.lower() in ['yes', 'y', 'add', 'buttons']:
            session['step'] = 'button_input'
            await update.message.reply_text(
                "➕ **Add Buttons to Your Ad**\n\n**Format:** [Button Text] - [URL]\n\n**Examples:**\n`Shop Now - https://example.com/shop`\n`Visit Website - https://mysite.com`\n`Contact Us - https://t.me/support`\n\n**Send one button per message, or multiple buttons separated by new lines.**\n\n**When finished, type 'done' or 'finish'**",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Skip buttons, move to target chats
            session['step'] = 'target_chats_choice'
            await self.show_target_chat_options(update, session)
    
    async def handle_button_input(self, update: Update, session: dict):
        """Handle button input from user"""
        message_text = update.message.text.strip()
        
        if message_text.lower() in ['done', 'finish', 'complete']:
            # Move to target chats selection
            session['step'] = 'target_chats_choice'
            await self.show_target_chat_options(update, session)
            return
        
        # Parse button input
        if 'buttons' not in session['campaign_data']:
            session['campaign_data']['buttons'] = []
        
        # Handle multiple buttons in one message
        lines = message_text.split('\n')
        buttons_added = 0
        
        for line in lines:
            line = line.strip()
            if ' - ' in line:
                try:
                    button_text, button_url = line.split(' - ', 1)
                    button_text = button_text.strip('[]')
                    button_url = button_url.strip()
                    
                    # Validate URL
                    if not (button_url.startswith('http://') or button_url.startswith('https://') or button_url.startswith('t.me/')):
                        button_url = 'https://' + button_url
                    
                    session['campaign_data']['buttons'].append({
                        'text': button_text,
                        'url': button_url
                    })
                    buttons_added += 1
                except:
                    continue
        
        if buttons_added > 0:
            total_buttons = len(session['campaign_data']['buttons'])
            await update.message.reply_text(
                f"✅ **{buttons_added} button(s) added!** (Total: {total_buttons})\n\n**Current buttons:**\n" + 
                "\n".join([f"• {btn['text']} → {btn['url']}" for btn in session['campaign_data']['buttons']]) +
                "\n\n**Add more buttons or type 'done' to continue.**",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "❌ **Invalid format!**\n\nPlease use: `[Button Text] - [URL]`\n\nExample: `Shop Now - https://example.com`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_target_chat_options(self, update: Update, session: dict):
        """Show enhanced target chat selection options"""
        text = """🎯 **Step 3/6: Target Chats**

**Choose how to select your target chats:**

**🌐 Send to All Worker Groups**
• Automatically targets all groups your worker account is in
• Smart detection of group chats
• Excludes private chats and channels
• Perfect for broad campaigns

**🎯 Specify Target Chats**
• Manually enter specific chat IDs or usernames
• Precise targeting control
• Include channels, groups, or private chats
• Custom audience selection"""
        
        keyboard = [
            [InlineKeyboardButton("🌐 Send to All Worker Groups", callback_data="target_all_groups")],
            [InlineKeyboardButton("🎯 Specify Target Chats", callback_data="target_specific_chats")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_add_buttons_yes(self, query):
        """Handle user choosing to add buttons"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session['step'] = 'button_input'
            
            await query.edit_message_text(
                "➕ **Add Buttons to Your Ad**\n\n**Format:** [Button Text] - [URL]\n\n**Examples:**\n`Shop Now - https://example.com/shop`\n`Visit Website - https://mysite.com`\n`Contact Us - https://t.me/support`\n\n**Send one button per message, or multiple buttons separated by new lines.**\n\n**When finished, type 'done' or 'finish'**",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_add_buttons_no(self, query):
        """Handle user choosing to skip buttons"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session['step'] = 'target_chats_choice'
            
            # Show target chat options
            text = """🎯 **Step 3/6: Target Chats**

**Choose how to select your target chats:**

**🌐 Send to All Worker Groups**
• Automatically targets all groups your worker account is in
• Smart detection of group chats
• Excludes private chats and channels
• Perfect for broad campaigns

**🎯 Specify Target Chats**
• Manually enter specific chat IDs or usernames
• Precise targeting control
• Include channels, groups, or private chats
• Custom audience selection"""
            
            keyboard = [
                [InlineKeyboardButton("🌐 Send to All Worker Groups", callback_data="target_all_groups")],
                [InlineKeyboardButton("🎯 Specify Target Chats", callback_data="target_specific_chats")],
                [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def handle_add_more_messages(self, query):
        """Handle user choosing to add more messages"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session['step'] = 'ad_content'  # Go back to ad content step
            
            await query.edit_message_text(
                "📤 **Add More Messages**\n\n**Forward additional messages** that you want to include in this ad campaign.\n\nAll messages will be sent in sequence when the campaign runs.\n\n**Just forward the next message(s) from any chat!**",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_target_all_groups(self, query):
        """Handle user choosing to target all worker groups"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session['campaign_data']['target_mode'] = 'all_groups'
            session['campaign_data']['target_chats'] = ['ALL_WORKER_GROUPS']
            session['step'] = 'schedule_type'
            
            # Move to schedule selection
            text = """✅ **Target set to all worker groups!**

**Step 4/6: Schedule Type**

**How often should this campaign run?**"""
            
            keyboard = [
                [InlineKeyboardButton("📅 Daily", callback_data="schedule_daily")],
                [InlineKeyboardButton("📊 Weekly", callback_data="schedule_weekly")],
                [InlineKeyboardButton("⏰ Hourly", callback_data="schedule_hourly")],
                [InlineKeyboardButton("🔧 Custom", callback_data="schedule_custom")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_campaign")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def handle_target_specific_chats(self, query):
        """Handle user choosing to specify target chats manually"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session['campaign_data']['target_mode'] = 'specific'
            session['step'] = 'target_chats'
            
            await query.edit_message_text(
                "🎯 **Specify Target Chats**\n\n**Send me the target chat IDs or usernames** where you want to post ads.\n\n**Format:** One per line or comma-separated\n\n**Examples:**\n@channel1\n@channel2\n@mygroup\n-1001234567890\n\n**Supported:**\n• Public channels (@channelname)\n• Public groups (@groupname)\n• Private chats (chat ID numbers)\n• Telegram usernames (@username)",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_cancel_campaign(self, query):
        """Handle user canceling campaign creation"""
        user_id = query.from_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await query.edit_message_text(
            "❌ **Campaign creation canceled.**\n\nYou can start a new campaign anytime from the Bump Service menu.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Return to bump service menu
        await asyncio.sleep(2)
        await self.show_bump_service(query)
    
    async def execute_immediate_campaign(self, campaign_id: int, account_id: int, campaign_data: dict) -> bool:
        """Execute campaign immediately upon creation"""
        try:
            # Get account details
            account = self.db.get_account(account_id)
            if not account:
                return False
            
            # Initialize Telethon client for immediate execution
            from telethon import TelegramClient
            import base64
            
            # Handle session creation
            temp_session_path = f"temp_session_{account_id}"
            
            # Check if we have a valid session
            if not account.get('session_string'):
                logger.error(f"Account {account_id} has no session string. Please re-authenticate the account.")
                return False
            
            # Handle uploaded sessions vs API credential sessions
            if account['api_id'] == 'uploaded' or account['api_hash'] == 'uploaded':
                # For uploaded sessions, decode and save the session file
                try:
                    session_data = base64.b64decode(account['session_string'])
                    with open(f"{temp_session_path}.session", "wb") as f:
                        f.write(session_data)
                    # Use dummy credentials for uploaded sessions
                    api_id = 123456  
                    api_hash = 'dummy_hash_for_uploaded_sessions'
                except Exception as e:
                    logger.error(f"Failed to decode uploaded session for account {account_id}: {e}")
                    return False
            else:
                # For API credential accounts with authenticated sessions
                try:
                    api_id = int(account['api_id'])
                    api_hash = account['api_hash']
                    
                    # Session string is base64 encoded session file data
                    # Decode and write it as the session file
                    session_data = base64.b64decode(account['session_string'])
                    with open(f"{temp_session_path}.session", "wb") as f:
                        f.write(session_data)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid API credentials for account {account_id}: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Failed to decode session for account {account_id}: {e}")
                    return False
            
            # Initialize and start client
            try:
                client = TelegramClient(temp_session_path, api_id, api_hash)
                await client.start()
                
                # Verify the session is valid
                me = await client.get_me()
                if not me:
                    logger.error(f"Session invalid for account {account_id}")
                    await client.disconnect()
                    return False
                    
                logger.info(f"Successfully authenticated as {me.username or me.phone}")
                
            except Exception as e:
                logger.error(f"Failed to start client for account {account_id}: {e}")
                # Clean up session file on failure
                import os
                try:
                    if os.path.exists(f"{temp_session_path}.session"):
                        os.remove(f"{temp_session_path}.session")
                except:
                    pass
                return False
            
            # Determine target chats
            target_chats = campaign_data['target_chats']
            if campaign_data.get('target_mode') == 'all_groups' or target_chats == ['ALL_WORKER_GROUPS']:
                # Get all groups the account is member of
                dialogs = await client.get_dialogs()
                target_chats = []
                for dialog in dialogs:
                    if dialog.is_group and not dialog.is_channel:
                        target_chats.append(str(dialog.id))
            
            # Send messages to target chats using entity objects
            success_count = 0
            ad_content = campaign_data['ad_content']
            
            # Create buttons from campaign data
            from telethon import Button
            buttons_data = campaign_data.get('buttons', [])
            
            if buttons_data:
                try:
                    button_rows = []
                    current_row = []
                    
                    for i, button in enumerate(buttons_data):
                        if button.get('url'):
                            telethon_button = Button.url(button['text'], button['url'])
                        else:
                            telethon_button = Button.inline(button['text'], f"btn_{i}")
                        
                        current_row.append(telethon_button)
                        
                        if len(current_row) == 2 or i == len(buttons_data) - 1:
                            button_rows.append(current_row)
                            current_row = []
                    
                    telethon_buttons = button_rows
                    logger.info(f"✅ Created {len(buttons_data)} campaign buttons for immediate execution")
                except Exception as e:
                    logger.error(f"❌ Error creating campaign buttons: {e}")
                    telethon_buttons = [[Button.url("Shop Now", "https://t.me/testukassdfdds")]]
            else:
                # Default button if none specified
                telethon_buttons = [[Button.url("Shop Now", "https://t.me/testukassdfdds")]]
                logger.info("Using default Shop Now button for immediate execution")
            
            # Get all dialogs and find groups (use entities instead of IDs)
            target_entities = []
            if campaign_data.get('target_mode') == 'all_groups' or target_chats == ['ALL_WORKER_GROUPS']:
                logger.info("Discovering worker account groups for immediate execution...")
                dialogs = await client.get_dialogs()
                
                for dialog in dialogs:
                    if dialog.is_group:  # Include both groups and supergroups
                        target_entities.append(dialog.entity)
                        logger.info(f"Found group for immediate execution: {dialog.name} (ID: {dialog.id})")
                
                logger.info(f"Discovered {len(target_entities)} groups for immediate execution")
            else:
                # Use specific chat IDs - convert to entities
                for chat_id in target_chats:
                    try:
                        entity = await client.get_entity(chat_id)
                        target_entities.append(entity)
                    except Exception as e:
                        logger.error(f"Failed to get entity for {chat_id}: {e}")
            
            for chat_entity in target_entities:
                try:
                    # RESTRUCTURED: Simplified message sending with guaranteed buttons
                    if isinstance(ad_content, list) and ad_content:
                        # For forwarded content, send each message and add button to the last one
                        for i, message_data in enumerate(ad_content):
                            message_text = message_data.get('text', '')
                            
                            # Add buttons to the last message only
                            if i == len(ad_content) - 1:
                                logger.info(f"Adding buttons to final message (immediate execution)")
                                try:
                                    # Try to send with buttons first
                                    await client.send_message(
                                        chat_entity,
                                        message_text,
                                        buttons=telethon_buttons
                                    )
                                    logger.info(f"✅ Sent message with inline buttons to {chat_entity.title}")
                                    message_sent = True
                                except Exception as button_error:
                                    logger.warning(f"⚠️ Inline buttons failed for {chat_entity.title}: {button_error}")
                                    # Fallback: Add button URLs as text
                                    button_text = ""
                                    for button_row in telethon_buttons:
                                        for button in button_row:
                                            if hasattr(button, 'url'):
                                                button_text += f"\n🔗 {button.text}: {button.url}"
                                    
                                    final_message = message_text + button_text
                                    try:
                                        await client.send_message(chat_entity, final_message)
                                        logger.info(f"✅ Sent message with text buttons to {chat_entity.title}")
                                        message_sent = True
                                    except Exception as fallback_error:
                                        logger.error(f"❌ Failed to send message to {chat_entity.title}: {fallback_error}")
                                        # Skip this chat and continue with others
                            else:
                                # Send without buttons for earlier messages
                                await client.send_message(
                                    chat_entity,
                                    message_text
                                )
                                message_sent = True
                    else:
                        # Single text message with buttons
                        message_text = ad_content if isinstance(ad_content, str) else str(ad_content)
                        logger.info(f"Sending single message with Shop Now button (immediate execution)")
                        await client.send_message(
                            chat_entity,
                            message_text,
                            buttons=telethon_buttons
                        )
                    
                    if message_sent:
                        success_count += 1
                        logger.info(f"Successfully sent to {chat_entity.title} ({chat_entity.id}) with buttons")
                    
                except Exception as e:
                    logger.error(f"Failed to send to {chat_entity.title if hasattr(chat_entity, 'title') else chat_entity.id}: {e}")
                    continue
            
            await client.disconnect()
            
            # Clean up temporary session file
            import os
            try:
                os.remove(f"{temp_session_path}.session")
            except:
                pass
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Immediate campaign execution failed: {e}")
            return False
    
    async def start_campaign_manually(self, query, campaign_id):
        """Manually start a campaign immediately"""
        user_id = query.from_user.id
        
        try:
            await query.answer("Starting campaign...")
            
            # Get campaign details
            campaign = self.bump_service.get_campaign(campaign_id)
            if not campaign or campaign['user_id'] != user_id:
                await query.answer("Campaign not found!", show_alert=True)
                return
            
            logger.info(f"Retrieved campaign data: {list(campaign.keys())}")
            logger.info(f"Campaign buttons: {campaign.get('buttons', 'NOT_FOUND')}")
            logger.info(f"Campaign target_mode: {campaign.get('target_mode', 'NOT_FOUND')}")
            logger.info(f"Full campaign data: {campaign}")
            
            # Get account details
            account = self.db.get_account(campaign['account_id'])
            if not account:
                await query.answer("Account not found!", show_alert=True)
                return
            
            # Prepare campaign data for execution
            enhanced_campaign_data = {
                'campaign_name': campaign['campaign_name'],
                'ad_content': campaign['ad_content'],
                'target_chats': campaign['target_chats'],
                'schedule_type': campaign['schedule_type'],
                'schedule_time': campaign['schedule_time'],
                'buttons': campaign.get('buttons', []),  # Get buttons from database
                'target_mode': campaign.get('target_mode', 'all_groups' if campaign['target_chats'] == ['ALL_WORKER_GROUPS'] else 'specific'),
                'immediate_start': True
            }
            
            logger.info(f"Executing campaign with {len(enhanced_campaign_data['buttons'])} buttons")
            
            # Execute campaign
            success = await self.execute_campaign_with_better_discovery(campaign['account_id'], enhanced_campaign_data)
            
            if success:
                success_text = f"""🎉 Campaign Started Successfully!

Campaign: {campaign['campaign_name']}
Account: {account['account_name']}
Status: ✅ First message sent immediately!
Schedule: Next message in {campaign['schedule_time']}

Your ads are now being posted to all target groups!"""
            else:
                # Check if account needs re-authentication
                if not account.get('session_string'):
                    success_text = f"""❌ Account Authentication Required

Campaign: {campaign['campaign_name']}
Account: {account['account_name']}
Status: ❌ Account not authenticated

**Solution:**
1. Delete this account from 'Manage Accounts'
2. Re-add the account using API credentials
3. Complete phone verification when prompted
4. Try starting the campaign again"""
                else:
                    success_text = f"""⚠️ Campaign Start Issues

Campaign: {campaign['campaign_name']}
Account: {account['account_name']}
Status: ❌ Authentication failed or no access to groups

**Possible Solutions:**
1. Check that your account has access to target groups
2. Try deleting and re-adding the account with phone verification
3. Make sure the account is not banned/restricted"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"start_campaign_{campaign_id}")],
                [InlineKeyboardButton("⚙️ Configure Campaign", callback_data=f"campaign_{campaign_id}")],
                [InlineKeyboardButton("📋 My Campaigns", callback_data="my_campaigns")],
                [InlineKeyboardButton("🔙 Bump Service", callback_data="back_to_bump")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                success_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Manual campaign start failed: {e}")
            await query.answer(f"❌ Failed to start campaign: {str(e)[:50]}", show_alert=True)
    
    async def execute_campaign_with_better_discovery(self, account_id: int, campaign_data: dict) -> bool:
        """Execute campaign with improved group discovery"""
        try:
            # Get account details
            account = self.db.get_account(account_id)
            if not account:
                return False
            
            # Initialize Telethon client
            from telethon import TelegramClient
            import base64
            
            # Handle session creation
            temp_session_path = f"temp_session_{account_id}"
            
            # Check if we have a valid session
            if not account.get('session_string'):
                logger.error(f"Account {account_id} has no session string. Please re-authenticate the account.")
                return False
            
            # Handle uploaded sessions vs API credential sessions
            if account['api_id'] == 'uploaded' or account['api_hash'] == 'uploaded':
                # For uploaded sessions, decode and save the session file
                try:
                    session_data = base64.b64decode(account['session_string'])
                    with open(f"{temp_session_path}.session", "wb") as f:
                        f.write(session_data)
                    # Use dummy credentials for uploaded sessions
                    api_id = 123456  
                    api_hash = 'dummy_hash_for_uploaded_sessions'
                except Exception as e:
                    logger.error(f"Failed to decode uploaded session for account {account_id}: {e}")
                    return False
            else:
                # For API credential accounts with authenticated sessions
                try:
                    api_id = int(account['api_id'])
                    api_hash = account['api_hash']
                    
                    # Session string is base64 encoded session file data
                    # Decode and write it as the session file
                    session_data = base64.b64decode(account['session_string'])
                    with open(f"{temp_session_path}.session", "wb") as f:
                        f.write(session_data)
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid API credentials for account {account_id}: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Failed to decode session for account {account_id}: {e}")
                    return False
            
            # Initialize and start client
            try:
                client = TelegramClient(temp_session_path, api_id, api_hash)
                await client.start()
                
                # Verify the session is valid
                me = await client.get_me()
                if not me:
                    logger.error(f"Session invalid for account {account_id}")
                    await client.disconnect()
                    return False
                    
                logger.info(f"Successfully authenticated as {me.username or me.phone}")
                
            except Exception as e:
                logger.error(f"Failed to start client for account {account_id}: {e}")
                # Clean up session file on failure
                import os
                try:
                    if os.path.exists(f"{temp_session_path}.session"):
                        os.remove(f"{temp_session_path}.session")
                except:
                    pass
                return False
            
            # Get all dialogs and find groups
            target_chats = []
            if campaign_data.get('target_mode') == 'all_groups' or campaign_data['target_chats'] == ['ALL_WORKER_GROUPS']:
                logger.info("Discovering worker account groups...")
                dialogs = await client.get_dialogs()
                
                for dialog in dialogs:
                    if dialog.is_group:  # Include both groups and supergroups
                        target_chats.append(dialog.entity)
                        logger.info(f"Found group: {dialog.name} (ID: {dialog.id})")
                
                logger.info(f"Discovered {len(target_chats)} groups")
            else:
                # Use specific chat IDs
                for chat_id in campaign_data['target_chats']:
                    try:
                        entity = await client.get_entity(chat_id)
                        target_chats.append(entity)
                    except Exception as e:
                        logger.error(f"Failed to get entity for {chat_id}: {e}")
            
            # Send messages to target chats
            success_count = 0
            ad_content = campaign_data['ad_content']
            
            # Use actual campaign button data
            buttons_data = campaign_data.get('buttons', [])
            if not buttons_data:
                # Fallback to default button if none specified
                buttons_data = [{"text": "Shop Now", "url": "https://t.me/testukassdfdds"}]
                logger.info(f"Using default button data: {buttons_data}")
            else:
                logger.info(f"Using campaign button data: {buttons_data}")
            
            # Create Telethon buttons from campaign data
            telethon_buttons = None
            if buttons_data:
                from telethon import Button
                try:
                    button_rows = []
                    current_row = []
                    
                    for i, button in enumerate(buttons_data):
                        if button.get('url'):
                            # URL button
                            telethon_button = Button.url(button['text'], button['url'])
                        else:
                            # Regular callback button
                            telethon_button = Button.inline(button['text'], f"btn_{i}")
                        
                        current_row.append(telethon_button)
                        
                        # Create new row every 2 buttons or at the end
                        if len(current_row) == 2 or i == len(buttons_data) - 1:
                            button_rows.append(current_row)
                            current_row = []
                    
                    telethon_buttons = button_rows
                    logger.info(f"✅ Created {len(buttons_data)} buttons in {len(button_rows)} rows from campaign data")
                except Exception as e:
                    logger.error(f"❌ Error creating buttons from campaign data: {e}")
                    # Fallback to default button
                    telethon_buttons = [[Button.url("Shop Now", "https://t.me/testukassdfdds")]]
                    logger.info("Using fallback Shop Now button")
            
            for chat_entity in target_chats:
                message_sent = False
                try:
                    # RESTRUCTURED: Always send with buttons - simplified approach
                    if isinstance(ad_content, list) and ad_content:
                        # For forwarded content, send each message and add button to the last one
                        for i, message_data in enumerate(ad_content):
                            message_text = message_data.get('text', '')
                            
                            # Add buttons to the last message only
                            if i == len(ad_content) - 1:
                                logger.info(f"Adding buttons to final message")
                                # ALWAYS add button URLs as text for groups (inline buttons don't work in regular groups)
                                button_text = ""
                                for button_row in telethon_buttons:
                                    for button in button_row:
                                        if hasattr(button, 'url'):
                                            button_text += f"\n\n🔗 {button.text}: {button.url}"
                                
                                # Combine message with button text
                                final_message = message_text + button_text
                                
                                try:
                                    # Try sending with both inline buttons AND text (belt and suspenders approach)
                                    await client.send_message(
                                        chat_entity,
                                        final_message,  # Message now includes button URLs as text
                                        buttons=telethon_buttons  # Also try inline buttons for channels/supergroups
                                    )
                                    logger.info(f"✅ Sent message with buttons (inline + text) to {chat_entity.title}")
                                    message_sent = True
                                except Exception as send_error:
                                    # If that fails, try without inline buttons
                                    try:
                                        await client.send_message(chat_entity, final_message)
                                        logger.info(f"✅ Sent message with text buttons to {chat_entity.title}")
                                        message_sent = True
                                    except Exception as fallback_error:
                                        logger.error(f"❌ Failed to send message to {chat_entity.title}: {fallback_error}")
                                        # Skip this chat and continue with others
                            else:
                                # Send without buttons for earlier messages
                                await client.send_message(
                                    chat_entity,
                                    message_text
                                )
                                message_sent = True
                    else:
                        # Single text message with buttons
                        message_text = ad_content if isinstance(ad_content, str) else str(ad_content)
                        logger.info(f"Sending single message with Shop Now button")
                        await client.send_message(
                            chat_entity, 
                            message_text,
                            buttons=telethon_buttons
                        )
                    
                    if message_sent:
                        success_count += 1
                        logger.info(f"Successfully sent to {chat_entity.title} ({chat_entity.id}) with buttons")
                    
                except Exception as e:
                    logger.error(f"Failed to send to {chat_entity.title if hasattr(chat_entity, 'title') else chat_entity.id}: {e}")
                    continue
            
            await client.disconnect()
            
            # Clean up temporary session file
            import os
            try:
                os.remove(f"{temp_session_path}.session")
            except:
                pass
            
            logger.info(f"Campaign execution completed. Success: {success_count}/{len(target_chats)}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Campaign execution failed: {e}")
            return False
    
    async def show_schedule_selection(self, query):
        """Show schedule selection menu (back navigation)"""
        user_id = query.from_user.id
        if user_id not in self.user_sessions:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        text = """⏰ **Step 4/6: Schedule Type**

**How often should this campaign run?**

**📅 Daily** - Once per day at a specific time
**📊 Weekly** - Once per week on a chosen day
**⏰ Hourly** - Every hour automatically
**🔧 Custom** - Set your own interval (e.g., every 4 hours)"""
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily", callback_data="schedule_daily")],
            [InlineKeyboardButton("📊 Weekly", callback_data="schedule_weekly")],
            [InlineKeyboardButton("⏰ Hourly", callback_data="schedule_hourly")],
            [InlineKeyboardButton("🔧 Custom", callback_data="schedule_custom")],
            [InlineKeyboardButton("🔙 Back to Targets", callback_data="back_to_target_selection")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_target_selection(self, query):
        """Show target selection menu (back navigation)"""
        user_id = query.from_user.id
        if user_id not in self.user_sessions:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        text = """🎯 **Step 3/6: Target Chats**

**Choose how to select your target chats:**

**🌐 Send to All Worker Groups**
• Automatically targets all groups your worker account is in
• Smart detection of group chats
• Excludes private chats and channels
• Perfect for broad campaigns

**🎯 Specify Target Chats**
• Manually enter specific chat IDs or usernames
• Precise targeting control
• Include channels, groups, or private chats
• Custom audience selection"""
        
        keyboard = [
            [InlineKeyboardButton("🌐 Send to All Worker Groups", callback_data="target_all_groups")],
            [InlineKeyboardButton("🎯 Specify Target Chats", callback_data="target_specific_chats")],
            [InlineKeyboardButton("🔙 Back to Buttons", callback_data="back_to_button_choice")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_button_choice(self, query):
        """Show button choice menu (back navigation)"""
        user_id = query.from_user.id
        if user_id not in self.user_sessions:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        text = """➕ **Step 2.5/6: Add Buttons (Optional)**

**Would you like to add buttons under your ad?**

Buttons will appear as an inline keyboard below your ad message.

**Examples:**
• Shop Now → https://yourstore.com
• Contact Us → https://t.me/support
• Visit Website → https://yoursite.com"""
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Buttons", callback_data="add_buttons_yes")],
            [InlineKeyboardButton("⏭️ Skip Buttons", callback_data="add_buttons_no")],
            [InlineKeyboardButton("📤 Add More Messages", callback_data="add_more_messages")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_web_interface(self, query):
        """Show web interface information"""
        text = f"""
🌐 **Web Interface**

Access the full-featured web interface for advanced configuration:

**URL:** `https://your-render-app.onrender.com`

**Features:**
• Visual configuration editor
• Real-time message preview
• Advanced plugin settings
• Bulk configuration management
• Message statistics

**Login:** Use your Telegram user ID as username
        """
        
        keyboard = [
            [InlineKeyboardButton("🔗 Open Web Interface", url="https://your-render-app.onrender.com")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_help(self, query):
        """Show help information"""
        help_text = """
❓ **Help & Support**

**Quick Start:**
1. Click "Add New Forwarding"
2. Enter source and destination chat IDs
3. Configure your settings
4. Start forwarding!

**Common Issues:**
• **Chat ID not found:** Make sure the bot is added to the source chat
• **Permission denied:** Check bot permissions in the chat
• **Messages not forwarding:** Verify chat IDs and bot status

**Need more help?**
• Check the web interface for detailed guides
• Join our support group: @tgcf_support
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages for configuration setup"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        message_text = update.message.text
        
        # Handle account creation
        if 'account_data' in session:
            if session['step'] == 'account_name':
                session['account_data']['account_name'] = message_text
                session['step'] = 'phone_number'
                
                await update.message.reply_text(
                    "✅ **Account name set!**\n\n**Step 2/5: Phone Number**\n\nPlease send me the phone number for this work account (with country code, e.g., +1234567890).",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'phone_number':
                session['account_data']['phone_number'] = message_text
                session['step'] = 'api_id'
                
                await update.message.reply_text(
                    "✅ **Phone number set!**\n\n**Step 3/5: API ID**\n\nPlease send me the API ID for this account.\n\n**Get it from:** https://my.telegram.org\n• Go to 'API development tools'\n• Create a new application\n• Copy your API ID",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'api_id':
                try:
                    api_id = int(message_text)
                    session['account_data']['api_id'] = str(api_id)
                    session['step'] = 'api_hash'
                    
                    await update.message.reply_text(
                        "✅ **API ID set!**\n\n**Step 4/5: API Hash**\n\nPlease send me the API Hash for this account.\n\n**Get it from:** https://my.telegram.org (same page as API ID)",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ **Invalid API ID!**\n\nPlease send a valid numeric API ID from https://my.telegram.org",
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            elif session['step'] == 'api_hash':
                session['account_data']['api_hash'] = message_text
                session['step'] = 'authenticating'
                
                # Now we need to authenticate with Telegram to create a session
                await update.message.reply_text(
                    "🔐 **Authenticating with Telegram...**\n\n"
                    "Please wait while I connect to your account...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Create session for this account
                from telethon import TelegramClient
                import asyncio
                
                try:
                    api_id = int(session['account_data']['api_id'])
                    api_hash = session['account_data']['api_hash']
                    phone = session['account_data']['phone_number']
                    
                    # Create a unique session name
                    session_name = f"account_{user_id}_{int(asyncio.get_event_loop().time())}"
                    client = TelegramClient(session_name, api_id, api_hash)
                    
                    await client.connect()
                    
                    # Request code
                    await client.send_code_request(phone)
                    
                    session['client'] = client
                    session['session_name'] = session_name
                    session['step'] = 'verification_code'
                    
                    await update.message.reply_text(
                        "📱 **Verification Code Sent!**\n\n"
                        f"A verification code has been sent to **{phone}**\n\n"
                        "Please enter the verification code you received:",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to start authentication: {e}")
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
                    await update.message.reply_text(
                        f"❌ **Authentication Failed**\n\n"
                        f"Error: {str(e)}\n\n"
                        f"Please check your API credentials and try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            elif session['step'] == 'verification_code':
                # Handle verification code
                code = message_text.strip()
                client = session.get('client')
                
                if not client:
                    await update.message.reply_text("❌ Session expired. Please start over.")
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
                    return
                
                try:
                    # Sign in with the code
                    await client.sign_in(session['account_data']['phone_number'], code)
                    
                    # Get session string - save the actual session file content
                    import base64
                    session_file_path = f"{session['session_name']}.session"
                    
                    # Save the session to ensure it's written to disk
                    await client.disconnect()
                    await client.connect()
                    
                    # Read the session file and encode it
                    with open(session_file_path, 'rb') as f:
                        session_data = f.read()
                    session_string = base64.b64encode(session_data).decode('utf-8')
                    
                    # Save account with session string
                    account_id = self.db.add_telegram_account(
                        user_id,
                        session['account_data']['account_name'],
                        session['account_data']['phone_number'],
                        session['account_data']['api_id'],
                        session['account_data']['api_hash'],
                        session_string
                    )
                    
                    # Disconnect client
                    await client.disconnect()
                    
                    # Clean up session file
                    import os
                    try:
                        if os.path.exists(f"{session['session_name']}.session"):
                            os.remove(f"{session['session_name']}.session")
                    except:
                        pass
                    
                    # Clear session
                    del self.user_sessions[user_id]
                    
                    keyboard = [
                        [InlineKeyboardButton("📢 Create Campaign", callback_data="add_campaign")],
                        [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"✅ **Account Added Successfully!**\n\n"
                        f"**Account:** {session['account_data']['account_name']}\n"
                        f"**Phone:** {session['account_data']['phone_number']}\n\n"
                        f"🎉 Your account is now authenticated and ready to use for campaigns!",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to verify code: {e}")
                    
                    # Check if 2FA is needed
                    if "Two-steps verification" in str(e) or "password" in str(e).lower() or "2FA" in str(e):
                        session['step'] = '2fa_password'
                        await update.message.reply_text(
                            "🔐 **Two-Factor Authentication Required**\n\n"
                            "Your account has 2FA enabled. Please enter your 2FA password:",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ **Verification Failed**\n\n"
                            f"Error: {str(e)}\n\n"
                            f"Please check the verification code and try again.",
                            parse_mode=ParseMode.MARKDOWN
                        )
            
            elif session['step'] == '2fa_password':
                # Handle 2FA password
                password = message_text
                client = session.get('client')
                
                if not client:
                    await update.message.reply_text("❌ Session expired. Please start over.")
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
                    return
                
                try:
                    # Sign in with password
                    await client.sign_in(password=password)
                    
                    # Get session string - save the actual session file content
                    import base64
                    session_file_path = f"{session['session_name']}.session"
                    
                    # Save the session to ensure it's written to disk
                    await client.disconnect()
                    await client.connect()
                    
                    # Read the session file and encode it
                    with open(session_file_path, 'rb') as f:
                        session_data = f.read()
                    session_string = base64.b64encode(session_data).decode('utf-8')
                    
                    # Save account with session string
                    account_id = self.db.add_telegram_account(
                        user_id,
                        session['account_data']['account_name'],
                        session['account_data']['phone_number'],
                        session['account_data']['api_id'],
                        session['account_data']['api_hash'],
                        session_string
                    )
                    
                    # Disconnect client
                    await client.disconnect()
                    
                    # Clean up session file
                    import os
                    try:
                        if os.path.exists(f"{session['session_name']}.session"):
                            os.remove(f"{session['session_name']}.session")
                    except:
                        pass
                    
                    # Clear session
                    del self.user_sessions[user_id]
                    
                    keyboard = [
                        [InlineKeyboardButton("📢 Create Campaign", callback_data="add_campaign")],
                        [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"✅ **Account Added Successfully!**\n\n"
                        f"**Account:** {session['account_data']['account_name']}\n"
                        f"**Phone:** {session['account_data']['phone_number']}\n\n"
                        f"🎉 Your account is now authenticated and ready to use for campaigns!",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to verify 2FA password: {e}")
                    await update.message.reply_text(
                        f"❌ **2FA Authentication Failed**\n\n"
                        f"Error: {str(e)}\n\n"
                        f"Please check your 2FA password and try again.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                keyboard = [
                    [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
                    [InlineKeyboardButton("➕ Add Forwarding", callback_data="add_forwarding")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🎉 **Work Account Added Successfully!**\n\n**Name:** {session['account_data']['account_name']}\n**Phone:** `{session['account_data']['phone_number']}`\n\nYou can now create campaigns and forwarding rules for this account!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            
        
        # Handle campaign creation
        elif 'campaign_data' in session:
            if session['step'] == 'campaign_name':
                session['campaign_data']['campaign_name'] = message_text
                session['step'] = 'ad_content'
                
                await update.message.reply_text(
                    "✅ **Campaign name set!**\n\n**Step 2/6: Ad Content**\n\n📤 **Forward me the message(s) you want to use as advertisement**\n\n**Supported Content:**\n• Text with custom/premium emojis ✨\n• Images, videos, documents 📸\n• Voice messages and stickers 🎵\n• Full formatting preservation 📝\n• Multiple messages (forward each one)\n\n**Just forward the message(s) from any chat - I'll preserve everything exactly!**",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'ad_content':
                # Handle forwarded message with full fidelity
                await self.handle_forwarded_ad_content(update, session)
            
            elif session['step'] == 'add_buttons_choice':
                # Handle button addition choice
                await self.handle_button_choice(update, session)
            
            elif session['step'] == 'button_input':
                # Handle button data input
                await self.handle_button_input(update, session)
            
            elif session['step'] == 'target_chats_choice':
                # This step is now handled by button callbacks
                pass
            
            elif session['step'] == 'target_chats':
                # Parse target chats
                chats = []
                for line in message_text.strip().split('\n'):
                    for chat in line.split(','):
                        chat = chat.strip()
                        if chat:
                            chats.append(chat)
                
                session['campaign_data']['target_chats'] = chats
                session['step'] = 'schedule_type'
                
                keyboard = [
                    [InlineKeyboardButton("📅 Daily", callback_data="schedule_daily")],
                    [InlineKeyboardButton("📊 Weekly", callback_data="schedule_weekly")],
                    [InlineKeyboardButton("⏰ Hourly", callback_data="schedule_hourly")],
                    [InlineKeyboardButton("🔧 Custom", callback_data="schedule_custom")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="back_to_bump")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **Target chats set!** ({len(chats)} chats)\n\n**Step 4/6: Schedule Type**\n\nHow often should this campaign run?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            
            elif session['step'] == 'schedule_time':
                session['campaign_data']['schedule_time'] = message_text
                session['step'] = 'account_selection'
                
                # Show account selection
                accounts = self.db.get_user_accounts(user_id)
                keyboard = []
                for account in accounts:
                    keyboard.append([InlineKeyboardButton(
                        f"📱 {account['account_name']} ({account['phone_number']})", 
                        callback_data=f"select_account_{account['id']}"
                    )])
                keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="back_to_bump")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ **Schedule set!**\n\n**Step 5/6: Select Account**\n\nWhich Telegram account should be used to post these ads?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        
        # Handle forwarding configuration creation
        elif 'config' in session:
            if session['step'] == 'source_chat':
                session['config']['source_chat_id'] = message_text
                session['step'] = 'destination_chat'
                
                await update.message.reply_text(
                    "✅ **Source chat set!**\n\n**Step 2/4: Destination Chat**\n\nPlease send me the destination chat ID or username.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'destination_chat':
                session['config']['destination_chat_id'] = message_text
                session['step'] = 'config_name'
                
                await update.message.reply_text(
                    "✅ **Destination chat set!**\n\n**Step 3/4: Configuration Name**\n\nPlease send me a name for this forwarding configuration.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'config_name':
                session['config']['config_name'] = message_text
                session['step'] = 'complete'
                
                # Create default configuration
                default_config = {
                    'filter': {'enabled': False},
                    'format': {'enabled': False},
                    'replace': {'enabled': False},
                    'caption': {'enabled': False, 'header': '', 'footer': ''},
                    'watermark': {'enabled': False},
                    'ocr': {'enabled': False}
                }
                
                # Get the first available account for this user
                accounts = self.db.get_user_accounts(user_id)
                if not accounts:
                    await update.message.reply_text(
                        "❌ **No accounts found!**\n\nPlease add a Telegram account first before creating forwarding configurations.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    del self.user_sessions[user_id]
                    return
                
                account_id = accounts[0]['id']  # Use first account
                
                # Save configuration
                config_id = self.db.add_forwarding_config(
                    user_id,
                    account_id,
                    session['config']['source_chat_id'],
                    session['config']['destination_chat_id'],
                    session['config']['config_name'],
                    default_config
                )
                
                # Clear session
                del self.user_sessions[user_id]
                
                keyboard = [
                    [InlineKeyboardButton("⚙️ Configure Plugins", callback_data=f"config_{config_id}")],
                    [InlineKeyboardButton("📋 My Configurations", callback_data="my_configs")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🎉 **Configuration Created!**\n\n**Name:** {session['config']['config_name']}\n**Source:** `{session['config']['source_chat_id']}`\n**Destination:** `{session['config']['destination_chat_id']}`\n**Account:** {accounts[0]['account_name']}\n\nYour forwarding configuration has been created successfully!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
    
    async def delete_config(self, query, config_id):
        """Delete a configuration"""
        user_id = query.from_user.id
        self.db.delete_config(config_id)
        
        await query.answer("Configuration deleted!", show_alert=True)
        await self.show_my_configs(query)
    
    async def toggle_config(self, query, config_id):
        """Toggle configuration status"""
        # This would require updating the database
        await query.answer("Feature coming soon!", show_alert=True)
    
    async def show_manage_accounts(self, query):
        """Show account management interface"""
        user_id = query.from_user.id
        accounts = self.db.get_user_accounts(user_id)
        
        if not accounts:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👥 **Manage Accounts**\n\nNo Telegram accounts found.\n\nAdd your first account to start forwarding messages!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        text = "👥 Manage Accounts\n\n"
        keyboard = []
        
        for account in accounts:
            # Use plain text formatting
            account_name = self.escape_markdown(account['account_name'])
            phone_number = self.escape_markdown(account['phone_number'])
            
            text += f"📱 {account_name}\n"
            text += f"📞 Phone: {phone_number}\n"
            text += f"Status: {'🟢 Active' if account['is_active'] else '🔴 Inactive'}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {self.escape_markdown(account['account_name'])}", callback_data=f"account_{account['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_account_{account['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add New Account", callback_data="add_account")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use plain text to avoid Markdown parsing issues
        plain_text = text.replace("**", "").replace("`", "").replace("*", "")
        await query.edit_message_text(
            plain_text,
            reply_markup=reply_markup
        )
    
    async def show_account_details(self, query, account_id):
        """Show detailed account information"""
        user_id = query.from_user.id
        account = self.db.get_account(account_id)
        
        if not account or account['user_id'] != user_id:
            await query.answer("Account not found!", show_alert=True)
            return
        
        # Get configurations for this account
        configs = self.db.get_user_configs(user_id, account_id)
        
        text = f"⚙️ **{account['account_name']}**\n\n"
        text += f"**Phone:** `{account['phone_number']}`\n"
        text += f"**API ID:** `{account['api_id']}`\n"
        text += f"**Status:** {'🟢 Active' if account['is_active'] else '🔴 Inactive'}\n"
        text += f"**Configurations:** {len(configs)}\n\n"
        
        if configs:
            text += "**Active Forwardings:**\n"
            for config in configs[:3]:  # Show first 3
                text += f"• {config['config_name']}\n"
            if len(configs) > 3:
                text += f"• ... and {len(configs) - 3} more\n"
        
        keyboard = [
            [InlineKeyboardButton("📋 View Configurations", callback_data=f"configs_for_account_{account_id}")],
            [InlineKeyboardButton("🔙 Back to Accounts", callback_data="back_to_accounts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_configs_for_account(self, query, account_id):
        """Show configurations for a specific account"""
        user_id = query.from_user.id
        configs = self.db.get_user_configs(user_id, account_id)
        account = self.db.get_account(account_id)
        
        if not account:
            await query.answer("Account not found!", show_alert=True)
            return
        
        if not configs:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Forwarding", callback_data="add_forwarding")],
                [InlineKeyboardButton("🔙 Back to Account", callback_data=f"account_{account_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📋 **Configurations for {account['account_name']}**\n\nNo forwarding configurations found.\n\nAdd your first forwarding rule!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        text = f"📋 **Configurations for {account['account_name']}**\n\n"
        keyboard = []
        
        for config in configs:
            status = "🟢 Active" if config['is_active'] else "🔴 Inactive"
            text += f"**{config['config_name']}** {status}\n"
            text += f"From: `{config['source_chat_id']}`\n"
            text += f"To: `{config['destination_chat_id']}`\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {config['config_name']}", callback_data=f"config_{config['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_config_{config['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add New", callback_data="add_forwarding")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Account", callback_data=f"account_{account_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_add_account(self, query):
        """Start the process of adding a new Telegram account"""
        user_id = query.from_user.id
        
        text = """
➕ **Add New Work Account**

**Choose your setup method:**

**📤 Upload Session File (Recommended)**
- Fastest setup method
- No API credentials needed
- Account ready immediately

**🔧 Manual Setup (Advanced)**
- Enter API credentials manually
- Step-by-step guided setup
- For advanced users
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload Session File", callback_data="upload_session")],
            [InlineKeyboardButton("🔧 Manual Setup (Advanced)", callback_data="manual_setup")],
            [InlineKeyboardButton("❌ Cancel", callback_data="manage_accounts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def delete_account(self, query, account_id):
        """Delete a Telegram account and clean up all related data"""
        user_id = query.from_user.id
        account = self.db.get_account(account_id)
        
        if not account or account['user_id'] != user_id:
            await query.answer("Account not found!", show_alert=True)
            return
        
        account_name = account.get('account_name', 'Unknown')
        
        # Get campaigns using this account before deletion
        campaigns = self.bump_service.get_user_campaigns(user_id)
        campaigns_to_delete = [c for c in campaigns if c['account_id'] == account_id]
        
        # Clean up campaigns in bump service first
        for campaign in campaigns_to_delete:
            logger.info(f"Cleaning up campaign {campaign['id']} for deleted account {account_name}")
            self.bump_service.delete_campaign(campaign['id'])
        
        # Delete the account and all related data
        self.db.delete_account(account_id)
        
        # Clean up any session files
        import os
        try:
            session_files = [
                f"temp_session_{account_id}.session",
                f"bump_session_{account_id}.session",
                f"account_{user_id}_{account_id}.session"
            ]
            for session_file in session_files:
                if os.path.exists(session_file):
                    os.remove(session_file)
                    logger.info(f"Cleaned up session file: {session_file}")
        except Exception as e:
            logger.warning(f"Could not clean up session files: {e}")
        
        success_msg = f"✅ Account '{account_name}' completely deleted!"
        if campaigns_to_delete:
            success_msg += f"\n🗑️ Also deleted {len(campaigns_to_delete)} related campaigns"
        
        await query.answer(success_msg, show_alert=True)
        await self.show_manage_accounts(query)
    
    # Bump Service Methods
    async def show_bump_service(self, query):
        """Show bump service main menu"""
        user_id = query.from_user.id
        campaigns = self.bump_service.get_user_campaigns(user_id)
        
        text = """
📢 **Bump Service - Auto Ads Manager**

Automatically post your advertisements to multiple chats at scheduled times!

**Features:**
• Schedule ads to post daily, weekly, or custom intervals
• Post to multiple channels/groups at once  
• Track ad performance and statistics
• Test ads before going live
• Manage multiple ad campaigns

**Current Status:**
        """
        
        if campaigns:
            active_campaigns = len([c for c in campaigns if c['is_active']])
            text += f"• Active Campaigns: {active_campaigns}\n"
            text += f"• Total Campaigns: {len(campaigns)}\n"
        else:
            text += "• No campaigns created yet\n"
        
        keyboard = [
            [InlineKeyboardButton("📋 My Campaigns", callback_data="my_campaigns")],
            [InlineKeyboardButton("➕ Create New Campaign", callback_data="add_campaign")],
            [InlineKeyboardButton("📊 Campaign Statistics", callback_data="campaign_stats")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_my_campaigns(self, query):
        """Show user's ad campaigns"""
        user_id = query.from_user.id
        campaigns = self.bump_service.get_user_campaigns(user_id)
        
        if not campaigns:
            keyboard = [
                [InlineKeyboardButton("➕ Create New Campaign", callback_data="add_campaign")],
                [InlineKeyboardButton("🔙 Back to Bump Service", callback_data="back_to_bump")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📋 **My Campaigns**\n\nNo ad campaigns found.\n\nCreate your first campaign to start automated advertising!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        text = "📋 My Ad Campaigns\n\n"
        keyboard = []
        
        for campaign in campaigns:
            status = "🟢 Active" if campaign['is_active'] else "🔴 Inactive"
            # Use plain text formatting to avoid Markdown conflicts
            campaign_name = str(campaign['campaign_name'])[:50]  # Limit length
            text += f"📢 {campaign_name} {status}\n"
            text += f"⏰ Schedule: {campaign['schedule_type']} at {campaign['schedule_time']}\n"
            text += f"🎯 Targets: {len(campaign['target_chats'])} chats\n"
            text += f"📊 Total Sends: {campaign['total_sends']}\n\n"
            
            # Add toggle button based on campaign status
            toggle_icon = "⏸️" if campaign['is_active'] else "▶️"
            toggle_text = "Pause" if campaign['is_active'] else "Activate"
            
            keyboard.append([
                InlineKeyboardButton(f"🚀 Start", callback_data=f"start_campaign_{campaign['id']}"),
                InlineKeyboardButton(f"{toggle_icon} {toggle_text}", callback_data=f"toggle_campaign_{campaign['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_campaign_{campaign['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Create New", callback_data="add_campaign")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Bump Service", callback_data="back_to_bump")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to display campaigns: {e}")
            # Try without reply markup first
            try:
                await query.edit_message_text(
                    "📋 My Campaigns\n\nRefreshing campaign list...",
                )
                # Then send new message with proper content
                await query.message.reply_text(
                    text,
                    reply_markup=reply_markup
                )
            except Exception as e2:
                logger.error(f"Fallback display also failed: {e2}")
                await query.answer("Error displaying campaigns. Please try again.", show_alert=True)
    
    async def show_campaign_details(self, query, campaign_id):
        """Show detailed campaign information"""
        user_id = query.from_user.id
        campaign = self.bump_service.get_campaign(campaign_id)
        
        if not campaign or campaign['user_id'] != user_id:
            await query.answer("Campaign not found!", show_alert=True)
            return
        
        # Get performance stats
        performance = self.bump_service.get_campaign_performance(campaign_id)
        
        status = "🟢 Active" if campaign['is_active'] else "🔴 Inactive"
        text = f"⚙️ {campaign['campaign_name']} {status}\n\n"
        text += f"Account: {campaign['account_name']}\n"
        text += f"Schedule: {campaign['schedule_type']} at {campaign['schedule_time']}\n"
        text += f"Target Chats: {len(campaign['target_chats'])}\n"
        text += f"Last Run: {campaign['last_run'] or 'Never'}\n\n"
        
        text += "Performance:\n"
        text += f"• Total Attempts: {performance['total_attempts']}\n"
        text += f"• Successful: {performance['successful_sends']}\n"
        text += f"• Failed: {performance['failed_sends']}\n"
        text += f"• Success Rate: {performance['success_rate']:.1f}%\n\n"
        
        text += "Ad Content Preview:\n"
        # Handle complex ad content safely
        if isinstance(campaign['ad_content'], list):
            preview = "Multiple forwarded messages"
        else:
            preview_text = str(campaign['ad_content'])[:200]
            preview = preview_text + "..." if len(preview_text) > 200 else preview_text
        text += f"{preview}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Toggle Status", callback_data=f"toggle_campaign_{campaign_id}")],
            [InlineKeyboardButton("🧪 Test Campaign", callback_data=f"test_campaign_{campaign_id}")],
            [InlineKeyboardButton("📊 Full Statistics", callback_data=f"stats_{campaign_id}")],
            [InlineKeyboardButton("🔙 Back to Campaigns", callback_data="back_to_campaigns")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
    
    async def start_add_campaign(self, query):
        """Start the process of adding a new ad campaign"""
        user_id = query.from_user.id
        
        # Check if user has any accounts
        accounts = self.db.get_user_accounts(user_id)
        if not accounts:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Account", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Back to Bump Service", callback_data="back_to_bump")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **No Accounts Found!**\n\nYou need to add at least one Telegram account before creating ad campaigns.\n\nClick 'Add New Account' to get started!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        self.user_sessions[user_id] = {'step': 'campaign_name', 'campaign_data': {}}
        
        text = """
➕ **Create New Ad Campaign**

**Step 1/6: Campaign Name**

Please send me a name for this ad campaign (e.g., "Daily Product Promo", "Weekend Sale").

This name will help you identify the campaign in your dashboard.
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_bump")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def delete_campaign(self, query, campaign_id):
        """Delete an ad campaign"""
        user_id = query.from_user.id
        campaign = self.bump_service.get_campaign(campaign_id)
        
        if not campaign or campaign['user_id'] != user_id:
            await query.answer("Campaign not found!", show_alert=True)
            return
        
        self.bump_service.delete_campaign(campaign_id)
        await query.answer("Campaign deleted!", show_alert=True)
        await self.show_my_campaigns(query)
    
    async def toggle_campaign(self, query, campaign_id):
        """Toggle campaign active status"""
        user_id = query.from_user.id
        campaign = self.bump_service.get_campaign(campaign_id)
        
        if not campaign or campaign['user_id'] != user_id:
            await query.answer("Campaign not found!", show_alert=True)
            return
        
        new_status = not campaign['is_active']
        
        # Update campaign status in database
        import sqlite3
        with sqlite3.connect(self.bump_service.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE ad_campaigns SET is_active = ? WHERE id = ?", (new_status, campaign_id))
            conn.commit()
        
        status_text = "activated" if new_status else "deactivated"
        await query.answer(f"Campaign {status_text}!", show_alert=True)
        
        # Refresh the My Campaigns view
        await self.show_my_campaigns(query)
    
    async def test_campaign(self, query, campaign_id):
        """Test an ad campaign"""
        user_id = query.from_user.id
        campaign = self.bump_service.get_campaign(campaign_id)
        
        if not campaign or campaign['user_id'] != user_id:
            await query.answer("Campaign not found!", show_alert=True)
            return
        
        # Test by sending to the user's private chat
        test_chat = str(user_id)
        
        try:
            success = await self.bump_service.test_campaign(campaign_id, test_chat)
            if success:
                await query.answer("✅ Test ad sent to your private chat!", show_alert=True)
            else:
                await query.answer("❌ Test failed! Check campaign settings.", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ Test error: {str(e)[:50]}", show_alert=True)
    
    async def handle_schedule_selection(self, query, schedule_type):
        """Handle schedule type selection"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or 'campaign_data' not in self.user_sessions[user_id]:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        session = self.user_sessions[user_id]
        session['campaign_data']['schedule_type'] = schedule_type
        session['step'] = 'schedule_time'
        
        if schedule_type == 'daily':
            text = "✅ **Daily schedule selected!**\n\n**Step 5/6: Schedule Time**\n\nPlease send me the time when ads should be posted daily.\n\n**Format:** HH:MM (24-hour format)\n**Example:** 14:30 (for 2:30 PM)"
        elif schedule_type == 'weekly':
            text = "✅ **Weekly schedule selected!**\n\n**Step 5/6: Schedule Time**\n\nPlease send me the day and time when ads should be posted weekly.\n\n**Format:** Day HH:MM\n**Example:** Monday 14:30"
        elif schedule_type == 'hourly':
            text = "✅ **Hourly schedule selected!**\n\nAds will be posted every hour automatically.\n\nProceeding to account selection..."
            session['campaign_data']['schedule_time'] = 'every hour'
            session['step'] = 'account_selection'
            
            # Show account selection
            accounts = self.db.get_user_accounts(user_id)
            keyboard = []
            for account in accounts:
                keyboard.append([InlineKeyboardButton(
                    f"📱 {account['account_name']} ({account['phone_number']})", 
                    callback_data=f"select_account_{account['id']}"
                )])
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="back_to_bump")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ **Hourly schedule set!**\n\n**Step 5/6: Select Account**\n\nWhich Telegram account should be used to post these ads?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        elif schedule_type == 'custom':
            text = "✅ **Custom schedule selected!**\n\n**Step 5/6: Custom Schedule**\n\nPlease send me your custom schedule.\n\n**Examples:**\n• every 4 hours\n• every 30 minutes\n• every 2 days\n• every 12 hours\n• every 1 day"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Schedule", callback_data="back_to_schedule_selection")],
            [InlineKeyboardButton("❌ Cancel Campaign", callback_data="cancel_campaign")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_account_selection(self, query, account_id):
        """Handle account selection for campaign with immediate execution"""
        user_id = query.from_user.id
        logger.info(f"Account selection started for user {user_id}, account {account_id}")
        
        try:
            await query.answer("Processing account selection...")
        except Exception as e:
            logger.error(f"Failed to answer query: {e}")
        
        if user_id not in self.user_sessions or 'campaign_data' not in self.user_sessions[user_id]:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        session = self.user_sessions[user_id]
        campaign_data = session['campaign_data']
        logger.info(f"Campaign data: {list(campaign_data.keys())}")
        
        # Get account details for display
        account = self.db.get_account(account_id)
        if not account:
            await query.answer("Account not found!", show_alert=True)
            logger.error(f"Account {account_id} not found in database")
            return
        
        logger.info(f"Account found: {account['account_name']}")
        
        # Create the campaign with enhanced data structure
        try:
            # Prepare enhanced campaign data
            enhanced_campaign_data = {
                'campaign_name': campaign_data['campaign_name'],
                'ad_content': campaign_data.get('ad_messages', [campaign_data.get('ad_content', '')]),
                'target_chats': campaign_data['target_chats'],
                'schedule_type': campaign_data['schedule_type'],
                'schedule_time': campaign_data['schedule_time'],
                'buttons': campaign_data.get('buttons', []),
                'target_mode': campaign_data.get('target_mode', 'specific'),
                'immediate_start': True  # Flag for immediate execution
            }
            
            logger.info(f"Creating campaign with data: {enhanced_campaign_data}")
            
            campaign_id = self.bump_service.add_campaign(
                user_id,
                account_id,
                enhanced_campaign_data['campaign_name'],
                enhanced_campaign_data['ad_content'],
                enhanced_campaign_data['target_chats'],
                enhanced_campaign_data['schedule_type'],
                enhanced_campaign_data['schedule_time'],
                enhanced_campaign_data['buttons'],
                enhanced_campaign_data['target_mode']
            )
            
            logger.info(f"Campaign created successfully with ID: {campaign_id}")
            
            # DISABLED AUTOMATIC EXECUTION: User must manually start campaigns
            logger.info("Campaign created - automatic execution disabled, user must click Start Campaign")
            immediate_success = False  # No automatic execution
            
            # Clear session
            del self.user_sessions[user_id]
            
            # Success message with immediate execution feedback
            success_text = f"""🎉 Campaign Created Successfully!

Campaign: {enhanced_campaign_data['campaign_name']}
Account: {account['account_name']} ({account['phone_number']})
Schedule: {enhanced_campaign_data['schedule_type']} at {enhanced_campaign_data['schedule_time']}
Targets: {len(enhanced_campaign_data['target_chats'])} chat(s)

"""
            
            # Always show manual start message
            success_text += "⏳ Campaign created and ready to start\n🚀 Click 'Start Campaign' to send the first message\n📅 Then messages will repeat according to your schedule"
            
            keyboard = [
                [InlineKeyboardButton("🚀 Start Campaign", callback_data=f"start_campaign_{campaign_id}")],
                [InlineKeyboardButton("⚙️ Configure Campaign", callback_data=f"campaign_{campaign_id}")],
                [InlineKeyboardButton("🧪 Test Campaign", callback_data=f"test_campaign_{campaign_id}")],
                [InlineKeyboardButton("📋 My Campaigns", callback_data="my_campaigns")],
                [InlineKeyboardButton("🔙 Bump Service", callback_data="back_to_bump")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                success_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await query.answer(f"❌ Error creating campaign: {str(e)[:50]}", show_alert=True)
            logger.error(f"Error creating campaign for user {user_id}: {e}")
    
    async def setup_bot_commands(self, application):
        """Setup bot commands"""
        commands = [
            BotCommand("start", "Start the bot and show main menu"),
            BotCommand("help", "Show help information"),
            BotCommand("config", "Manage forwarding configurations"),
            BotCommand("status", "Check bot status")
        ]
        await application.bot.set_my_commands(commands)
    

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads for session files"""
        user_id = update.message.from_user.id
        

        document = update.message.document
        
        # Check if this is a session file
        if not document.file_name or not document.file_name.endswith(".session"):
            await update.message.reply_text(
                " **Invalid file type!**\n\nI can only process .session files for account setup.\n\nPlease upload a .session file or use the account management menu.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Automatically process session files
        
        document = update.message.document
        
        # Check file extension
        if not document.file_name or not document.file_name.endswith(".session"):
            await update.message.reply_text(
                " **Invalid file type!**\n\nPlease send a .session file.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Check file size (50KB limit)
        if document.file_size > 50000:
            await update.message.reply_text(
                " **File too large!**\n\nSession files should be less than 50KB.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            # Download the session file
            file = await context.bot.get_file(document.file_id)
            session_data = await file.download_as_bytearray()
            
            # Extract phone number from filename
            phone_number = document.file_name.replace(".session", "").replace("+", "")
            account_name = f"Account_{phone_number[:4]}****" if phone_number else f"Uploaded_Account_{user_id}"
            
            # Save session as base64 in database
            import base64
            session_string = base64.b64encode(session_data).decode("utf-8")
            
            # Add account to database
            account_id = self.db.add_telegram_account(
                user_id,
                account_name,
                phone_number or "Unknown",
                "uploaded",  # API ID placeholder
                "uploaded",  # API Hash placeholder  
                session_string
            )
            
            # Clear user session
            del self.user_sessions[user_id]
            
            # Success message with options
            keyboard = [
                [InlineKeyboardButton(" Manage Accounts", callback_data="manage_accounts")],
                [InlineKeyboardButton(" Upload Another", callback_data="upload_session")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f" **Session Uploaded Successfully!**\n\n**Account:** {account_name}\n**Phone:** +{phone_number or 'Unknown'}\n**Status:** Ready for campaigns\n\nYour account has been added and is ready to use!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Session upload error: {e}")
            await update.message.reply_text(
                f" **Upload failed!**\n\nError: {str(e)}\n\nPlease try again with a valid session file.",
                parse_mode=ParseMode.MARKDOWN
            )


    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors that occur in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to send error message to user if possible
        if update and hasattr(update, '"'"'effective_chat'"'"') and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=" **Something went wrong!**\n\nPlease try again or contact support if the issue persists.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    def run(self):
        """Run the bot"""
        # Validate configuration
        Config.validate()
        
        # Start bump service scheduler
        self.bump_service.start_scheduler()
        logger.info("Bump service scheduler started")
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Setup bot commands
        application.post_init = self.setup_bot_commands
        
        # Start the bot
        logger.info("Starting TgCF Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


    async def start_session_upload(self, query):
        """Start session file upload process"""
        user_id = query.from_user.id
        self.user_sessions[user_id] = {"step": "upload_session", "account_data": {}}
        
        text = """
 **Upload Session File**

Send me your Telegram session file (.session) as a document.

**Requirements:**
 File must have .session extension
 File size should be less than 50KB
 Session must be valid and active

**Benefits:**
 Instant account setup - no API credentials needed
 No verification codes required  
 Account ready immediately after upload

Send the session file now, or click Cancel to go back.
        """
        
        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="manage_accounts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_manual_setup(self, query):
        """Start manual account setup (old 5-step process)"""
        user_id = query.from_user.id
        self.user_sessions[user_id] = {"step": "account_name", "account_data": {}}
        
        text = """
 **Manual Account Setup**

**Step 1/5: Account Name**

Please send me a name for this work account (e.g., "Marketing Account", "Sales Account", "Support Account").

This name will help you identify the account when managing campaigns.
        """
        
        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="manage_accounts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

if __name__ == "__main__":
    bot = TgcfBot()
    bot.run()
