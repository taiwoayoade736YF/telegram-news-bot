# new_bot.py - Complete working bot with /latestnews command
import json
import logging
import os
import re
import asyncio
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.request import HTTPXRequest

# ✅ Import your scraper function from PPY.py
from PPY import scrape_hackernews

import sys
import os

# Render runs in headless mode - ensure Playwright works
if os.getenv("RENDER"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/.cache/ms-playwright"

# 📝 Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🌐 Global variables
GENRE_COMMAND_MAP = {}
executor = ThreadPoolExecutor(max_workers=1)
scraping_lock = asyncio.Lock()

# 📥 Load JSON database
JSON_PATH = Path(__file__).parent / "PPY.json"
logger.info(f"🔍 Loading news from: {JSON_PATH.absolute()}")

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        NEWS_DATABASE = json.load(f)
    logger.info(f"✅ Loaded {sum(len(v) for v in NEWS_DATABASE.values())} articles")
except Exception as e:
    logger.critical(f"❌ Failed to load news: {e}")
    NEWS_DATABASE = {}


def safe_command_name(genre: str) -> str:
    """Convert genre to valid Telegram command (lowercase, alphanumeric, max 32 chars)"""
    clean = re.sub(r'[^a-z0-9_]', '_', genre.lower().strip().replace(' ', '_'))
    return clean[:32] or 'general'


def format_news_message(genre: str, news_list: list, max_items: int = 5) -> str:
    """Formats news articles into a Telegram message with HTML"""
    msg = f"📰 <b>Latest {genre.capitalize()} News:</b>\n\n"
    for i, item in enumerate(news_list[:max_items], 1):
        title = item.get('title', 'No title')
        summary = item.get('summary', 'No summary')
        url = item.get('url', '#')
        msg += f"{i}. <b>{title}</b>\n   {summary}\n   🔗 <a href='{url}'>Read more</a>\n\n"
    return msg + " Type /news [genre] for more."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1️⃣ Message with INLINE genre buttons
    genre_buttons = [[InlineKeyboardButton(g.capitalize(), callback_data=g)] for g in NEWS_DATABASE.keys()]
    await update.message.reply_text(
        "👋 *Welcome! Tap a genre below:*\n\n💡 *No typing required!*",
        reply_markup=InlineKeyboardMarkup(genre_buttons),
        parse_mode="Markdown"
    )

    # 2️⃣ Separate message that brings up the PERSISTENT keyboard
    await update.message.reply_text(
        "🔘 *Main commands are ready below 👇*",
        reply_markup=get_clickable_commands_keyboard(),
        parse_mode="Markdown"
    )


async def show_news_by_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks"""
    query = update.callback_query
    await query.answer()
    genre = query.data.lower()
    news_list = NEWS_DATABASE.get(genre, [])
    if not news_list:
        await query.edit_message_text(f"❌ No news for {genre}")
        return
    await query.edit_message_text(
        format_news_message(genre, news_list),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def send_genre_news(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str):
    """Reusable handler for any genre command like /tech, /sports, etc."""
    news_list = NEWS_DATABASE.get(genre, [])
    if not news_list:
        await update.message.reply_text(f"❌ No news found for {genre.capitalize()}.")
        return
    await update.message.reply_text(
        format_news_message(genre, news_list),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows commands as clickable buttons"""
    msg = "📖 *Available Commands:*\n\n"
    msg += "🔘 *Tap any button below to run it instantly!*\n\n"
    msg += "• `/start` - Welcome menu\n"
    msg += "• `/latestnews` - 🔄 Scrape fresh news now\n"
    msg += "• `/news <genre>` - Fetch by genre name\n"
    msg += "• `/tech`, `/world`, etc. - Direct genre news\n\n"
    msg += "💡 *No typing needed! Just tap.*"

    await update.message.reply_text(
        msg,
        reply_markup=get_clickable_commands_keyboard(),  # 👈 ATTACHES THE BUTTONS
        parse_mode="Markdown"
    )


async def latestnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Scrape fresh news on-demand and update the bot's database"""
    async with scraping_lock:
        status_msg = await update.message.reply_text(
            "🔄 Scraping latest news from Hacker News... (please wait ~30 seconds)")

        try:
            # ⏱️ Run scraper with explicit timeout
            loop = asyncio.get_event_loop()
            fresh_articles = await asyncio.wait_for(
                loop.run_in_executor(executor, lambda: scrape_hackernews(max_articles=15)),
                timeout=50.0  # Fails cleanly after 50s instead of crashing
            )

            if not fresh_articles:
                await status_msg.edit_text("❌ Failed to fetch fresh news. Try again later.")
                return

            # 3️⃣ Group by genre
            fresh_database = defaultdict(list)
            for article in fresh_articles:
                genre = article.pop('genre', 'general')
                fresh_database[genre].append(article)
            fresh_database = dict(fresh_database)

            # 4️⃣ Save to JSON
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(fresh_database, f, ensure_ascii=False, indent=2)

            # 5️⃣ Update in-memory database
            global NEWS_DATABASE, GENRE_COMMAND_MAP
            NEWS_DATABASE = fresh_database
            GENRE_COMMAND_MAP = {safe_command_name(g): g for g in NEWS_DATABASE.keys()}

            # 6️⃣ Send confirmation
            genres = list(fresh_database.keys())
            first_genre = genres[0] if genres else "general"

            await status_msg.edit_text(
                f"✅ Fresh news scraped! Found {sum(len(v) for v in fresh_database.values())} articles across {len(genres)} genres.\n\n"
                f"📊 Genres: {', '.join(genres)}\n\n"
                f"💡 Try: /{safe_command_name(first_genre)} or /start to browse"
            )

        except asyncio.TimeoutError:
            await status_msg.edit_text("⏱️ Scraping timed out. The site might be slow. Try again in a minute.")
        except Exception as e:
            logger.error(f"❌ Error in /latestnews: {e}")
            await status_msg.edit_text(f"⚠️ Error scraping news: {str(e)[:150]}")





# ... rest of your main() function ...


# ... (your existing help_command, latestnews_command, etc.) ...

async def handle_command_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts command button taps and executes them instantly"""
    text = update.message.text.strip()

    # Map button text to actual handler functions
    command_map = {
        "/start": start,
        "/help": help_command,
        "/latestnews": latestnews_command,
    }

    # Check if it's a genre command like /tech
    if text.startswith("/") and text not in command_map:
        genre = text[1:].lower()  # Remove "/"
        if genre in NEWS_DATABASE:
            await send_genre_news(update, context, genre)
            return

    # Execute mapped command
    if text in command_map:
        await command_map[text](update, context)
        return

    # Fallback: let Telegram handle it normally
    await update.message.reply_text(f"✅ Received: {text}")


from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_clickable_commands_keyboard() -> ReplyKeyboardMarkup:
    """Creates a tap-to-send command menu"""
    # Get genre commands dynamically
    genres = [f"/{safe_command_name(g)}" for g in NEWS_DATABASE.keys()]

    # Split genres into rows of 2 for clean mobile layout
    genre_rows = [genres[i:i + 2] for i in range(0, len(genres), 2)]

    keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/help")],
        [KeyboardButton("/latestnews")],
        *genre_rows  # Adds genre buttons dynamically
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Fits screen nicely
        one_time_keyboard=False,  # Stays visible after tap
        input_field_placeholder="👇 Tap a command to run it"
    )


def main():
    import traceback  # ← For error logging

    try:  # ← ✅ START OF TRY BLOCK
        # 🔐 TOKEN SETUP
        from dotenv import load_dotenv
        import os
        from telegram.request import HTTPXRequest
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, Update, ContextTypes

        load_dotenv()
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

        # Simple validation
        if not TOKEN or len(TOKEN) < 40 or ":" not in TOKEN:
            print(f"❌ Invalid token: '{TOKEN}'")
            raise ValueError("⚠️ Bot token is invalid! Check for typos or extra spaces.")

        logger.info(f"🔐 Bot token loaded (length: {len(TOKEN)}, ends with ...{TOKEN[-6:]})")

        # ⚙️ Dynamic timeout
        timeout = 120 if os.getenv("RENDER") else 60

        # 🌐 Configure HTTP request
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=timeout,
            write_timeout=timeout,
            pool_timeout=30.0
        )

        # 🤖 Create Application
        app = Application.builder().token(TOKEN).request(request).build()

        # ✅ Register handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("news", news_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("latestnews", latestnews_command))

        # 🚀 Genre commands
        for genre in NEWS_DATABASE.keys():
            cmd_name = safe_command_name(genre)
            app.add_handler(CommandHandler(
                cmd_name,
                lambda update, context, g=genre: send_genre_news(update, context, g)
            ))

        # ✅ Inline button handler
        app.add_handler(CallbackQueryHandler(show_news_by_callback))

        # 🛡️ Error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"❌ Update {update} caused error: {context.error}")

        app.add_error_handler(error_handler)

        # 🔄 Auto-refresh for Render
        if os.getenv("RENDER"):
            async def auto_refresh(context: ContextTypes.DEFAULT_TYPE):
                logger.info("🔄 Auto-refreshing news...")
                try:
                    from PPY import scrape_hackernews
                    fresh = scrape_hackernews(max_articles=10)
                    from collections import defaultdict
                    import json
                    from pathlib import Path
                    fresh_db = defaultdict(list)
                    for a in fresh:
                        genre = a.pop('genre', 'general')
                        fresh_db[genre].append(a)
                    with open(Path(__file__).parent / "PPY.json", "w", encoding="utf-8") as f:
                        json.dump(dict(fresh_db), f, ensure_ascii=False, indent=2)
                    logger.info(f"✅ Auto-refreshed {len(fresh)} articles")
                except Exception as e:
                    logger.error(f"❌ Auto-refresh failed: {e}")

            app.job_queue.run_repeating(auto_refresh, interval=3600, first=300)

        # 🚀 Start polling (CORRECT INDENTATION)
        logger.info("✅ Bot is running. Press Ctrl+C to stop.")
        logger.info(f"📊 Available genres: {list(NEWS_DATABASE.keys())}")
        app.run_polling(
            poll_interval=2,
            timeout=timeout,
            allowed_updates=None
        )

    except Exception as e:  # ← ✅ EXCEPT MATCHES THE TRY ABOVE
        # 🔴 CATCH AND PRINT ALL ERRORS
        print(f"\n❌ CRASH: {type(e).__name__}: {e}")
        print("🔍 Full traceback:")
        traceback.print_exc()
        print("\n")
        raise  # Re-raise so Render sees it failed

from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_command_keyboard() -> ReplyKeyboardMarkup:
    """Creates a clickable keyboard with all bot commands"""
    # Organize commands in rows for better UX
    keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/help")],
        [KeyboardButton("/latestnews")],  # Important command gets its own row
        [KeyboardButton(f"/{safe_command_name(g)}") for g in list(NEWS_DATABASE.keys())[:4]]  # Top 4 genres
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Makes buttons fit screen
        one_time_keyboard=False,  # Keeps keyboard visible after use
        input_field_placeholder="Tap a command 👇"  # Hint text
    )

if __name__ == "__main__":
    main()