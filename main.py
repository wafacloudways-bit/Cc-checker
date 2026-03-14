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

# --- Dependency Check (Only Telegram is needed now) ---
try:
    from telegram import Update, constants
    from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
except ImportError:
    logger.error("Telegram library missing. Ensure 'python-telegram-bot' is in requirements.")
    sys.exit(1)

# --- Configuration ---
class Config:
    TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")

class CardProcessor:
    """Professional implementation of card validation without external libraries."""
    
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """Standard Luhn Algorithm implementation."""
        try:
            digits = [int(d) for d in card_number]
            # Double every second digit from the right
            for i in range(len(digits) - 2, -1, -2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            return sum(digits) % 10 == 0
        except ValueError:
            return False

    @classmethod
    def process(cls, text: str):
        # Extract digits only
        clean_num = "".join(filter(str.isdigit, text))
        
        # Validate length (Standard cards are 13-19 digits)
        if 13 <= len(clean_num) <= 19:
            is_valid = cls.luhn_check(clean_num)
            
            # Simple Issuer Detection
            brands = {"4": "VISA", "5": "MASTERCARD", "3": "AMEX", "6": "DISCOVER"}
            issuer = brands.get(clean_num[0], "UNKNOWN")
            
            return is_valid, clean_num, issuer
        return False, None, None

# --- Handler Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ **Validator System Online**\n\n"
        "Send a card number to check its integrity. Valid hits are forwarded to the channel.",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_valid, num, issuer = CardProcessor.process(update.message.text)
    
    if is_valid:
        report = (
            f"✅ **Valid Card Detected**\n"
            f"━━━━━━━━━━━━━━\n"
            f"**Issuer:** {issuer}\n"
            f"**Number:** `{num}`\n"
            f"**Status:** LUHN_PASSED"
        )
        try:
            # Forward to the Private Channel
            await context.bot.send_message(
                chat_id=Config.CHANNEL_ID, 
                text=report, 
                parse_mode=constants.ParseMode.MARKDOWN
            )
            # Notify the user
            await update.message.reply_text("✅ Verification successful. Sent to channel.")
        except Exception as e:
            logger.error(f"Forwarding Error: {e}")
            await update.message.reply_text("⚠️ Valid card, but failed to forward (Check Bot Permissions).")
    
    elif num: # If it looked like a card but failed Luhn
        await update.message.reply_text("❌ Validation Failed: Invalid Checksum.")

# --- Main Entry Point ---
if __name__ == "__main__":
    if not Config.TOKEN or not Config.CHANNEL_ID:
        logger.error("CRITICAL: BOT_TOKEN or CHANNEL_ID missing in GitHub Secrets!")
        sys.exit(1)
        
    # Build the application
    app = ApplicationBuilder().token(Config.TOKEN).build()
    
    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logger.info("Bot is running on GitHub Actions...")
    app.run_polling()
