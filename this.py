import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time

visited_urls = set()


def same_domain(url1, url2):
    return urlparse(url1).netloc == urlparse(url2).netloc


def normalize_url(url):
    url, _ = urldefrag(url)  # Remove #fragment
    return url.rstrip('/')  # Remove trailing slash for consistency


def crawl(url, depth=1, domain=None):
    if depth == 0 or url in visited_urls:
        return

    url = normalize_url(url)

    if domain is None:
        domain = urlparse(url).netloc

    if not same_domain(url, f"https://{domain}"):
        return

    print(f"Crawling: {url}")
    visited_urls.add(url)

    try:
        response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})

        if "text/html" not in response.headers.get("Content-Type", ""):
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            next_url = urljoin(url, link.get('href'))
            next_url = normalize_url(next_url)

            print(f"  → Found: {next_url}")

            if next_url not in visited_urls and same_domain(url, next_url):
                time.sleep(0.5)  # Be polite: rate limiting
                crawl(next_url, depth - 1, domain)

    except Exception as e:
        print(f"Failed to crawl {url}: {e}")


if __name__ == "__main__":
    start_url = 'https://fqluxury.org'
    crawl(start_url, depth=1)