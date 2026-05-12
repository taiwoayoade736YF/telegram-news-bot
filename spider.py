#!/usr/bin/env python3
"""
===============================================
PROGRAM: spider.py (Python 3 Version)
AUTHOR: Converted from aahz's original (2006)
VERSION: 2.0
DATE: 2026
DESCRIPTION: Web crawler that finds all pages
             within a website. Start from command line:
             python3 spider.py https://example.com
===============================================
"""

# ===== IMPORT MODULES =====
import sys  # For command-line arguments
import urllib.request  # Download web pages (replaces urllib2)
import urllib.error  # Handle URL errors
import urllib.parse  # Parse and join URLs (replaces urlparse)
from html.parser import HTMLParser  # Parse HTML (replaces htmllib)
from urllib.parse import urljoin, urlparse  # URL manipulation
from collections import deque  # Efficient queue for BFS


# ===== LINE 15-17: LOGGING FUNCTION =====
def log_stdout(msg):
    """
    Print message to the screen.
    This is a simple logging function that can be replaced
    with file logging or other output methods.

    Args:
        msg (str): Message to print
    """
    print(msg)


# ===== LINE 19-31: PAGE DOWNLOADER =====
def get_page(url, log):
    """
    Retrieve URL content and return HTML, log errors.

    Args:
        url (str): URL to download
        log (function): Logging function to use

    Returns:
        str: HTML content, or empty string on error
    """
    try:
        # Create request with User-Agent header (avoids 403 errors)
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'EducationalSpider/1.0'}
        )

        # Open URL with timeout (prevents hanging)
        with urllib.request.urlopen(req, timeout=10) as response:
            # Handle character encoding properly
            charset = response.headers.get_content_charset() or 'utf-8'
            return response.read().decode(charset, errors='ignore')

    except urllib.error.URLError as e:
        # Log network errors (DNS failure, timeout, etc.)
        log(f"❌ Error retrieving: {url} - {e}")
        return ''

    except Exception as e:
        # Log unexpected errors
        log(f"❌ Unexpected error at {url}: {e}")
        return ''


# ===== LINE 33-49: LINK EXTRACTOR =====
class LinkFinder(HTMLParser):
    """
    Custom HTML parser that extracts href values from <a> tags.
    This replaces the old htmllib.HTMLParser + formatter approach.
    """

    def __init__(self):
        # Initialize parent HTMLParser class
        super().__init__()
        # Store extracted links in a list
        self.links = []

    def handle_starttag(self, tag, attrs):
        """
        Called automatically when parser encounters a start tag (<a>, <div>, etc.)

        Args:
            tag (str): Tag name (e.g., 'a', 'div', 'img')
            attrs (list): List of (attribute, value) tuples
        """
        # Only process <a> tags (anchor/link tags)
        if tag == 'a':
            # Convert attrs list to dictionary for easier access
            attrs_dict = dict(attrs)

            # Check if 'href' attribute exists
            if 'href' in attrs_dict:
                # Get the href value and clean it
                href = attrs_dict['href'].strip()

                # Skip empty hrefs and JavaScript links
                if href and not href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    self.links.append(href)


def find_links(html):
    """
    Parse HTML and return list of link URLs.

    Args:
        html (str): Raw HTML content

    Returns:
        list: Extracted href values (may be relative URLs)
    """
    # Create parser instance
    parser = LinkFinder()

    # Feed HTML to parser (triggers handle_starttag for each tag)
    try:
        parser.feed(html)
    except Exception as e:
        # Best-effort parsing; continue even if HTML is malformed
        print(f"⚠️ Warning: HTML parsing error: {e}")

    # Close parser (cleanup)
    parser.close()

    # Return collected links
    return parser.links


