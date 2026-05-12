# inspect_json.py
import json
from pathlib import Path

file = Path("news2_data.json")
with open(file, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"🔑 All keys: {list(data.keys())}")
print(f"🔑 Key repr (to see hidden chars): {[repr(k) for k in data.keys()]}")

# Show first article under 'null' genre
if "null" in data or None in data:
    key = "null" if "null" in data else None
    print(f"\n📁 Articles under '{key}':")
    for i, item in enumerate(data[key][:3], 1):  # Show first 3
        print(f"{i}. {json.dumps(item, indent=2, ensure_ascii=False)}")