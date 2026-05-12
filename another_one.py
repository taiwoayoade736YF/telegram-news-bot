# convert_raw_to_news.py
import json
from pathlib import Path
import re

# Reuse the same genre classifier
GENRE_KEYWORDS = {...}  # Copy from above


def classify_genre(text: str) -> str: ...  # Copy from above


INPUT = Path("output.json")
OUTPUT = Path("news2_data.json")

with open(INPUT, "r", encoding="utf-8") as f:
    nodes = json.load(f)  # List of {"text": ..., "parent": ...}

# Heuristic: group consecutive text nodes into "articles"
articles = []
current = []
for node in nodes:
    text = node['text']
    parent = node['parent']

    # Start new article on headings or after long gaps
    if parent in ['h1', 'h2', 'h3'] or (current and len(text) > 100):
        if current:
            full_text = " ".join(item['text'] for item in current)
            articles.append({
                "title": current[0]['text'][:80],
                "summary": full_text[:200],
                "url": "#",  # No URL available from raw scrape
                "genre": classify_genre(full_text)
            })
        current = [node]
    else:
        current.append(node)

# Group by genre
news_database = {}
for art in articles:
    genre = art['genre']
    news_database.setdefault(genre, []).append(art)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(news_database, f, ensure_ascii=False, indent=2)

print(f"✅ Converted {len(articles)} raw nodes into {sum(len(v) for v in news_database.values())} structured articles")