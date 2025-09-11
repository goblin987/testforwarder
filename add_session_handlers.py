with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add session upload handlers after the callback query handlers
insert_point = "elif callback_data == \"add_account\":\n            await self.start_add_account(query)"

session_handlers = """elif callback_data == \"upload_session\":
            await self.start_session_upload(query)
        elif callback_data == \"manual_setup\":
            await self.start_manual_setup(query)"""

content = content.replace(insert_point, insert_point + "\n        " + session_handlers)

# Add the session upload methods at the end of the class
session_methods = """
    async def start_session_upload(self, query):
        \"\"\"Start session file upload process\"\"\"
        user_id = query.from_user.id
        self.user_sessions[user_id] = {\"step\": \"upload_session\", \"account_data\": {}}
        
        text = \"\"\"
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
        \"\"\"
        
        keyboard = [[InlineKeyboardButton(\" Cancel\", callback_data=\"manage_accounts\")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_manual_setup(self, query):
        \"\"\"Start manual account setup (old 5-step process)\"\"\"
        user_id = query.from_user.id
        self.user_sessions[user_id] = {\"step\": \"account_name\", \"account_data\": {}}
        
        text = \"\"\"
 **Manual Account Setup**

**Step 1/5: Account Name**

Please send me a name for this work account (e.g., \"Marketing Account\", \"Sales Account\", \"Support Account\").

This name will help you identify the account when managing campaigns.
        \"\"\"
        
        keyboard = [[InlineKeyboardButton(\" Cancel\", callback_data=\"manage_accounts\")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
"""

# Find the end of the class and insert before the last method
content = content.replace("if __name__ == \"__main__\":", session_methods + "\nif __name__ == \"__main__\":")

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Added session upload handlers to bot")

