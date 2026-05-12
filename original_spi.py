#!/usr/bin/env python3
# program: spider.py
# author: YF (original username)
# version: 2.2
# date: April 2026
# description: Start from the command line with a URL argument.
# Finds and lists all pages within a website.

import sys
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
    The heart of this program, finds all links within a website.
    run() contains the main loop.
    process_page() retrieves each page and finds the links.
    """

    def __init__(self, initial_url, log=None):
        self.visited_urls = set()
        self.visited_urls.add(initial_url)
        self.base_url = initial_url
        self._queue = [initial_url]

        self.log = log_stdout if log is None else log

    def run(self):
        while self._queue:
            current_url = self._queue.pop()
            self.log(f"Retrieving: {current_url}")
            self._process_page(current_url)

    def _url_in_site(self, link):
        return link.startswith(self.base_url)

    def _process_page(self, page_url):
        html = get_page(page_url, self.log)
        for raw_link in find_links(html):
            absolute_link = urllib.parse.urljoin(page_url, raw_link)
            self.log(f"Checking: {absolute_link}")

            if absolute_link not in self.visited_urls and self._url_in_site(absolute_link):
                self.visited_urls.add(absolute_link)
                self._queue.append(absolute_link)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python spider.py <URL>")
        sys.exit(1)

    base_url = sys.argv[1]
    crawler = Spider(base_url)
    crawler.run()

    for discovered_url in sorted(crawler.visited_urls):
        print(discovered_url)