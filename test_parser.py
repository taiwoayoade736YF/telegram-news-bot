# Save as test_parser.py
from html.parser import HTMLParser


class LinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)


# Test it
html = '''
<html>
  <body>
    <a href="/home">Home</a>
    <a href="https://example.com/about">About</a>
    <a href="../contact">Contact</a>
    <img src="logo.png">  <!-- NOT extracted -->
  </body>
</html>
'''

parser = LinkFinder()
parser.feed(html)
print("Extracted links:", parser.links)