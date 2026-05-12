import requests
from bs4 import BeautifulSoup, Comment
import json  # For JSON output


def extract_and_save(url, output_file='output.txt', format='txt'):

    try:
        # 1. Fetch the page
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # 2. Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        raw_text_nodes = soup.find_all(string=True)

        # 3. Filter & clean nodes
        cleaned_nodes = []
        for node in raw_text_nodes:
            if isinstance(node, Comment):
                continue
            if hasattr(node.parent, 'name') and node.parent.name in ['script', 'style']:
                continue
            stripped = node.strip()
            if stripped:
                cleaned_nodes.append({
                    'text': stripped,
                    'parent': node.parent.name if hasattr(node.parent, 'name') else None
                })

        # 4. Save to file based on format
        if format == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in cleaned_nodes:
                    f.write(item['text'] + '\n')

        elif format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_nodes, f, ensure_ascii=False, indent=2)

        elif format == 'csv':
            import csv
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['text', 'parent_tag'])
                for item in cleaned_nodes:
                    writer.writerow([item['text'], item['parent']])

        print(f"✅ Saved {len(cleaned_nodes)} text nodes to '{output_file}'")
        return cleaned_nodes

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


# ===== USAGE EXAMPLES =====
# Save as plain text
extract_and_save('https://kalshi.com/', 'YF.txt', format='txt')

# Save as JSON (with structure)
extract_and_save('https://kalshi.com/', 'YF.json', format='json')

# Save as CSV (for Excel)
extract_and_save('https://kalshi.com/', 'YF.csv', format='csv')