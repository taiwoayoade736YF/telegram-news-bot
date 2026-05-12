# test_connection.py
import requests
urls = ["https://www.gamespot.com/news/", "https://www.bbc.com/news"]
for url in urls:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        print(f"{url}: {r.status_code} ✅" if r.ok else f"{url}: {r.status_code} ❌")
    except Exception as e:
        print(f"{url}: Error - {e}")