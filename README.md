# TgCF Bot - Multi-Account Telegram Chat Forwarding Bot

A powerful Telegram bot for automated message forwarding with **multiple account support** and advanced filtering options. This bot provides an intuitive inline keyboard interface for managing multiple Telegram accounts and their forwarding configurations.

## Features

- 👥 **Multi-Account Support**: Add and manage multiple Telegram accounts
- 🤖 **Easy-to-use Bot Interface**: Complete configuration through Telegram inline keyboards
- 📨 **Message Forwarding**: Forward messages between channels, groups, and users
- 🔧 **Advanced Plugins**: Filter, format, replace, caption, watermark, and OCR plugins
- 📊 **Configuration Management**: Create, edit, and manage multiple forwarding rules per account
- 🚀 **Cloud Ready**: Deploy easily on Render or any cloud platform
- 🔒 **Secure**: User-based configuration isolation with account separation
- 🎯 **Flexible Routing**: Forward from different accounts to different or same destinations

## Quick Start

### 1. Get Telegram Credentials

1. **Create a Bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Use `/newbot` command and follow instructions
   - Save your `BOT_TOKEN`

2. **Get API Credentials:**
   - Go to [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Save your `API_ID` and `API_HASH`

### 2. Deploy on Render

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service on Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     - **Name**: `tgcf-bot`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python main.py`

3. **Set Environment Variables:**
   - `BOT_TOKEN`: Your bot token from BotFather
   - `API_ID`: Your API ID from my.telegram.org
   - `API_HASH`: Your API hash from my.telegram.org
   - `PASSWORD`: A secure password (optional, for future features)

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete

### 3. Start Using the Bot

1. **Find your bot** on Telegram using the username you created
2. **Start the bot** with `/start` command
3. **Add Telegram accounts** using "Manage Accounts"
4. **Create forwarding rules** for each account
5. **Configure plugins** and start forwarding!

## Bot Commands

- `/start` - Start the bot and show main menu
- `/help` - Show help information
- `/config` - Manage your forwarding configurations
- `/status` - Check bot status

## How to Use

### Adding Telegram Accounts

1. **Click "Manage Accounts"** in the main menu
2. **Click "Add New Account"**
3. **Enter Account Details:**
   - Account name (e.g., "Personal Account", "Work Account")
   - Phone number (with country code, e.g., +1234567890)
   - API ID (from https://my.telegram.org)
   - API Hash (from https://my.telegram.org)
4. **Account is ready** for forwarding configurations

### Creating a Forwarding Rule

1. **Click "Add New Forwarding"** in the main menu
2. **Enter Source Chat ID:**
   - For channels: `@channel_username` or `-1001234567890`
   - For groups: `-1001234567890` (get from @userinfobot)
   - For users: `@username` or `123456789`
3. **Enter Destination Chat ID** (same format as source)
4. **Give it a name** for easy identification
5. **Configure plugins** (optional)

### Getting Chat IDs

- **Channels**: Use `@channel_username` or forward a message to @userinfobot
- **Groups**: Forward any message from the group to @userinfobot
- **Users**: Use `@username` or forward a message to @userinfobot

### Available Plugins

1. **Filter Plugin**: Blacklist/whitelist messages based on text patterns
2. **Format Plugin**: Add bold, italic, code formatting to messages
3. **Replace Plugin**: Replace text using regex patterns
4. **Caption Plugin**: Add header/footer text to messages
5. **Watermark Plugin**: Add watermarks to images/videos
6. **OCR Plugin**: Extract text from images

## Configuration Examples

### Multi-Account Setup
```
Account 1: "Personal Account" (+1234567890)
Account 2: "Work Account" (+0987654321)
Account 3: "News Account" (+1122334455)
```

### Basic Forwarding
```
Account: Personal Account
Source: @source_channel
Destination: @destination_channel
Name: "News Forwarding"
```

### Multiple Account Forwarding
```
Account 1: Personal Account
Source: @personal_channel
Destination: @my_group

Account 2: Work Account  
Source: @work_channel
Destination: @work_group

Account 3: News Account
Source: @news_channel
Destination: @news_group
```

### Same Destination, Different Sources
```
Account 1: Personal Account
Source: @personal_channel
Destination: @unified_group

Account 2: Work Account
Source: @work_channel  
Destination: @unified_group
```

## Local Development

### Prerequisites
- Python 3.10+
- pip
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/your-username/tgcf-bot.git
cd tgcf-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN="your_bot_token"
export API_ID="your_api_id"
export API_HASH="your_api_hash"

# Run the bot
python main.py
```

## File Structure

```
tgcf-bot/
├── main.py              # Main application entry point
├── bot.py               # Telegram bot implementation
├── forwarder.py         # Message forwarding logic
├── plugins.py           # Plugin system
├── database.py          # Database operations
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── Procfile             # Process configuration
├── runtime.txt          # Python version
└── README.md            # This file
```

## Troubleshooting

### Common Issues

1. **"Chat not found" error:**
   - Make sure the bot is added to the source chat
   - Check if the chat ID is correct
   - Verify bot permissions in the chat

2. **"Permission denied" error:**
   - Ensure the bot has admin rights in the source chat
   - Check if the bot can send messages to the destination

3. **Messages not forwarding:**
   - Verify both source and destination chat IDs
   - Check if the forwarding rule is active
   - Look at the bot logs for error messages

### Getting Help

- Check the bot's `/help` command for quick assistance
- Review the logs in your Render dashboard
- Make sure all environment variables are set correctly

## Security Notes

- Keep your `BOT_TOKEN`, `API_ID`, and `API_HASH` secure
- Use a strong password for the web interface
- Regularly update dependencies for security patches
- Monitor bot activity and logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the original [tgcf](https://github.com/aahnik/tgcf) project
- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Uses [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram API access
