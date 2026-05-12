import sys
import urllib.request
import urllib.error
from urllib.parse import urljoin
from html.parser import HTMLParser

def log_stdout(msg):
    """Print msg to the screen."""
    print(msg)

def get_page(url, log):
    """Retrieve URL and return contents, log errors."""
    try:
        page = urllib.request.urlopen(url)
    except urllib.error.URLError:
        log("Error retrieving: " + url)
        return ''
    body = page.read().decode('utf-8')
    page.close()
    return body

class LinkParser(HTMLParser):
    """Extracts href attributes from <a> tags."""
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.links.append(value)

def find_links(html):
    """Return a list of links in html."""
    parser = LinkParser()
    parser.feed(html)
    return parser.links

class Spider:
    """
    The heart of this program, finds all links within a web site.
    run() contains the main loop.
    process_page() retrieves each page and finds the links.
    """
    def __init__(self, start_url, log=None):
        self.URLs = set()
        self.URLs.add(startURL)
        self.include = startURL
        self._links_to_process = [startURL]
        if log is None:
            self.log = log_stdout
        else:
            self.log = log

    def run(self):
        while self._links_to_process:
            url = self._links_to_process.pop()
            self.log("Retrieving: " + url)
            self.process_page(url)

    def url_in_site(self, link):
        return link.startswith(self.include)

    def process_page(self, url):
        html = get_page(url, self.log)
        for link in find_links(html):
            link = urljoin(url, link)
            self.log("Checking: " + link)
            if link not in self.URLs and self.url_in_site(link):
                self.URLs.add(link)
                self._links_to_process.append(link)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python spider.py <start_url>")
        sys.exit(1)
    startURL = sys.argv[1]
    spider = Spider(startURL)
    spider.run()
    for URL in sorted(spider.URLs):
        print(URL)
