import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Professional Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Dependency Check ---
try:
    from card_validator import Luhn
    from telegram import Update, constants
    from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
except ImportError as e:
    logger.error(f"Required library missing: {e}")
    sys.exit(1)

# --- Configuration ---
class Config:
    TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")

class CardProcessor:
    @staticmethod
    def validate(text: str):
        clean_num = "".join(filter(str.isdigit, text))
        if 13 <= len(clean_num) <= 19:
            is_valid = Luhn.is_valid(clean_num)
            # Basic Issuer Detection
            brands = {"4": "VISA", "5": "MASTERCARD", "3": "AMEX", "6": "DISCOVER"}
            issuer = brands.get(clean_num[0], "UNKNOWN")
            return is_valid, clean_num, issuer
        return False, None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **Validator Active**\nSend card details to check.", parse_mode=constants.ParseMode.MARKDOWN)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_valid, num, issuer = CardProcessor.validate(update.message.text)
    
    if is_valid:
        report = f"✅ **Valid Card**\n━━━━━━━━━━━━━━\n**Issuer:** {issuer}\n**Number:** `{num}`"
        try:
            await context.bot.send_message(chat_id=Config.CHANNEL_ID, text=report, parse_mode=constants.ParseMode.MARKDOWN)
            await update.message.reply_text("✅ Forwarded to channel.")
        except Exception as e:
            logger.error(f"Send error: {e}")
    elif num: # Only reply if it actually looked like a card number
        await update.message.reply_text("❌ Invalid Checksum.")

if __name__ == "__main__":
    if not Config.TOKEN or not Config.CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID is missing!")
        sys.exit(1)
        
    app = ApplicationBuilder().token(Config.TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logger.info("Bot is running...")
    app.run_polling()
