# test_bot.py - Minimal bot to verify command handling
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import os, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ Received /{context.invoked_with}!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot is alive! Try /test or /hello")

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8752478750:AAGD00YE7PTc2FtM6AmpBj-I9nTdJKvvAiM"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("hello", test_cmd))
    logger.info("🚀 Test bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()