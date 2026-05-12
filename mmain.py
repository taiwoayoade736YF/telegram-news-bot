import os
import time
import logging
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from instagram_api import publish_post, get_recent_comments, reply_to_comment
from web_monitor import get_price, collect_public_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

def job_publish():
    publish_post("https://example.com/your-image.jpg", "Automated post ✅")

def job_monitor_prices():
    price = get_price("https://example-shop.com/product", "span.price")
    if price is not None:
        logging.info(f"💰 Current price: ${price}")
        # Add your alert logic here (email, webhook, DB, etc.)

def job_manage_comments():
    # Replace with your actual post ID or fetch latest dynamically
    post_id = os.getenv("TEST_POST_ID", "YOUR_INSTAGRAM_POST_ID")
    comments = get_recent_comments(post_id)
    for c in comments:
        if "question" in c.get("text", "").lower():
            reply_to_comment(c["id"], "Thanks! Check our bio for details. 🔗")

# Schedule tasks
schedule.every().day.at("10:00").do(job_publish)
schedule.every().hour.do(job_monitor_prices)
schedule.every(30).minutes.do(job_manage_comments)

if __name__ == "__main__":
    logging.info("🤖 Bot started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(15)