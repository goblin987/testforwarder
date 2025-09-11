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
    
    async def show_main_menu(self, query):
        """Show main menu"""
        keyboard = [
            [InlineKeyboardButton("👥 Manage Accounts", callback_data="manage_accounts")],
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
                session['step'] = 'complete'
                
                # Save account
                account_id = self.db.add_telegram_account(
                    user_id,
                    session['account_data']['account_name'],
                    session['account_data']['phone_number'],
                    session['account_data']['api_id'],
                    session['account_data']['api_hash']
                )
                
                # Clear session
                del self.user_sessions[user_id]
                
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
                    "✅ **Campaign name set!**\n\n**Step 2/6: Ad Content**\n\nPlease send me the advertisement content that will be posted.\n\nYou can include:\n• Text messages\n• Emojis\n• Links\n• Formatting (bold, italic, etc.)",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'ad_content':
                session['campaign_data']['ad_content'] = message_text
                session['step'] = 'target_chats'
                
                await update.message.reply_text(
                    "✅ **Ad content set!**\n\n**Step 3/6: Target Chats**\n\nPlease send me the target chat IDs or usernames where you want to post ads.\n\n**Format:** One per line or comma-separated\n\n**Examples:**\n@channel1\n@channel2\n-1001234567890",
                    parse_mode=ParseMode.MARKDOWN
                )
            
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
        self.user_sessions[user_id] = {'step': 'account_name', 'account_data': {}}
        
        text = """
➕ **Add New Work Account**

**Fast Session Upload Method**

 **Upload your .session file for instant account setup**

**Benefits:**
 No API credentials needed
 No verification codes
 Account ready immediately

Send your .session file as a document, or use manual setup below:
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="manage_accounts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def delete_account(self, query, account_id):
        """Delete a Telegram account"""
        user_id = query.from_user.id
        account = self.db.get_account(account_id)
        
        if not account or account['user_id'] != user_id:
            await query.answer("Account not found!", show_alert=True)
            return
        
        # Delete the account
        self.db.delete_account(account_id)
        
        await query.answer("Account deleted!", show_alert=True)
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
        
        text = "📋 **My Ad Campaigns**\n\n"
        keyboard = []
        
        for campaign in campaigns:
            status = "🟢 Active" if campaign['is_active'] else "🔴 Inactive"
            text += f"**{campaign['campaign_name']}** {status}\n"
            text += f"Schedule: {campaign['schedule_type']} at {campaign['schedule_time']}\n"
            text += f"Targets: {len(campaign['target_chats'])} chats\n"
            text += f"Total Sends: {campaign['total_sends']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {campaign['campaign_name']}", callback_data=f"campaign_{campaign['id']}"),
                InlineKeyboardButton("🧪", callback_data=f"test_campaign_{campaign['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_campaign_{campaign['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Create New", callback_data="add_campaign")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Bump Service", callback_data="back_to_bump")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
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
        text = f"⚙️ **{campaign['campaign_name']}** {status}\n\n"
        text += f"**Account:** {campaign['account_name']}\n"
        text += f"**Schedule:** {campaign['schedule_type']} at {campaign['schedule_time']}\n"
        text += f"**Target Chats:** {len(campaign['target_chats'])}\n"
        text += f"**Last Run:** {campaign['last_run'] or 'Never'}\n\n"
        
        text += "**Performance:**\n"
        text += f"• Total Attempts: {performance['total_attempts']}\n"
        text += f"• Successful: {performance['successful_sends']}\n"
        text += f"• Failed: {performance['failed_sends']}\n"
        text += f"• Success Rate: {performance['success_rate']:.1f}%\n\n"
        
        text += "**Ad Content Preview:**\n"
        preview = campaign['ad_content'][:200] + "..." if len(campaign['ad_content']) > 200 else campaign['ad_content']
        text += f"`{preview}`"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Toggle Status", callback_data=f"toggle_campaign_{campaign_id}")],
            [InlineKeyboardButton("🧪 Test Campaign", callback_data=f"test_campaign_{campaign_id}")],
            [InlineKeyboardButton("📊 Full Statistics", callback_data=f"stats_{campaign_id}")],
            [InlineKeyboardButton("🔙 Back to Campaigns", callback_data="back_to_campaigns")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
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
        self.bump_service.update_campaign(campaign_id, is_active=new_status)
        
        status_text = "activated" if new_status else "deactivated"
        await query.answer(f"Campaign {status_text}!", show_alert=True)
        await self.show_campaign_details(query, campaign_id)
    
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
            text = "✅ **Custom schedule selected!**\n\n**Step 5/6: Custom Schedule**\n\nPlease send me your custom schedule.\n\n**Examples:**\n• every 4 hours\n• every 30 minutes\n• every 2 days"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_to_bump")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_account_selection(self, query, account_id):
        """Handle account selection for campaign"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or 'campaign_data' not in self.user_sessions[user_id]:
            await query.answer("Session expired! Please start again.", show_alert=True)
            await self.show_bump_service(query)
            return
        
        session = self.user_sessions[user_id]
        campaign_data = session['campaign_data']
        
        # Create the campaign
        try:
            campaign_id = self.bump_service.add_campaign(
                user_id,
                account_id,
                campaign_data['campaign_name'],
                campaign_data['ad_content'],
                campaign_data['target_chats'],
                campaign_data['schedule_type'],
                campaign_data['schedule_time']
            )
            
            # Clear session
            del self.user_sessions[user_id]
            
            account = self.db.get_account(account_id)
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Configure Campaign", callback_data=f"campaign_{campaign_id}")],
                [InlineKeyboardButton("🧪 Test Campaign", callback_data=f"test_campaign_{campaign_id}")],
                [InlineKeyboardButton("📋 My Campaigns", callback_data="my_campaigns")],
                [InlineKeyboardButton("🔙 Bump Service", callback_data="back_to_bump")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            success_text = f"""
🎉 **Campaign Created Successfully!**

**Name:** {campaign_data['campaign_name']}
**Account:** {account['account_name']}
**Schedule:** {campaign_data['schedule_type']} at {campaign_data['schedule_time']}
**Target Chats:** {len(campaign_data['target_chats'])}

Your campaign is now active and will start posting ads according to your schedule!

**Next Steps:**
• Test your campaign before it goes live
• Monitor performance in campaign details
• Adjust settings as needed
            """
            
            await query.edit_message_text(
                success_text,
                parse_mode=ParseMode.MARKDOWN,
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
