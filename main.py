import os
import logging
from dotenv import load_dotenv
from card_validator import Luhn
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management."""
    TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    LOG_LEVEL = logging.INFO

class CardProcessor:
    """Handles the logic of cleaning and validating card data."""
    @staticmethod
    def clean_input(text: str) -> str:
        return "".join(filter(str.isdigit, text))

    @staticmethod
    def validate_card(number: str) -> bool:
        return Luhn.is_valid(number)

    @staticmethod
    def get_issuer(number: str) -> str:
        prefixes = {"4": "VISA", "5": "MASTERCARD", "3": "AMEX", "6": "DISCOVER"}
        return prefixes.get(number[0], "UNKNOWN")

class TelegramBot:
    """The main Bot application class."""
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=Config.LOG_LEVEL
        )
        self.logger = logging.getLogger(__name__)

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🛡️ **Validator System Active**\n\n"
            "Submit card details below. All valid hits are logged to the secure channel.",
            parse_mode=constants.ParseMode.MARKDOWN
        )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        clean_num = CardProcessor.clean_input(update.message.text)

        # Basic filter for card-length strings
        if not (13 <= len(clean_num) <= 19):
            return

        if CardProcessor.validate_card(clean_num):
            issuer = CardProcessor.get_issuer(clean_num)
            report = (
                f"✅ **Card Validated**\n"
                f"━━━━━━━━━━━━━━\n"
                f"**Issuer:** `{issuer}`\n"
                f"**Number:** `{clean_num}`\n"
                f"**Status:** LUHN_PASSED"
            )
            try:
                await context.bot.send_message(chat_id=Config.CHANNEL_ID, text=report, parse_mode=constants.ParseMode.MARKDOWN)
                await update.message.reply_text("✨ Validated and forwarded.")
            except Exception as e:
                self.logger.error(f"Forwarding failed: {e}")
        else:
            await update.message.reply_text("❌ Invalid Checksum.")

    def run(self):
        if not Config.TOKEN:
            self.logger.error("BOT_TOKEN missing in environment!")
            return
        
        app = ApplicationBuilder().token(Config.TOKEN).build()
        app.add_handler(CommandHandler("start", self.start_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        self.logger.info("Bot is polling...")
        app.run_polling()

if __name__ == "__main__":
    TelegramBot().run()
  
