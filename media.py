import requests
import json
import os

# 🔑 CONFIG - Get your FREE key: https://mediastack.com/product
API_KEY = "your_api_key_here"  # ← REPLACE THIS!
BASE_URL = "https://gnews.io"

params = {
    "access_key": API_KEY,
    "sources": "reuters",
    "countries": "us",
    "limit": 5
}

print(f"🔍 Requesting: {BASE_URL}")
print(f"📦 Params: {params}\n")

try:
    response = requests.get(BASE_URL, params=params, timeout=10)

    # 🔎 DEBUG: Print raw response details
    print(f"📡 Status Code: {response.status_code}")
    print(f"🏷️  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
    print(f"📄 Response Preview (first 300 chars):\n{response.text[:300]}\n")

    # ✅ Only parse JSON if status is OK and content-type is JSON
    if response.status_code == 200 and "application/json" in response.headers.get("Content-Type", ""):
        data = response.json()

        # Save to file
        os.makedirs("mediastack_data", exist_ok=True)
        output_path = os.path.join("mediastack_data", "news.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        articles = data.get("data", [])
        print(f"✅ Success! Saved {len(articles)} articles to {output_path}")

        # Preview first article
        if articles:
            print(f"\n📰 First article preview:")
            print(f"   Title: {articles[0].get('title', 'N/A')[:80]}...")
            print(f"   Source: {articles[0].get('source', 'N/A')}")
    else:
        print(f"❌ API returned non-JSON response (status {response.status_code})")
        print("💡 Check: Is your API key valid? Did you exceed free tier limits?")

except requests.RequestException as e:
    print(f"❌ Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"❌ Failed to parse JSON: {e}")
    print(f"💡 Raw response was: {response.text[:200]}")