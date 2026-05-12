# playwright_scraper_async.py
from playwright.async_api import async_playwright  # ← Async API
import asyncio, json, re
from pathlib import Path
from collections import defaultdict


GENRE_KEYWORDS = {
    "tech": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "startup", "coding",
             "cybersecurity", "internet", "computer"],
    "sports": ["football", "basketball", "soccer", "tennis", "match", "player", "team", "championship", "league",
               "game", "win"],
    "business": ["market", "stock", "economy", "finance", "investment", "company", "earnings", "trade", "money",
                 "bank"],
    "entertainment": ["movie", "music", "celebrity", "film", "actor", "singer", "awards", "concert", "tv", "show"],
    "health": ["health", "medical", "doctor", "hospital", "vaccine", "disease", "wellness", "nutrition"],
    "world": ["war", "election", "government", "politics", "united nations", "diplomacy", "conflict", "refugee"],
}

async def scrape_with_playwright_async(url: str, max_articles: int = 10):
    print(f"🌐 Launching browser for {url}...")
    articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_selector('article', timeout=10000)

            # ... same extraction logic ...

        finally:
            await browser.close()  # ✅ Now await works!

    return articles


async def main():
    # ... same logic but with await ...
    articles = await scrape_with_playwright_async("https://www.reuters.com")
    # ...


if __name__ == "__main__":
    asyncio.run(main())  # ✅ Required for async entry point