# ===== LINE 51-95: SPIDER CLASS =====
class Spider:
    """
    The heart of this program. Finds all links within a website.

    Attributes:
        start_url (str): Initial URL to crawl
        base_domain (str): Domain to stay within (e.g., 'example.com')
        URLs (set): All unique URLs discovered
        _links_to_process (deque): Queue of URLs to crawl next
        log (function): Logging function
    """

    def __init__(self, start_url, log=None):
        """
        Initialize spider with starting URL.

        Args:
            start_url (str): URL to begin crawling
            log (function, optional): Logging function. Defaults to log_stdout.
        """
        # Store starting URL
        self.start_url = start_url

        # Extract base domain for filtering (handles http/https and www)
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc.lower().replace('www.', '')
        self.scheme = parsed.scheme  # 'http' or 'https'

        # Track all discovered URLs (set prevents duplicates)
        self.URLs = set()
        self.URLs.add(start_url)

        # Queue of URLs to process (BFS using deque for efficiency)
        self._links_to_process = deque([start_url])

        # Set logging function
        if log is None:
            self.log = log_stdout
        else:
            self.log = log

    def url_in_site(self, link):
        """
        Check if link belongs to the same site as start_url.

        Args:
            link (str): URL to check

        Returns:
            bool: True if same domain and scheme, False otherwise
        """
        try:
            # Parse the link
            parsed = urlparse(link)

            # Extract domain (normalize by removing www.)
            domain = parsed.netloc.lower().replace('www.', '')

            # Check if domain and scheme match base
            return domain == self.base_domain and parsed.scheme == self.scheme
        except:
            # If parsing fails, assume it's not in site
            return False

    def run(self, max_pages=100):
        """
        Main crawling loop. Processes URLs until queue is empty or limit reached.

        Args:
            max_pages (int): Maximum number of pages to crawl (safety limit)
        """
        self.log(f"🕷️ Starting crawl at: {self.start_url}")
        self.log("=" * 60)

        # Continue while there are URLs to process and limit not reached
        while self._links_to_process and len(self.URLs) < max_pages:
            # Get next URL from queue (BFS: popleft = first-in-first-out)
            url = self._links_to_process.popleft()

            # Log current URL being processed
            self.log(f"📥 Retrieving: {url}")

            # Process the page (download + extract links)
            self.process_page(url)

        # Crawl complete
        self.log("=" * 60)
        self.log(f"✅ Crawl finished! Discovered {len(self.URLs)} pages.")

    def process_page(self, url):
        """
        Download page, extract links, and add new links to queue.

        Args:
            url (str): URL to process
        """
        # Download HTML content
        html = get_page(url, self.log)

        # Skip if download failed
        if not html:
            return

        # Extract all links from HTML
        raw_links = find_links(html)

        # Process each link
        for raw_link in raw_links:
            # Resolve relative URLs to absolute URLs
            # Example: url="https://example.com/blog/post1", raw_link="../contact"
            # Result: "https://example.com/contact"
            absolute_link = urljoin(url, raw_link)

            # Log the link being checked
            self.log(f"  🔍 Checking: {absolute_link}")

            # Add to queue if: (1) not seen before AND (2) same site
            if absolute_link not in self.URLs and self.url_in_site(absolute_link):
                # Add to discovered URLs
                self.URLs.add(absolute_link)

                # Add to queue for future crawling
                self._links_to_process.append(absolute_link)

                # Log new discovery
                self.log(f"    ➕ Added to queue: {absolute_link}")


# ===== LINE 97-107: MAIN EXECUTION =====
if __name__ == '__main__':
    """
    This code runs when script is started from command line.
    Entry point of the program.
    """

    # Validate command-line arguments
    if len(sys.argv) < 2:
        print("❌ Usage: python3 spider.py https://example.com")
        print("❌ Example: python3 spider.py https://example.com")
        sys.exit(1)

    # Get starting URL from command line
    start_url = sys.argv[1]

    # Basic URL validation
    if not start_url.startswith(('http://', 'https://')):
        print("❌ Error: URL must start with http:// or https://")
        sys.exit(1)

    # Create spider instance
    spider = Spider(start_url)

    # Run the spider (crawl the site)
    spider.run(max_pages=50)  # Limit for safety

    # Print all discovered URLs
    print("\n" + "=" * 60)
    print("📄 DISCOVERED URLS:")
    print("=" * 60)

    for i, url in enumerate(sorted(spider.URLs), 1):
        print(f"{i:3d}. {url}")
