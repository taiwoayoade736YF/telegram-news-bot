# ppt_scrap.py
import csv
from playwright.sync_api import sync_playwright


def scrape_and_save(url: str, output_file: str = "book.csv"):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate and wait for network to be idle
            print(f"🌐 Loading: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Optional: Wait for specific element if page is dynamic
            # page.wait_for_selector(".quote")  # Uncomment and adjust for your target

            # Extract data using JavaScript in browser context
            data = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('h1, p')).map(el => {
                    const text = el.innerText.trim();
                    return text ? text : null;
                }).filter(t => t); // Remove empty strings
            }''')

            # Save to CSV
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['index', 'content'])  # Header
                for i, item in enumerate(data, 1):
                    writer.writerow([i, item])

            print(f"✅ Successfully saved {len(data)} items to '{output_file}'")
            return data

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            raise
        finally:
            browser.close()


# ▶️ Run it
if __name__ == "__main__":
    scrape_and_save("https://books.toscrape.com")