with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace Step 1/5 with session upload priority
content = content.replace("**Step 1/5: Account Name**", "**Fast Session Upload Method**")

# Replace the instruction text
old_text = "Please send me a name for this work account (e.g., \"Marketing Account\", \"Sales Account\", \"Support Account\").\n\nThis name will help you identify the account when managing campaigns."
new_text = " **Upload your .session file for instant account setup**\n\n**Benefits:**\n No API credentials needed\n No verification codes\n Account ready immediately\n\nSend your .session file as a document, or use manual setup below:"

content = content.replace(old_text, new_text)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated bot to prioritize session upload")

