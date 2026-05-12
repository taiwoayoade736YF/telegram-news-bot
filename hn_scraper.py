# hn_scraper.py - Works 100% with Hacker News
from playwright.sync_api import sync_playwright
import json
import re
from pathlib import Path
from collections import defaultdict

# 🎯 Genre keywords (Hacker News is mostly tech, but we'll classify anyway)
GENRE_KEYWORDS = {
    "tech": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "startup", "coding",
             "cybersecurity", "internet", "computer", "python", "javascript", "linux", "open source"],
    "business": ["startup", "funding", "venture", "ipo", "acquisition", "company", "ceo", "investment"],
    "science": ["research", "study", "science", "discovery", "physics", "biology", "space", "nasa"],
    "world": ["politics", "government", "election", "policy", "regulation", "law", "privacy"],
}


def classify_genre(text: str) -> str:
    if not text:
        return "tech"  # HN is mostly tech by default
    text_lower = text.lower()
    scores = {genre: sum(1 for kw in keywords if kw in text_lower)
              for genre, keywords in GENRE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "tech"


def scrape_hackernews(max_articles: int = 20):
    """Scrapes Hacker News - simplified and debug-friendly"""
    url = "https://news.ycombinator.com"
    articles = []

    print(f"🌐 Scraping Hacker News: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate and wait
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_selector('tr.athing', timeout=10000)

        # ✅ Get all article rows
        rows = page.query_selector_all('tr.athing')
        print(f"✅ Found {len(rows)} article rows")

        for i, row in enumerate(rows[:max_articles]):
            try:
                # 🔍 Extract title using query_selector (more reliable in loops)
                title_el = row.query_selector('a.storylink')
                if not title_el:
                    print(f"  ⚠️ Row {i + 1}: No storylink found")
                    continue

                title = title_el.text_content().strip()
                href = title_el.get_attribute('href')

                if not title or len(title) < 3:
                    print(f"  ⚠️ Row {i + 1}: Empty title")
                    continue

                # Clean URLs (HN uses relative and absolute)
                if href:
                    if href.startswith('item?id='):
                        href = f"https://news.ycombinator.com/{href}"
                    elif href.startswith('//'):
                        href = f"https:{href}"
                    elif not href.startswith('http'):
                        href = f"https://{href}"

                if not href:
                    print(f"  ⚠️ Row {i + 1}: No URL found")
                    continue

                # HN doesn't show summaries on front page
                summary = title[:200]
                genre = classify_genre(title)

                articles.append({
                    "title": re.sub(r'\s+', ' ', title)[:150],
                    "summary": re.sub(r'\s+', ' ', summary)[:200],
                    "url": href,
                    "image": None,
                    "genre": genre,
                    "source": "Hacker News"
                })

                print(f"  ✅ Row {i + 1}: {title[:50]}...")

            except Exception as e:
                print(f"  ❌ Row {i + 1} error: {e}")
                continue

        browser.close()

    return articles


def main():
    # Scrape Hacker News
    articles = scrape_hackernews(max_articles=20)

    if not articles:
        print("❌ No articles scraped. Check your Playwright installation.")
        return

    # 🗂️ Group by genre for bot compatibility
    news_database = defaultdict(list)
    for article in articles:
        genre = article.pop('genre')
        news_database[genre].append(article)

    # 💾 Save to JSON (same format your bot expects)
    output_file = Path("hn_news.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dict(news_database), f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {sum(len(v) for v in news_database.values())} articles to {output_file}")
    print(f"📊 Genres: {sorted(news_database.keys())}")

    # 🔍 Quick preview
    print("\n🎯 Sample articles:")
    for genre, items in list(news_database.items())[:4]:
        print(f"\n{genre.upper()} ({len(items)}):")
        for item in items[:3]:
            print(f"  • {item['title'][:70]}...")


if __name__ == "__main__":
    main()