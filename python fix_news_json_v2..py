# fix_news_json_v2.py
import json
from pathlib import Path
from collections import defaultdict

INPUT = Path("news2_data.json")
OUTPUT = Path("news2yf_data_fixed.json")

# 🎯 Genre keywords for classification
GENRE_KEYWORDS = {
    "tech": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "startup", "coding", "cybersecurity", "internet", "computer", "robot", "gadget", "cloud"],
    "sports": ["football", "basketball", "soccer", "tennis", "match", "player", "team", "championship", "league", "game", "win", "score", "olympics", "cricket", "rugby"],
    "business": ["market", "stock", "economy", "finance", "investment", "company", "earnings", "trade", "money", "bank", "crypto", "inflation", "startup", "ceo", "merger"],
    "entertainment": ["movie", "music", "celebrity", "film", "actor", "singer", "awards", "concert", "tv", "show", "streaming", "netflix", "gaming", "esports", "anime"],
    "health": ["health", "medical", "doctor", "hospital", "vaccine", "disease", "wellness", "nutrition", "fitness", "mental health", "cancer", "pandemic", "research", "drug"],
    "science": ["space", "nasa", "research", "discovery", "climate", "environment", "physics", "biology", "chemistry", "experiment", "universe", "mars", "evolution"],
    "world": ["war", "election", "government", "politics", "united nations", "diplomacy", "conflict", "refugee", "sanctions", "treaty", "president", "parliament"],
    "general": []  # Fallback
}


def classify_genre(text: str) -> str:
    if not text:
        return "general"
    text_lower = text.lower()

    # Broader, more forgiving keyword sets
    GENRE_KEYWORDS = {
        "tech": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "startup", "coding",
                 "cybersecurity", "internet", "computer", "robot", "gadget", "cloud", "data", "silicon", "chip",
                 "algorithm", "tech giant", "meta", "google", "apple", "microsoft", "amazon"],
        "sports": ["football", "basketball", "soccer", "tennis", "match", "player", "team", "championship", "league",
                   "game", "win", "score", "olympics", "cricket", "rugby", "nba", "fifa", "world cup", "super bowl",
                   "baseball", "hockey", "golf", "ufc", "fighter"],
        "business": ["market", "stock", "economy", "finance", "investment", "company", "earnings", "trade", "money",
                     "bank", "crypto", "inflation", "startup", "ceo", "merger", "wall street", "dow", "s&p", "nasdaq",
                     "profit", "revenue", "layoff", "hire"],
        "entertainment": ["movie", "music", "celebrity", "film", "actor", "singer", "awards", "concert", "tv", "show",
                          "streaming", "netflix", "gaming", "esports", "anime", "oscar", "grammy", "box office",
                          "director", "album", "band", "festival"],
        "health": ["health", "medical", "doctor", "hospital", "vaccine", "disease", "wellness", "nutrition", "fitness",
                   "mental health", "cancer", "pandemic", "research", "drug", "fda", "who", "treatment", "symptom",
                   "virus", "therapy"],
        "science": ["space", "nasa", "research", "discovery", "climate", "environment", "physics", "biology",
                    "chemistry", "experiment", "universe", "mars", "evolution", "dna", "telescope", "rocket",
                    "scientist", "lab", "study", "peer-reviewed"],
        "world": ["war", "election", "government", "politics", "united nations", "diplomacy", "conflict", "refugee",
                  "sanctions", "treaty", "president", "parliament", "prime minister", "foreign", "diplomat", "summit",
                  "crisis", "border", "migration"]
    }

    scores = {genre: sum(1 for kw in keywords if kw in text_lower)
              for genre, keywords in GENRE_KEYWORDS.items()}
    best_genre = max(scores, key=scores.get)

    # Lower threshold: if at least 1 keyword matches, use it
    return best_genre if scores[best_genre] > 0 else "general"

# Load raw data
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned = defaultdict(list)

for key, value in data.items():
    # Handle invalid/missing genre keys
    if key is None or (isinstance(key, str) and key.strip().lower() in ["null", "none", ""]):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    text = item.get("title", "") + " " + item.get("summary", "")
                    genre = classify_genre(text)  # ✅ FIXED: was classify_fallback
                    cleaned[genre].append(item)
        continue

    # Skip invalid values
    if not isinstance(value, list):
        continue

    genre = key.strip().lower()
    for item in value:
        if not isinstance(item, dict):
            continue
        # Clean item
        clean_item = {k: v for k, v in item.items()
                      if isinstance(v, (str, int, float, bool)) and v is not None}
        # Ensure required fields
        clean_item.setdefault("title", "No title")
        clean_item.setdefault("summary", "No summary available")
        clean_item.setdefault("url", "#")
        cleaned[genre].append(clean_item)

# Save cleaned data
result = dict(cleaned)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✅ Fixed JSON saved to {OUTPUT}")
print(f"📊 Genres: {sorted(result.keys())}")
print(f"📰 Total articles: {sum(len(v) for v in result.values())}")