import json
import logging
import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 📥 Load JSON
JSON_PATH = Path(__file__).parent / "news2yf_data_fixed.json"
logger.info(f"🔍 Loading news from: {JSON_PATH.absolute()}")

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        NEWS_DATABASE = json.load(f)
    logger.info(f"✅ Loaded {sum(len(v) for v in NEWS_DATABASE.values())} articles")
except Exception as e:
    logger.critical(f"❌ Failed to load news: {e}")
    NEWS_DATABASE = {}


def format_news_message(genre: str, news_list: list, max_items: int = 5) -> str:
    msg = f"📰 <b>Latest {genre.capitalize()} News:</b>\n\n"
    for i, item in enumerate(news_list[:max_items], 1):
        title = item.get('title', 'No title')
        summary = item.get('summary', 'No summary')
        url = item.get('url', '#')
        msg += f"{i}. <b>{title}</b>\n   {summary}\n   🔗 <a href='{url}'>Read more</a>\n\n"
    return msg + "💡 Type /news [genre] for more."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(g.capitalize(), callback_data=g)] for g in NEWS_DATABASE.keys()]
    await update.message.reply_text("👋 Choose a genre:", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_news_by_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    genre = query.data.lower()
    news_list = NEWS_DATABASE.get(genre, [])
    if not news_list:
        await query.edit_message_text(f"❌ No news for {genre}")
        return
    await query.edit_message_text(format_news_message(genre, news_list), parse_mode="HTML",
                                  disable_web_page_preview=True)


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /news [genre] command"""
    if not context.args:
        await update.message.reply_text(
            "📝 Usage: `/news <genre>`\nExample: `/news tech`\n\nType `/help` to see all available genres.",
            parse_mode="Markdown"
        )
        return

    genre = context.args[0].lower()
    if genre in NEWS_DATABASE:
        await send_genre_news(update, context, genre)
    else:
        available = ", ".join(NEWS_DATABASE.keys())
        await update.message.reply_text(f"❌ Unknown genre. Available: {available}")


import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


# ... (keep your imports, JSON loading, and format_news_message exactly as they are) ...

async def send_genre_news(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str):
    """Reusable handler for any genre command"""
    news_list = NEWS_DATABASE.get(genre, [])
    if not news_list:
        await update.message.reply_text(f"❌ No news found for {genre.capitalize()}.")
        return
    await update.message.reply_text(
        format_news_message(genre, news_list),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all available commands"""
    genres = [f"/{safe_cmd}" for safe_cmd in GENRE_COMMAND_MAP.keys()]
    msg = "📖 **Available Commands:**\n\n"
    msg += "• `/start` - Show genre buttons\n"
    msg += "• `/news <genre>` - Fetch news by genre\n"
    msg += "• " + ", ".join(genres) + " - Direct genre commands\n"
    msg += "• `/help` - Show this message"
    await update.message.reply_text(msg, parse_mode="Markdown")


def safe_command_name(genre: str) -> str:
    """Convert genre to valid Telegram command (lowercase, alphanumeric, max 32 chars)"""
    clean = re.sub(r'[^a-z0-9_]', '_', genre.lower().strip().replace(' ', '_'))
    return clean[:32] or 'general'


def main():
    # 🔐 Token setup (use your preferred method)
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        TOKEN = "8147918546:AAHvyarydPndzZZyOST05IByfkgBfBzkvlE"  # ← Replace temporarily if needed

    app = Application.builder().token(TOKEN).build()

    # 📥 Map clean command names to actual JSON keys
    global GENRE_COMMAND_MAP
    GENRE_COMMAND_MAP = {safe_command_name(g): g for g in NEWS_DATABASE.keys()}

    # ✅ Register base commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("help", help_command))

    # 🚀 DYNAMICALLY register genre commands
    for cmd, genre in GENRE_COMMAND_MAP.items():
        app.add_handler(CommandHandler(
            cmd,
            lambda update, context, g=genre: send_genre_news(update, context, g)
        ))

    app.add_handler(CallbackQueryHandler(show_news_by_callback))

    logger.info("✅ Bot is running. Press Ctrl+C to stop.")
    app.run_polling(poll_interval=2, timeout=30, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()