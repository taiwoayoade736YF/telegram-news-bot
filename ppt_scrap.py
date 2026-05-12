import asyncio
from pyppeteer import launch

async def scrape():
    browser = await launch(
        headless=True,
        executablePath=None,  # Let pyppeteer manage it
        args=['--no-sandbox', '--disable-setuid-sandbox'],
        # Try a known-good revision (may still break in future)
        revision='1234567'  # ← Replace with a recent valid revision
    )
    # ... rest of your code
    page = await browser.newPage()
    await page.goto('https://fqluxury.org', waitUntil='networkidle2')

    # Extract data using JavaScript inside the page
    data = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('h1, p')).map(el => el.innerText.trim())
    }''')

    print(data)
    await browser.close()


asyncio.run(scrape())