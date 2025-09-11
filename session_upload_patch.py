# This is the code to add session file upload functionality
# We'll modify the show_manage_accounts method to include session upload option

# In show_manage_accounts method, change the keyboard for no accounts:
if not accounts:
    keyboard = [
        [InlineKeyboardButton(" Add New Account", callback_data="add_account")],
        [InlineKeyboardButton(" Upload Session File", callback_data="upload_session")],
        [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
    ]

# And for existing accounts, add the upload option:
keyboard.append([InlineKeyboardButton(" Upload Session File", callback_data="upload_session")])
keyboard.append([InlineKeyboardButton(" Add New Account", callback_data="add_account")])
