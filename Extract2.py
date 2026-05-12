import requests
from bs4 import BeautifulSoup, Comment  # 🔧 FIX 1: Import Comment class

url = 'https://fqluxury.org'
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

# Extract all raw text nodes
raw_text_nodes = soup.find_all(string=True)

# Filter out unwanted nodes
meaningful_text_nodes = []
for node in raw_text_nodes:
    # 🔧 FIX 2: isinstance() needs TWO arguments: (object, type_to_check)
    if isinstance(node, Comment):  # ✅ Skip HTML comments
        continue
    if hasattr(node.parent, 'name') and node.parent.name in ['script', 'style']:
        continue
    stripped_text = node.strip()
    if stripped_text:
        meaningful_text_nodes.append(stripped_text)

# Output results
for txt in meaningful_text_nodes:
    print(repr(txt))