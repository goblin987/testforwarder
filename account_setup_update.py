# Update the start_add_account method to prioritize session upload

# Find and replace the account setup text
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Step 1/5 text with new session-first approach
content = content.replace('**Step 1/5: Account Name**', '**Choose Your Setup Method:**')

content = content.replace(
    'Please send me a name for this work account (e.g., "Marketing Account", "Sales Account", "Support Account").\n\nThis name will help you identify the account when managing campaigns.',
    ' **Recommended:** Upload session file for instant setup\n **Alternative:** Manual setup with API credentials\n\n**Session Upload Benefits:**\n Instant account setup - no API credentials needed\n No verification codes required\n Account ready immediately\n\nChoose your preferred method below:'
)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated account setup text")
