#!/usr/bin/env python3
# program: spider.py
# author: YF
# version: 3.0
# date: April 2026
# description: Crawls a website, extracts page content, and exports to TXT/CSV/JSON.

import sys
import re
import csv
import json
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser


def log_stdout(msg):
    """Print msg to the screen."""
    print(msg)


def get_page(page_url, log):
    """Retrieve URL and return contents, log errors."""
    try:
        response = urllib.request.urlopen(page_url)
        body = response.read().decode('utf-8', errors='ignore')
        response.close()
        return body
    except urllib.error.URLError as e:
        log(f"Error retrieving: {page_url} - {e}")
        return ''


class LinkFinder(HTMLParser):
    """Extract all <a href=""..."> links from HTML."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)


def find_links(html):
    """Return a list of links in HTML."""
    parser = LinkFinder()
    parser.feed(html)
    parser.close()
    return parser.links


class Spider:
    """
    Crawls a website, extracts content, and supports multiple export formats.
    """

    def __init__(self, initial_url, log=None):
        self.visited_urls = set()
        self.visited_urls.add(initial_url)
        self.base_url = initial_url
        self._queue = [initial_url]
        self.collected_data = []  # Stores extracted content

        self.log = log_stdout if log is None else log

    def run(self):
        while self._queue:
            current_url = self._queue.pop()
            self.log(f"Retrieving: {current_url}")
            self._process_page(current_url)

    def _url_in_site(self, link):
        return link.startswith(self.base_url)

    @staticmethod
    def _extract_content(html):
        """Extract page title and a cleaned text snippet."""
        # Extract <title> tag
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled"

        # Strip HTML tags and normalize whitespace
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()

        # Return title + first 800 chars to keep files manageable
        return title, text[:800]

    def _process_page(self, page_url):
        html = get_page(page_url, self.log)
        if not html:
            return

        # Extract and store content
        page_title, page_snippet = self._extract_content(html)
        self.collected_data.append({
            "url": page_url,
            "title": page_title,
            "content_snippet": page_snippet
        })

        # Find and queue new links
        for raw_link in find_links(html):
            absolute_link = urllib.parse.urljoin(page_url, raw_link)
            self.log(f"Checking: {absolute_link}")

            if absolute_link not in self.visited_urls and self._url_in_site(absolute_link):
                self.visited_urls.add(absolute_link)
                self._queue.append(absolute_link)

    # ================= EXPORT METHODS =================
    def save_to_txt(self, filepath):
        """Save collected data to a plain text file."""
        with open(filepath, 'w', encoding='utf-8') as file:
            for item in self.collected_data:  # ✅ Fixed typo
                file.write(f"URL: {item['url']}\n")
                file.write(f"Title: {item['title']}\n")
                file.write(f"Snippet: {item['content_snippet']}\n")
                file.write("-" * 60 + "\n")
        self.log(f"✅ Data saved to {filepath}")

    def save_to_csv(self, filepath):
        """Save collected data to a CSV file."""
        fieldnames = ["url", "title", "content_snippet"]
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.collected_data)
        self.log(f"✅ Data saved to {filepath}")

    def save_to_json(self, filepath):
        """Save collected data to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(self.collected_data, file, indent=4, ensure_ascii=False)
        self.log(f"✅ Data saved to {filepath}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python spider.py <URL>")
        sys.exit(1)

    target_url = sys.argv[1]
    crawler = Spider(target_url)
    crawler.run()

    # Export to all three formats automatically
    crawler.save_to_txt("crawled_pages.txt")
    crawler.save_to_csv("crawled_pages.csv")
    crawler.save_to_json("crawled_pages.json")