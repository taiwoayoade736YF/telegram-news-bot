# playwright_scraper_sync.py
# working_scraper.py
from playwright.sync_api import sync_playwright
import json, re, time
from pathlib import Path
from collections import defaultdict

# 🎯 Your existing genre keywords
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


def classify_genre(text: str) -> str:
    if not text:
        return "general"
    text_lower = text.lower()
    scores = {genre: sum(1 for kw in keywords if kw in text_lower)
              for genre, keywords in GENRE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


# ✅ Paste the site-specific functions from Step 2 here:
# - scrape_reuters()
# - scrape_bbc()
# - scrape_hackernews()

def scrape_hackernews(max_articles: int = 20):
    """Scrapes Hacker News using the CORRECT selector: .title a"""
    url = "https://news.ycombinator.com"
    articles = []

    print(f"🌐 Scraping Hacker News: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate and wait for content
        page.goto(url, wait_until='networkidle', timeout=45000)
        page.wait_for_selector('tr.athing', timeout=15000)

        # ✅ Get all article rows
        rows = page.query_selector_all('tr.athing')
        print(f"✅ Found {len(rows)} article rows")

        for i, row in enumerate(rows[:max_articles]):
            try:
                # 🔍 CORRECT SELECTOR: .title a (not a.storylink!)
                link_el = row.query_selector('.title a')
                if not link_el:
                    continue

                title = link_el.text_content().strip()
                href = link_el.get_attribute('href')

                # Skip if no title or too short
                if not title or len(title) < 3:
                    continue

                # Clean URLs (HN uses relative, absolute, and external links)
                if href:
                    if href.startswith('item?id='):
                        # HN discussion page
                        href = f"https://news.ycombinator.com/{href}"
                    elif href.startswith('//'):
                        # Protocol-relative URL
                        href = f"https:{href}"
                    elif not href.startswith('http'):
                        # Relative URL
                        href = f"https://{href}"

                if not href:
                    continue

                # HN front page doesn't show summaries - use title as fallback
                summary = title[:200]
                genre = classify_genre(title)

                articles.append({
                    "title": re.sub(r'\s+', ' ', title)[:150],
                    "summary": re.sub(r'\s+', ' ', summary)[:200],
                    "url": href,
                    "image": None,  # HN doesn't include images in listings
                    "genre": genre,
                    "source": "Hacker News"
                })

                print(f"  ✅ #{i + 1}: {title[:60]}...")

            except Exception as e:
                print(f"  ⚠️ Row {i + 1} error: {e}")
                continue

        browser.close()

    print(f"\n📊 Successfully parsed {len(articles)} articles")
    return articles

def main():
    print("🚀 Starting news scrape...")
    all_articles = []



    print("\n🔍 Scraping Hacker News...")
    all_articles.extend(scrape_hackernews(max_articles=5))

    if not all_articles:
        print("⚠️ No articles found. Run debug_playwright.py to check selectors.")
        return

    # 🗂️ Group by genre
    news_database = defaultdict(list)
    for article in all_articles:
        genre = article.pop('genre')
        news_database[genre].append(article)

    # 💾 Save to JSON
    output = Path("PPY.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(dict(news_database), f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {sum(len(v) for v in news_database.values())} articles to {output}")
    print(f"📊 Genres: {sorted(news_database.keys())}")

    # 🔍 Preview
    print("\n🎯 Sample:")
    for genre, items in list(news_database.items())[:4]:
        print(f"\n{genre.upper()} ({len(items)}):")
        for item in items[:2]:
            print(f"  • {item['title'][:60]}...")


if __name__ == "__main__":
    main()