import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import time
import re

# 1. CONFIGURATION
BASE_URL = "https://mediastack.com"
OUTPUT_FOLDER = "Shadows name 'filepath' from outer media_scrape"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 2. HEADERS to mimic a real browser (avoids blocks)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 3. FETCH THE PAGE
try:
    response = requests.get(BASE_URL, headers=headers, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Failed to fetch page: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

# 4. SCRAPE TEXT CONTENT (Product Info)
print("🔍 Scraping product text...")
products = []

# Common e-commerce patterns - adjust selectors if needed
for item in soup.find_all(["div", "article"], class_=re.compile("product|item|card|watch", re.I)):
    product = {}

    # Try to find brand name
    brand = item.find(class_=re.compile("brand|maker", re.I))
    product["brand"] = brand.get_text(strip=True) if brand else "Unknown"

    # Try to find product title/model
    title = item.find(class_=re.compile("title|name|model", re.I))
    product["title"] = title.get_text(strip=True) if title else "No title"

    # Try to find price
    price = item.find(class_=re.compile("price|cost", re.I))
    product["price"] = price.get_text(strip=True) if price else "Call for price"

    if product["brand"] != "Unknown" or product["title"] != "No title":
        products.append(product)
        print(f"  ✓ Found: {product['brand']} - {product['title']} ({product['price']})")

# 5. SCRAPE & LABEL IMAGES
print("\n🖼️  Scraping and labeling images...")
os.makedirs(os.path.join(OUTPUT_FOLDER, "images"), exist_ok=True)

img_tags = soup.find_all("img")
for idx, img in enumerate(img_tags, 1):
    img_url = img.get("src") or img.get("data-src")  # Handle lazy-loaded images
    if not img_url:
        continue

    # Make URL absolute
    img_url = urllib.parse.urljoin(BASE_URL, img_url)

    # CREATE A SMART LABEL from surrounding product info
    # Strategy: look for nearest product title/brand to use as label
    label_parts = []

    # Check alt text first
    alt = img.get("alt", "").strip()
    if alt and alt.lower() not in ["", "image", "photo"]:
        label_parts.append(alt)
    else:
        # Fallback: use product info we scraped earlier
        parent = img.find_parent(["div", "article"], class_=re.compile("product|item|card", re.I))
        if parent:
            p_brand = parent.find(class_=re.compile("brand|maker", re.I))
            p_title = parent.find(class_=re.compile("title|name|model", re.I))
            if p_brand:
                label_parts.append(p_brand.get_text(strip=True))
            if p_title:
                label_parts.append(p_title.get_text(strip=True))

    # Finalize label
    if not label_parts:
        label = f"product_{idx}"
    else:
        label = " - ".join(label_parts)

    # Clean label for filename (remove bad chars)
    safe_label = re.sub(r'[<>:"/\\|?*]', "_", label)
    safe_label = safe_label[:50]  # Limit length
    filename = f"{safe_label}.jpg"
    filepath = os.path.join(OUTPUT_FOLDER, "images", filename)

    # DOWNLOAD IMAGE
    try:
        img_data = requests.get(img_url, headers=headers, timeout=10).content
        with open(filepath, "wb") as f:
            f.write(img_data)
        print(f"  ✓ Saved: {filename}")
    except Exception as e:
        print(f"  ✗ Failed to download {img_url}: {e}")

    time.sleep(0.5)  # Be polite to the server

# 6. SAVE TEXT DATA TO CSV
import csv

csv_path = os.path.join(OUTPUT_FOLDER, "products.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["brand", "title", "price"])
    writer.writeheader()
    writer.writerows(products)
print(f"\n💾 Saved {len(products)} products to {csv_path}")

import json
# 7. SAVE TO JSON
json_path = os.path.join(OUTPUT_FOLDER, "products.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=4, ensure_ascii=False)
print(f"\n💾 Saved {len(products)} products to {json_path}")