#!/usr/bin/env python3
"""
Ndola City Council Web Scraper & HTML Table Extractor
Course: 2025/26 CSC 4792 - Data Mining and Warehousing
Target: Ndola City Council (https://www.ndolacouncil.gov.zm)

This script crawls key pages on the Ndola City Council website, extracts HTML
tables (such as CDF project trackers, ward statistics, departmental data),
and saves raw HTML dumps and structured JSON dumps into the /source_files/ directory.
"""

import json
import logging
import os
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

# Suppress insecure SSL warnings for government portal certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.ndolacouncil.gov.zm"
SOURCE_FILES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "source_files")
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False
    return session


def crawl_site_pages(session, max_pages=100):
    """
    Crawls internal pages starting from known hub endpoints to discover
    content, tables, and document links.
    """
    seed_urls = [
        f"{BASE_URL}/",
        f"{BASE_URL}/?page_id=2845",  # Downloads
        f"{BASE_URL}/?page_id=1879",  # CDF Page
        f"{BASE_URL}/?page_id=3765",  # CDF Projects
        f"{BASE_URL}/?page_id=3162",  # Publications
        f"{BASE_URL}/?page_id=932",  # CDF Project Tracker
        f"{BASE_URL}/?page_id=3621",  # ZDSP
        f"{BASE_URL}/?page_id=187",  # News
        f"{BASE_URL}/?page_id=118",  # Who We Are / Council Profile
        f"{BASE_URL}/?page_id=2814",  # Administration
        f"{BASE_URL}/?page_id=2816",  # Finance
        f"{BASE_URL}/?page_id=2818",  # Engineering Services
        f"{BASE_URL}/?page_id=2823",  # Public Health
        f"{BASE_URL}/?page_id=2827",  # Legal
        f"{BASE_URL}/?page_id=2832",  # Planning
        f"{BASE_URL}/?page_id=2834",  # Housing & Social Services
        f"{BASE_URL}/?page_id=2838",  # Fisheries & Livestock
        f"{BASE_URL}/?page_id=2841",  # Agriculture
    ]

    visited = set()
    queue = list(seed_urls)
    discovered_pages = {}
    doc_links = set()

    logger.info(f"Beginning crawl starting with {len(seed_urls)} seed URLs...")

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            page_title = soup.title.get_text(strip=True) if soup.title else url

            # Record page details
            tables = soup.find_all("table")
            discovered_pages[url] = {
                "title": page_title,
                "status": resp.status_code,
                "table_count": len(tables),
                "content_length": len(resp.text),
            }

            # Discover internal document links and child pages
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)

                # Check for document extensions
                ext = parsed.path.split(".")[-1].lower() if "." in parsed.path else ""
                if ext in ["pdf", "xlsx", "xls", "docx", "doc", "csv"]:
                    link_text = a_tag.get_text(strip=True)
                    doc_links.add((full_url, link_text, ext))
                elif "ndolacouncil.gov.zm" in parsed.netloc:
                    clean_url = full_url.split("#")[0]
                    if clean_url not in visited and clean_url not in queue:
                        if any(
                            param in clean_url
                            for param in ["page_id=", "p=", "category", "tag"]
                        ):
                            queue.append(clean_url)

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")

    logger.info(
        f"Crawl completed. Visited {len(visited)} pages. Discovered {len(doc_links)} downloadable documents."
    )
    return discovered_pages, doc_links


def extract_and_dump_html_tables(session):
    """
    Extracts all HTML tables from key tracking and operational pages,
    saving raw HTML and structured data into /source_files/.
    """
    os.makedirs(SOURCE_FILES_DIR, exist_ok=True)
    tracker_url = f"{BASE_URL}/?page_id=932"
    logger.info(f"Extracting HTML tables from tracker page: {tracker_url}")

    try:
        resp = session.get(tracker_url, timeout=25)
        if resp.status_code == 200:
            # Save raw HTML dump
            raw_html_path = os.path.join(
                SOURCE_FILES_DIR, "ndola_council_tracker_raw.html"
            )
            with open(raw_html_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            logger.info(f"Saved raw tracker HTML to {raw_html_path}")

            # Parse tables
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")
            extracted_tables = []

            for idx, table in enumerate(tables):
                headers = []
                header_row = table.find("tr")
                if header_row:
                    headers = [
                        th.get_text(strip=True)
                        for th in header_row.find_all(["th", "td"])
                    ]

                rows_data = []
                for tr in table.find_all("tr")[1:]:
                    cells = [
                        td.get_text(strip=True) for td in tr.find_all(["td", "th"])
                    ]
                    if cells and any(cells):
                        rows_data.append(cells)

                table_dict = {
                    "table_index": idx + 1,
                    "headers": headers,
                    "row_count": len(rows_data),
                    "rows": rows_data,
                }
                extracted_tables.append(table_dict)

            json_path = os.path.join(
                SOURCE_FILES_DIR, "ndola_council_cdf_tracker_tables.json"
            )
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(extracted_tables, f, indent=2)
            logger.info(
                f"Saved {len(extracted_tables)} extracted HTML tables to {json_path}"
            )

    except Exception as e:
        logger.error(f"Failed to scrape HTML tables: {e}")


def main():
    session = get_session()
    discovered_pages, doc_links = crawl_site_pages(session)
    extract_and_dump_html_tables(session)

    # Save discovery manifest
    manifest_path = os.path.join(SOURCE_FILES_DIR, "site_discovery_index.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "target": BASE_URL,
                "crawled_pages_count": len(discovered_pages),
                "discovered_documents_count": len(doc_links),
                "discovered_documents": [
                    {"url": u, "anchor_text": t, "extension": ext}
                    for u, t, ext in sorted(doc_links)
                ],
                "crawled_pages": discovered_pages,
            },
            f,
            indent=2,
        )
    logger.info(f"Saved site discovery index to {manifest_path}")


if __name__ == "__main__":
    main()
