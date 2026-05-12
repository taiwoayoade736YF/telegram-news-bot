# debug_news.py
import json
from pathlib import Path

file = Path("news2_data.json")
with open(file, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"📦 Type: {type(data).__name__}")
print(f"🔑 Keys: {list(data.keys())}")
print(f"🔑 Key types: {[type(k).__name__ for k in data.keys()]}")

for key in data.keys():
    print(f"\n📁 Genre: '{key}' (type: {type(key).__name__})")
    items = data[key]
    print(f"   Articles: {len(items) if isinstance(items, list) else 'NOT A LIST'}")
    if isinstance(items, list) and items:
        print(f"   Sample: {items[0]}")