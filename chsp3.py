import requests
from bs4 import BeautifulSoup

def crawl_web(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href:
                print(href)
    else:
        print(f"Failed to retrieve webpage. Status code: {response.status_code}")

if __name__ == "__main__":
    start_url = "https://example.com"
    crawl_web(start_url)