import os
import time
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/alidev487-dotcom/FlyRank-Backend-AI-Engineering-Internship)"
)

TIMEOUT_SECONDS = 10
DELAY_SECONDS = 0.5
CACHE_DIR = "cache"
MAX_PAGES = 3

FIRST_PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"

RATING_WORDS = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def fetch_page(url, cache_filename):
    os.makedirs(CACHE_DIR, exist_ok=True)

    cache_path = os.path.join(CACHE_DIR, cache_filename)

    # Use cached HTML if it already exists
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()

        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )
    except requests.RequestException as e:
        print(f"FETCH ERROR: {url}")
        print(f"Reason: {e}")
        return None

    if response.status_code != 200:
        print(
            f"FETCH FAILED: {url} "
            f"returned status {response.status_code}"
        )
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
            absolute_url = urljoin(
                page_url,
                a_tag["href"]
            )

            links.append(absolute_url)

    return links


def get_next_page_url(html, current_page_url):
    soup = BeautifulSoup(html, "html.parser")

    next_link = soup.select_one("li.next a")

    if next_link and next_link.get("href"):
        return urljoin(
            current_page_url,
            next_link["href"]
        )

    return None


def discover_all_book_links():
    all_links = []

    current_url = FIRST_PAGE_URL
    page_number = 1

    while current_url and page_number <= MAX_PAGES:

        print(
            f"\nDiscovering catalogue page "
            f"{page_number}/{MAX_PAGES}..."
        )

        cache_filename = (
            f"catalogue-page-{page_number}.html"
        )

        html = fetch_page(
            current_url,
            cache_filename
        )

        if html is None:
            break

        page_links = get_book_links_from_page(
            html,
            current_url
        )

        print(
            f"Found {len(page_links)} books "
            f"on page {page_number}"
        )

        all_links.extend(page_links)

        current_url = get_next_page_url(
            html,
            current_url
        )

        page_number += 1

    unique_links = list(dict.fromkeys(all_links))

    print("\n--- Discovery Summary ---")
    print(f"catalogue_pages={page_number - 1}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    return unique_links


def extract_book_record(
    html,
    product_url,
    source_page
):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    product_area = soup.select_one(
        "div.product_main"
    )

    # Title
    title = None

    if product_area:
        title_tag = product_area.select_one("h1")

        if title_tag:
            title = title_tag.get_text(
                strip=True
            )

    # Price
    price_text = None

    price_tag = soup.select_one(
        "p.price_color"
    )

    if price_tag:
        price_text = price_tag.get_text(
            strip=True
        )

    # Availability
    availability_text = None

    availability_tag = soup.select_one(
        "p.availability"
    )

    if availability_tag:
        availability_text = availability_tag.get_text(
            " ",
            strip=True
        )

    # Rating
    rating_text = None

    if product_area:
        rating_tag = product_area.select_one(
            "p.star-rating"
        )

        if rating_tag:
            classes = rating_tag.get(
                "class",
                []
            )

            for cls in classes:
                if cls in RATING_WORDS:
                    rating_text = cls
                    break

    # Description
    description = None

    description_heading = soup.find(
        "div",
        id="product_description"
    )

    if description_heading:
        description_paragraph = (
            description_heading.find_next_sibling("p")
        )

        if description_paragraph:
            description = (
                description_paragraph.get_text(
                    strip=True
                )
            )

    record = {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    return record


def make_cache_filename_for_book(product_url):
    slug = product_url.rstrip("/").split("/")[-2]
    book_id = slug.split("_")[-1]
    return f"book-{book_id}.html"

def extract_all_books(book_links):
    records = []

    total = len(book_links)

    print(
        f"\nStarting detail-page extraction "
        f"for {total} books..."
    )

    for index, link in enumerate(
        book_links,
        start=1
    ):

        print(
            f"\nProcessing book "
            f"{index}/{total}"
        )

        cache_filename = (
            make_cache_filename_for_book(link)
        )

        html = fetch_page(
            link,
            cache_filename
        )

        if html is None:
            continue

        record = extract_book_record(
            html,
            link,
            source_page=FIRST_PAGE_URL
        )

        records.append(record)

        print(
            f"Extracted: {record['title']}"
        )

    print("\n--- Extraction Summary ---")
    print(f"detail_pages={len(records)}")

    return records


def save_records(records):
    output_file = "books.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            records,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nSaved {len(records)} records "
        f"to {output_file}"
    )


def main():
    print("=" * 60)
    print("Polite scraper starting...")
    print("=" * 60)

    book_links = discover_all_book_links()

    if not book_links:
        print(
            "\nERROR: No book links were discovered."
        )
        return

    raw_records = extract_all_books(
        book_links
    )

    if raw_records:
        print("\n--- Sample Record ---")

        print(
            json.dumps(
                raw_records[0],
                indent=2,
                ensure_ascii=False
            )
        )

        save_records(raw_records)

    else:
        print(
            "\nERROR: No book records were extracted."
        )


if __name__ == "__main__":
    main()

