import os
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YOUR_USERNAME/FlyRank-Backend-AI-Engineering-Internship)"
TIMEOUT_SECONDS = 10
CACHE_DIR = "cache"

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"


def fetch_page(url, cache_filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        print(f"FETCH FAILED: {url} returned status {response.status_code}")
        return None

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    return html


if __name__ == "__main__":
    print("Polite scraper starting...")
    page1_html = fetch_page(CATALOGUE_URL, "catalogue-page-1.html")