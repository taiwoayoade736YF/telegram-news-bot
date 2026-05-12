import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set of visited URLs to avoid re-crawling
visited_urls = set()


def crawl(url, depth=1):
    if depth == 0 or url in visited_urls:
        return

    print(f"Crawling: {url}")
    visited_urls.add(url)

    try:
        response = requests.get(url, timeout=5)
        # Only parse HTML content
        if "text/html" not in response.headers.get("Content-Type", ""):
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links
        for link in soup.find_all('a', href=True):
            next_url = link.get('href')
            # Normalize relative URLs
            next_url = urljoin(url, next_url)

            print(f"URL found => {next_url}")  # ← FIXED: added missing closing parenthesis
            # Recurse with reduced depth
            crawl(next_url, depth - 1)

    except Exception as e:  # ← FIXED: aligned with 'try' (same indentation level)
        print(f"Failed to crawl {url}: {e}")  # ← FIXED: indented inside except block


# Start the crawler
if __name__ == "__main__":  # ← FIXED: _name_ → __name__, _main_ → __main__
    start_url = 'https://fqluxury.org'  # Replace with target
    crawl(start_url, depth=1)