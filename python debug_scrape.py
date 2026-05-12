# debug_scrape.py
import requests
from bs4 import BeautifulSoup

url = 'https://www.nytimes.com'  # ← Your target URL
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

try:
    print(f"🌐 Fetching {url} ...")
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    print(f"✅ Status: {response.status_code}")
    print(f"📄 Page length: {len(response.text):,} characters")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove scripts/styles
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Count common article-like elements
    print("\n🔍 Looking for article containers:")
    selectors = [
        ('article tags', soup.find_all('article')),
        ('.post class', soup.find_all(class_='post')),
        ('.article class', soup.find_all(class_='article')),
        ('.news-item class', soup.find_all(class_='news-item')),
        ('[itemtype*=NewsArticle]', soup.find_all(itemtype=lambda x: x and 'NewsArticle' in x if x else False)),
        ('h2 headings', soup.find_all('h2')),
        ('a links', soup.find_all('a', href=True)[:10]),  # First 10 links
    ]

    for name, results in selectors:
        print(f"  • {name}: {len(results)} found")
        if results and name == 'a links':
            for i, link in enumerate(results[:3], 1):
                print(f"    {i}. {link.get_text(strip=True)[:50]} → {link.get('href', '')[:60]}")

    # Save raw HTML for inspection
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("\n💾 Saved page source to 'page_source.html' — open in browser to inspect!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()