import os
import logging
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Setup logging
logging.basicConfig(level=logging.INFO)

# These pull values from GitHub Secrets
# If they are missing, the bot stops immediately for security
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("CHANNEL_ID")

async def handle_msg(update: Update, context):
    if not update.message or not update.message.text:
        return
    
    # Simple validation logic
    text = update.message.text
    if len(text) > 13: # Logic simplified for demonstration
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            text=f"Card Received: `{text}`", 
            parse_mode=constants.ParseMode.MARKDOWN
        )

if __name__ == "__main__":
    if not TOKEN or not GROUP_ID:
        print("Error: Secrets are not loaded!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT, handle_msg))
        app.run_polling()
