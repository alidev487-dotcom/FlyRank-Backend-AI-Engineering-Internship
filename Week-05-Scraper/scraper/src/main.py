import os
import time
import json
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pydantic import BaseModel, ValidationError
from typing import Optional


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

stats = {
    "start_time": None,
    "pages_fetched": 0,
    "cache_hits": 0,
    "failed_pages": 0,
}


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: str
    fetched_at: str


def fetch_page(url, cache_filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        stats["cache_hits"] += 1
        return html

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        print(f"FETCH ERROR: {url}")
        print(f"Reason: {e}")
        stats["failed_pages"] += 1
        return None

    if response.status_code != 200:
        print(f"FETCH FAILED: {url} returned status {response.status_code}")
        stats["failed_pages"] += 1
        return None

    response.encoding = "utf-8"
    html = response.text

    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    stats["pages_fetched"] += 1
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

    while current_url and page_number <= MAX_PAGES:
        print(f"\nDiscovering catalogue page {page_number}/{MAX_PAGES}...")

        cache_filename = f"catalogue-page-{page_number}.html"
        html = fetch_page(current_url, cache_filename)

        if html is None:
            break

        page_links = get_book_links_from_page(html, current_url)
        print(f"Found {len(page_links)} books on page {page_number}")

        all_links.extend(page_links)
        current_url = get_next_page_url(html, current_url)
        page_number += 1

    unique_links = list(dict.fromkeys(all_links))

    print("\n--- Discovery Summary ---")
    print(f"catalogue_pages={page_number - 1}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    return unique_links


def clean_price(price_text):
    if not price_text:
        return None
    match = re.search(r"[\d.]+", price_text)
    if match:
        return float(match.group())
    return None


def extract_book_record(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")
    product_area = soup.select_one("div.product_main")

    title = None
    if product_area:
        title_tag = product_area.select_one("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)

    price_text = None
    price_tag = soup.select_one("p.price_color")
    if price_tag:
        price_text = price_tag.get_text(strip=True)

    availability_text = None
    availability_tag = soup.select_one("p.availability")
    if availability_tag:
        availability_text = availability_tag.get_text(" ", strip=True)

    rating_text = None
    if product_area:
        rating_tag = product_area.select_one("p.star-rating")
        if rating_tag:
            classes = rating_tag.get("class", [])
            for cls in classes:
                if cls in RATING_WORDS:
                    rating_text = cls
                    break

    description = None
    description_heading = soup.find("div", id="product_description")
    if description_heading:
        description_paragraph = description_heading.find_next_sibling("p")
        if description_paragraph:
            description = description_paragraph.get_text(strip=True)

    record = {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    return record


def make_cache_filename_for_book(product_url):
    slug = product_url.rstrip("/").split("/")[-2]
    book_id = slug.split("_")[-1]
    return f"book-{book_id}.html"


def extract_all_books(book_links):
    valid_records = []
    invalid_records = []
    total = len(book_links)

    print(f"\nStarting detail-page extraction for {total} books...")

    seen_urls = set()

    for index, link in enumerate(book_links, start=1):
        print(f"\nProcessing book {index}/{total}")

        if link in seen_urls:
            print(f"Skipping duplicate URL: {link}")
            continue
        seen_urls.add(link)

        cache_filename = make_cache_filename_for_book(link)
        html = fetch_page(link, cache_filename)

        if html is None:
            invalid_records.append({"url": link, "reason": "fetch failed"})
            continue

        raw_record = extract_book_record(html, link, source_page=FIRST_PAGE_URL)
        price_gbp = clean_price(raw_record["price_text"])

        try:
            validated = BookRecord(
                title=raw_record["title"],
                product_url=raw_record["product_url"],
                price_gbp=price_gbp,
                price_text=raw_record["price_text"],
                availability_text=raw_record["availability_text"],
                rating_text=raw_record["rating_text"],
                description=raw_record["description"],
                source_page=raw_record["source_page"],
                fetched_at=raw_record["fetched_at"],
            )
            valid_records.append(validated.model_dump())
            print(f"Extracted: {validated.title}")
        except ValidationError as e:
            invalid_records.append({"url": link, "reason": str(e)})
            print(f"VALIDATION FAILED: {link}")

    print("\n--- Extraction Summary ---")
    print(f"detail_pages={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")

    return valid_records, invalid_records


def save_records(valid_records, invalid_records):
    os.makedirs("output", exist_ok=True)

    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(valid_records)} valid records to output/books.json")

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(invalid_records)} invalid records to output/errors.json")


def save_run_report(valid_records, invalid_records):
    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - stats["start_time"]).total_seconds()

    report = {
        "start_time": stats["start_time"].isoformat(),
        "duration_seconds": round(duration_seconds, 2),
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": stats["failed_pages"],
    }

    os.makedirs("output", exist_ok=True)
    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n--- Run Report ---")
    print(json.dumps(report, indent=2))


def main():
    print("=" * 60)
    print("Polite scraper starting...")
    print("=" * 60)

    stats["start_time"] = datetime.now(timezone.utc)

    book_links = discover_all_book_links()

    if not book_links:
        print("\nERROR: No book links were discovered.")
        return

    # Deliberately add one broken URL to prove the pipeline survives a bad page
    book_links.append(
        "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"
    )

    valid_records, invalid_records = extract_all_books(book_links)

    if valid_records:
        print("\n--- Sample Record ---")
        print(json.dumps(valid_records[0], indent=2, ensure_ascii=False))

    save_records(valid_records, invalid_records)
    save_run_report(valid_records, invalid_records)


if __name__ == "__main__":
    main()