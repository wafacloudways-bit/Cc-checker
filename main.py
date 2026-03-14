import os
import logging
import sys
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config: Using environment variables for security
TOKEN = os.getenv("8693796900:AAHqD_NvImjissaeBY0QfWYsw1XmiiGbDXs")
GROUP_ID = os.getenv("-5100702051") 

class CardProcessor:
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        digits = [int(d) for d in card_number]
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9: digits[i] -= 9
        return sum(digits) % 10 == 0

    @classmethod
    def process(cls, text: str):
        clean_num = "".join(filter(str.isdigit, text))
        if 13 <= len(clean_num) <= 19:
            is_valid = cls.luhn_check(clean_num)
            issuer = "VISA" if clean_num.startswith('4') else "MC" if clean_num.startswith('5') else "OTHER"
            return is_valid, clean_num, issuer
        return False, None, None

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    is_valid, num, issuer = CardProcessor.process(update.message.text)
    
    if is_valid:
        report = f"✅ **Valid Card**\n**Issuer:** {issuer}\n**Number:** `{num}`"
        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=report, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Post Error: {e}")
            await update.message.reply_text("⚠️ Failed to post. Ensure I am an Admin in this group.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling()
