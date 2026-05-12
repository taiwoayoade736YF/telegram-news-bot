# debug_hn_structure.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://news.ycombinator.com", wait_until='networkidle')

    # Get first article row
    first_row = page.query_selector('tr.athing')
    if first_row:
        print("🔍 First .athing row HTML:")
        html = first_row.evaluate('el => el.outerHTML')
        print(html[:500] + "...")  # First 500 chars

        # Try different selectors
        selectors = ['a.storylink', '.title a', 'a[href*="news"]']
        print("\n🔍 Testing selectors:")
        for sel in selectors:
            el = first_row.query_selector(sel)
            if el:
                print(f"  ✅ {sel}: '{el.text_content().strip()[:50]}'")
            else:
                print(f"  ❌ {sel}: not found")

    browser.close()