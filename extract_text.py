# 1. Import required classes
from bs4 import BeautifulSoup,  Comment

# 2. Define sample HTML
# Replace the html_content string with this:
with open('my_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
# 3. Parse HTML into a DOM-like tree
soup = BeautifulSoup(html_content, 'html.parser')

# 4. Extract all raw text nodes
raw_text_nodes = soup.find_all(string=True)

# 5. Filter out unwanted nodes (comments, whitespace, script/style)
meaningful_text_nodes = []
for node in raw_text_nodes:
    if isinstance(node, Comment):
        continue
    if hasattr(node.parent, 'name') and node.parent.name in ['script', 'style']:
        continue
    stripped_text = node.strip()
    if stripped_text:
        meaningful_text_nodes.append(stripped_text)

# 6. Output results
for txt in meaningful_text_nodes:
    print(repr(txt))