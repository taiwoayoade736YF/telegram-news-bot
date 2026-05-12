# debug_playwright.py
from playwright.sync_api import sync_playwright
import time


def debug_page(url: str):
    print(f"🔍 Inspecting: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(3000)  # Let JS finish

        # 🎯 Try common selectors and report what's found
        selectors = [
            'article',
            '.story',
            '.post',
            '.news-item',
            '.gs-c-promo-body',  # BBC
            '.ArticleHeader',  # Reuters
            '.athing',  # Hacker News
            '[itemtype*="NewsArticle"]',
            'div[class*="article"]',
            'section[class*="story"]'
        ]

        print(f"\n📊 Selector results for {url}:")
        for sel in selectors:
            try:
                count = page.locator(sel).count()
                if count > 0:
                    print(f"  ✅ {sel}: {count} elements found")
                    # Show first element's HTML snippet
                    first = page.locator(sel).first
                    if first.count() > 0:
                        html = first.evaluate('el => el.outerHTML')
                        print(f"     Sample: {html[:200]}...")
                else:
                    print(f"  ❌ {sel}: 0 elements")
            except Exception as e:
                print(f"  ⚠️ {sel}: Error - {e}")

        # 📝 Also show first 10 h2/h3 headings (likely titles)
        headings = page.query_selector_all('h2, h3')
        print(f"\n📝 First 10 headings:")
        for i, h in enumerate(headings[:10], 1):
            text = h.text_content().strip()[:80]
            print(f"  {i}. {text}")

        browser.close()


if __name__ == "__main__":
    # Test your target sites
    #debug_page("https://www.reuters.com")
    # debug_page("https://www.bbc.com/news")
     debug_page("https://news.ycombinator.com")