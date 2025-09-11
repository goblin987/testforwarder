# Session Upload Feature for TgCF Bot
# Add this to bot.py to enable session file uploads

# 1. Add document handler to __init__ method:
# self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

# 2. Add callback handler for upload_session:
# elif callback_data == \"upload_session\":
#     await self.start_session_upload(query)

# 3. Add these methods to TgcfBot class:

async def start_session_upload(self, query):
    user_id = query.from_user.id
    self.user_sessions[user_id] = {'step': 'upload_session', 'account_data': {}}
    
    text = '''
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
    '''
    
    keyboard = [[InlineKeyboardButton(\" Cancel\", callback_data=\"manage_accounts\")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in self.user_sessions or self.user_sessions[user_id].get('step') != 'upload_session':
        return
    
    document = update.message.document
    
    if not document.file_name.endswith('.session'):
        await update.message.reply_text(
            \" **Invalid file type!**\\n\\nPlease send a .session file.\",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if document.file_size > 50000:  # 50KB limit
        await update.message.reply_text(
            \" **File too large!**\\n\\nSession files should be less than 50KB.\",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Download the session file
        file = await context.bot.get_file(document.file_id)
        session_data = await file.download_as_bytearray()
        
        # Extract phone number from filename (if available)
        phone_number = document.file_name.replace('.session', '').replace('+', '')
        account_name = f\"Account_{phone_number[:4]}****\" if phone_number else f\"Uploaded_Account_{user_id}\"
        
        # Save to database (store session as base64)
        import base64
        session_string = base64.b64encode(session_data).decode('utf-8')
        
        account_id = self.db.add_telegram_account(
            user_id,
            account_name,
            phone_number or \"Unknown\",
            \"uploaded\",  # API ID placeholder
            \"uploaded\",  # API Hash placeholder  
            session_string
        )
        
        # Clear session
        del self.user_sessions[user_id]
        
        keyboard = [
            [InlineKeyboardButton(\" Manage Accounts\", callback_data=\"manage_accounts\")],
            [InlineKeyboardButton(\" Main Menu\", callback_data=\"main_menu\")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f\" **Session Uploaded Successfully!**\\n\\n**Account:** {account_name}\\n**Phone:** {phone_number or 'Unknown'}\\n\\nYour account is now ready for campaigns and forwarding!\",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text(
            f\" **Upload failed!**\\n\\nError: {str(e)}\\n\\nPlease try again with a valid session file.\",
            parse_mode=ParseMode.MARKDOWN
        )
