import requests
from bs4 import BeautifulSoup
import re


def extract_business_emails(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; EducationalBot/1.0; +https://yoursite.com/bot)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Simple regex for standard business emails (not foolproof)
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

    # Search in <a> tags and text nodes
    emails = set()
    for tag in soup.find_all(True):
        if tag.has_attr('href') and re.search(r'mailto:', str(tag['href']), re.IGNORECASE):
            emails.add(tag['href'].replace('mailto:', ''))
        if tag.string:
            matches = email_pattern.findall(tag.string)
            emails.update(matches)

    return list(emails)

# Example usage (replace with a site you own or have explicit permission to scrape)
print(extract_business_emails("https://fqluxury.org"))