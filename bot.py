import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config import Config
from database import Database
from plugins import PluginManager
from forwarder import MessageForwarder
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TgcfBot:
    def __init__(self):
        self.db = Database()
        self.plugin_manager = PluginManager()
        self.forwarder = MessageForwarder()
        self.user_sessions = {}  # Store user session data
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = """
🤖 **Welcome to TgCF Bot!**

The ultimate tool to automate custom telegram message forwarding with **multiple account support**.

**Features:**
• Multiple Telegram account management
• Live message forwarding
• Custom filters and plugins
• Separate forwarding per account
• Support for all message types

Use the buttons below to get started!
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
• Add multiple Telegram accounts
• Each account can have separate forwarding rules
• Forward to different or same destinations
• Manage all accounts from one bot interface

**Chat IDs:**
• For channels: Use @channel_username or channel ID
• For groups: Use group ID (get from @userinfobot)
• For users: Use @username or user ID

**Account Setup:**
• Get API credentials from https://my.telegram.org
• Each account needs its own API ID and Hash
• Phone number authentication required for each account
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
                    "✅ **Account name set!**\n\n**Step 2/5: Phone Number**\n\nPlease send me the phone number for this account (with country code, e.g., +1234567890).",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'phone_number':
                session['account_data']['phone_number'] = message_text
                session['step'] = 'api_id'
                
                await update.message.reply_text(
                    "✅ **Phone number set!**\n\n**Step 3/5: API ID**\n\nPlease send me the API ID for this account.\n\nGet it from: https://my.telegram.org",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif session['step'] == 'api_id':
                try:
                    api_id = int(message_text)
                    session['account_data']['api_id'] = str(api_id)
                    session['step'] = 'api_hash'
                    
                    await update.message.reply_text(
                        "✅ **API ID set!**\n\n**Step 4/5: API Hash**\n\nPlease send me the API Hash for this account.\n\nGet it from: https://my.telegram.org",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ **Invalid API ID!**\n\nPlease send a valid numeric API ID.",
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
                    f"🎉 **Account Added Successfully!**\n\n**Name:** {session['account_data']['account_name']}\n**Phone:** `{session['account_data']['phone_number']}`\n\nYou can now create forwarding configurations for this account!",
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
        
        text = "👥 **Manage Accounts**\n\n"
        keyboard = []
        
        for account in accounts:
            text += f"**{account['account_name']}**\n"
            text += f"Phone: `{account['phone_number']}`\n"
            text += f"Status: {'🟢 Active' if account['is_active'] else '🔴 Inactive'}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {account['account_name']}", callback_data=f"account_{account['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_account_{account['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add New Account", callback_data="add_account")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
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
➕ **Add New Telegram Account**

**Step 1/5: Account Name**

Please send me a name for this account (e.g., "My Personal Account", "Work Account").

This name will help you identify the account in the bot interface.
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
    
    async def setup_bot_commands(self, application):
        """Setup bot commands"""
        commands = [
            BotCommand("start", "Start the bot and show main menu"),
            BotCommand("help", "Show help information"),
            BotCommand("config", "Manage forwarding configurations"),
            BotCommand("status", "Check bot status")
        ]
        await application.bot.set_my_commands(commands)
    
    def run(self):
        """Run the bot"""
        # Validate configuration
        Config.validate()
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Setup bot commands
        application.post_init = self.setup_bot_commands
        
        # Start the bot
        logger.info("Starting TgCF Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TgcfBot()
    bot.run()
