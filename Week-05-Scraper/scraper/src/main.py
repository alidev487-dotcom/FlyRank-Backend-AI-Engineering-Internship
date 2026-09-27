import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/alidev487-dotcom/FlyRank-Backend-AI-Engineering-Internship)"
TIMEOUT_SECONDS = 10
DELAY_SECONDS = 0.5
CACHE_DIR = "cache"

BASE_URL = "https://books.toscrape.com/catalogue/"
FIRST_PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"


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
    time.sleep(DELAY_SECONDS)
    return html


def get_book_links_from_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 a")
        if a_tag and a_tag.get("href"):
            absolute_url = urljoin(page_url, a_tag["href"])
            links.append(absolute_url)
    return links


def get_next_page_url(html, current_page_url):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link and next_link.get("href"):
        return urljoin(current_page_url, next_link["href"])
    return None


def discover_all_book_links():
    all_links = []
    current_url = FIRST_PAGE_URL
    page_number = 1
    MAX_PAGES = 3

    while current_url and page_number <= MAX_PAGES:
        cache_filename = f"catalogue-page-{page_number}.html"
        html = fetch_page(current_url, cache_filename)
        if html is None:
            break

        page_links = get_book_links_from_page(html, current_url)
        all_links.extend(page_links)

        current_url = get_next_page_url(html, current_url)
        page_number += 1

    unique_links = list(dict.fromkeys(all_links))

    print(f"catalogue_pages={page_number - 1}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    return unique_links


if __name__ == "__main__":
    print("Polite scraper starting...")
    book_links = discover_all_book_links()