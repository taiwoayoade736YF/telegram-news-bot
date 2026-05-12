# news_scraper.py
from typing import Any

import requests
from bs4 import BeautifulSoup, Comment
import json
import re
from urllib.parse import urljoin, urlparse

# 🎯 Genre keywords for simple classification
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
}

def classify_genre(text: str) -> str:
    """Simple keyword-based genre classification"""
    text_lower = text.lower()
    scores = {}
    for genre, keywords in GENRE_KEYWORDS.items():
        scores[genre] = sum(1 for kw in keywords if kw in text_lower)
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

def extract_news_articles(url: object, output_file: object = 'kb_data.json', max_articles: object = 15) -> dict[Any, Any]:
    """
    Extract structured news articles from a news website.
    Saves in format: {genre: [{title, summary, url, genre}, ...]}
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []
        seen_urls = set()

        # 🔍 Strategy 1: Look for common news article containers
        # Adjust selectors based on your target site's HTML structure
        candidates = (
            soup.find_all('article') +
            soup.find_all(class_=re.compile(r'post|article|news-item|entry', re.I)) +
            soup.find_all('div', {'itemtype': re.compile(r'NewsArticle', re.I)})
        )

        for container in candidates[:max_articles * 2]:  # Scan extra, filter later
            # Extract title
            title_tag = container.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|headline', re.I))
            if not title_tag:
                title_tag = container.find(['h1', 'h2', 'h3'])  # Fallback
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title or len(title) < 10:
                continue  # Skip weak titles

            # Extract link
            link_tag = container.find('a', href=True)
            if not link_tag:
                continue
            article_url = urljoin(url, link_tag['href'])
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)

            # Extract summary/description
            summary_tag = (
                container.find(class_=re.compile(r'summary|excerpt|description', re.I)) or
                container.find('p')
            )
            summary = summary_tag.get_text(strip=True) if summary_tag else title  # Fallback to title

            # Clean text
            summary = re.sub(r'\s+', ' ', summary)[:200]  # Limit length
            title = re.sub(r'\s+', ' ', title)

            # Classify genre
            genre = classify_genre(title + " " + summary)

            articles.append({
                "title": title,
                "summary": summary,
                "url": article_url,
                "genre": genre
            })

            if len(articles) >= max_articles:
                break

        # 🗂️ Group by genre for bot compatibility
        news_database = {}
        for article in articles:
            genre = article['genre']
            if genre not in news_database:
                news_database[genre] = []
            news_database[genre].append(article)

        # 💾 Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(news_database, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved {sum(len(v) for v in news_database.values())} articles across {len(news_database)} genres to '{output_file}'")
        return news_database

    except Exception as e:
        print(f"❌ Error: {e}")
        return {}


# ===== USAGE =====
