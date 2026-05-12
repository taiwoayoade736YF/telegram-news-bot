# news_scraper_newspaper.py
import newspaper
import pandas as pd
import json
import re
from pathlib import Path
from collections import defaultdict
import time

# 🎯 Genre keywords for classification
GENRE_KEYWORDS = {
    "tech": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "startup", "coding",
             "cybersecurity", "internet", "computer", "robot", "gadget", "cloud", "data", "silicon", "chip",
             "algorithm", "meta", "google", "apple", "microsoft", "amazon"],
    "sports": ["football", "basketball", "soccer", "tennis", "match", "player", "team", "championship", "league",
               "game", "win", "score", "olympics", "cricket", "rugby", "nba", "fifa", "world cup", "super bowl",
               "baseball", "hockey", "golf"],
    "business": ["market", "stock", "economy", "finance", "investment", "company", "earnings", "trade", "money", "bank",
                 "crypto", "inflation", "startup", "ceo", "merger", "wall street", "dow", "s&p", "nasdaq", "profit",
                 "revenue"],
    "entertainment": ["movie", "music", "celebrity", "film", "actor", "singer", "awards", "concert", "tv", "show",
                      "streaming", "netflix", "gaming", "esports", "anime", "oscar", "grammy", "box office", "director",
                      "album"],
    "health": ["health", "medical", "doctor", "hospital", "vaccine", "disease", "wellness", "nutrition", "fitness",
               "mental health", "cancer", "pandemic", "research", "drug", "fda", "who", "treatment", "symptom"],
    "science": ["space", "nasa", "research", "discovery", "climate", "environment", "physics", "biology", "chemistry",
                "experiment", "universe", "mars", "evolution", "dna", "telescope", "rocket", "scientist"],
    "world": ["war", "election", "government", "politics", "united nations", "diplomacy", "conflict", "refugee",
              "sanctions", "treaty", "president", "parliament", "prime minister", "foreign", "crisis", "border"],
    "gaming": ["game", "gaming", "esports", "playstation", "xbox", "nintendo", "steam", "epic", "twitch", "video game",
               "console", "pc gaming", "mobile game"]
}


def get_stealth_config():
    """Returns a newspaper Config with stealth headers"""
    from newspaper import Config
    cfg = Config()
    cfg.request_timeout = 15
    cfg.memoize_articles = False
    cfg.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    cfg.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    return cfg


def classify_genre(title: str, text: str) -> str:
    """Classifies article into genre based on keyword matching"""
    combined = f"{title} {text[:300]}".lower()
    scores = {genre: sum(1 for kw in keywords if kw in combined)
              for genre, keywords in GENRE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def clean_text(text: str, max_length: int = 200) -> str:
    """Cleans and truncates text for bot messages"""
    if not text:
        return "No summary available"
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned[:max_length] + "..." if len(cleaned) > max_length else cleaned


# 🌐 Define your news sources (BBC works; GameSpot may block)
sources_config = [
    {"url": "https://news.ycombinator.com", "name": "NYT", "memoize": False},
    {"url": "https://www.reuters.com", "name": "reuter", "memoize": False},  # Gaming alternative
]

# Build newspaper sources with stealth config
sources = []
cfg = get_stealth_config()

for config in sources_config:
    print(f"🔍 Building source: {config['name']}...")
    try:
        source = newspaper.build(config["url"], config=cfg)
        sources.append(source)
        print(f"✅ {config['name']} built successfully ({len(source.articles)} articles found)")
    except Exception as e:
        print(f"❌ Failed to build {config['name']}: {e}")
        continue

if not sources:
    print("⚠️ No sources built successfully. Exiting.")
    exit(1)

# ⏳ Safe sequential download with timeout (prevents hanging)
print("⏳ Downloading articles (this may take 1-2 mins)...")
for source in sources:
    # Limit to first 15 to avoid long waits
    for article in source.articles[:15]:
        try:
            article.download(timeout=10)
        except Exception:
            pass  # Silently skip failed downloads
print("✅ Articles downloaded to memory")

# 📊 Collect articles
articles_list = []
limit_per_source = 10

for source in sources:
    print(f"📥 Processing {source.url}...")
    count = 0
    for article in source.articles:
        if count >= limit_per_source:
            break
        try:
            if not article.is_downloaded:
                article.download(timeout=10)
            article.parse()
            # ... rest of your processing code ...

            title = article.title or "No title"
            text = article.text or ""
            url = article.url
            source_name = source.domain

            # Classify genre
            genre = classify_genre(title, text)

            # Clean summary for bot
            summary = clean_text(text)

            articles_list.append({
                "title": title,
                "summary": summary,
                "url": url,
                "genre": genre,
                "source": source_name,
                "published": article.publish_date.isoformat() if article.publish_date else None
            })

            count += 1
            if count % 5 == 0:
                print(f"  ✓ Processed {count} articles...")

        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                print(f"  ⚠️ 403 Blocked: {article.url[:60]}... (skipping)")
            else:
                print(f"  ⚠️ Skipped article: {e}")
            continue

    print(f"✅ Finished {source.domain}: {count} articles")

# 🗂️ Group by genre for bot compatibility
news_database = defaultdict(list)
for art in articles_list:
    genre = art.pop("genre")
    news_database[genre].append(art)

# 💾 Save to CSV
if articles_list:
    df = pd.DataFrame(articles_list)
    df.to_csv("my_scraped_articles.csv", index=False, encoding="utf-8")
    print(f"📄 Saved CSV: my_scraped_articles.csv ({len(df)} rows)")

# 💾 Save to JSON for bot ✅
output_json = Path("news_data_bot.json")  # ← Fixed filename
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(dict(news_database), f, ensure_ascii=False, indent=2)

print(f"✅ Saved JSON for bot: {output_json}")
print(f"📊 Genres: {sorted(news_database.keys())}")
print(f"📰 Total articles: {sum(len(v) for v in news_database.values())}")

# 🔍 Quick preview
if news_database:
    print("\n🎯 Sample articles per genre:")
    for genre, items in list(news_database.items())[:4]:
        print(f"\n{genre.upper()} ({len(items)}):")
        for item in items[:2]:
            print(f"  • {item['title'][:60]}...")