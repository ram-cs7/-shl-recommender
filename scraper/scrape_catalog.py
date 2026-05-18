"""
SHL Product Catalog Scraper
────────────────────────────
Scrapes Individual Test Solutions from https://www.shl.com/solutions/products/product-catalog/
and writes data/catalog.json.

Strategy
────────
1. Requests + BeautifulSoup  (fast, no browser dependency)
2. Falls back to Playwright if JS rendering is required

Usage
─────
    python -m scraper.scrape_catalog

Set SHL_USE_PLAYWRIGHT=1 to force the Playwright path.
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL    = "https://www.shl.com"
CATALOG_URL = f"{BASE_URL}/solutions/products/product-catalog/"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "catalog.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TEST_TYPE_KEYWORDS: dict[str, list[str]] = {
    "A": ["ability", "aptitude", "numerical", "verbal", "inductive", "deductive",
          "spatial", "mechanical", "reasoning"],
    "P": ["personality", "behavioural", "behavioral", "opq", "motivation"],
    "K": ["knowledge", "skills", "coding", "java", "python", "technical"],
    "S": ["simulation", "situational judgment", "sjt", "game-based"],
    "C": ["competency", "360", "structured"],
    "B": ["biodata", "biographical"],
}

PAGE_SIZE   = 12   # SHL catalog shows 12 results per page
REQUEST_GAP = 0.8  # seconds between requests


# ── Session helper ────────────────────────────────────────────────────────────
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


# ── Test-type heuristic ───────────────────────────────────────────────────────
def infer_test_type(text: str) -> tuple[str, str]:
    """Return (code, label) based on keyword presence in page text."""
    text_lower = text.lower()
    for code, keywords in TEST_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            from app.retriever import TEST_TYPE_LABELS  # lazy import
            return code, TEST_TYPE_LABELS.get(code, "")
    return "", ""


# ── Product detail scraper ────────────────────────────────────────────────────
def scrape_detail(session: requests.Session, url: str, retries: int = 2) -> Optional[dict]:
    """Fetch an individual product page and extract structured data."""
    for attempt in range(retries + 1):
        try:
            time.sleep(REQUEST_GAP)
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt == retries:
                logger.warning("Failed to fetch %s: %s", url, exc)
                return None
            time.sleep(2 ** attempt)

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    assessment: dict = {"url": url}

    # Name — prefer <h1>, fallback to <title>
    h1 = soup.find("h1")
    if h1:
        assessment["name"] = h1.get_text(strip=True)
    else:
        title = soup.find("title")
        assessment["name"] = (title.get_text(strip=True) if title else "").split("|")[0].strip()

    # Description — prefer meta description, then first long <p>
    meta = soup.find("meta", {"name": "description"})
    if meta and meta.get("content"):
        assessment["description"] = meta["content"].strip()
    else:
        for p in soup.find_all("p"):
            txt = p.get_text(strip=True)
            if len(txt) > 60:
                assessment["description"] = txt
                break
        else:
            assessment["description"] = ""

    # Test type
    code, label = infer_test_type(page_text)
    assessment["test_type"]       = code
    assessment["test_type_label"] = label

    # Duration
    dur_match = re.search(
        r"(\d+)\s*(?:to|-)\s*(\d+)\s*min|(\d+)\s*min(?:ute)?s?",
        page_text, re.I
    )
    if dur_match:
        if dur_match.group(1) and dur_match.group(2):
            assessment["duration"] = f"{dur_match.group(1)}–{dur_match.group(2)} minutes"
        elif dur_match.group(3):
            assessment["duration"] = f"{dur_match.group(3)} minutes"
    else:
        assessment["duration"] = "N/A"

    # Remote testing
    assessment["remote_testing"] = (
        "Yes" if re.search(r"\bremote\b.*\btest", page_text, re.I) else "Check catalog"
    )

    # Adaptive / IRT
    assessment["adaptive_irt"] = (
        "Yes" if re.search(r"\badaptive\b|\birt\b|\bitem response", page_text, re.I) else "No"
    )

    # Languages — surface-level heuristic
    lang_match = re.search(r"(\d+)\+?\s*language", page_text, re.I)
    assessment["languages"] = (
        [f"{lang_match.group(1)}+ languages"] if lang_match else []
    )

    # Job levels — common SHL taxonomy
    levels = []
    for level in ["graduate", "manager", "director", "professional", "executive",
                  "entry", "mid-level", "senior", "frontline"]:
        if level in page_text.lower():
            levels.append(level.title())
    assessment["job_levels"] = levels

    return assessment


# ── Catalog page scraper ──────────────────────────────────────────────────────
def scrape_catalog_page_bs(
    session: requests.Session, start: int
) -> tuple[list[dict], bool]:
    """Scrape one page of the catalog using requests + BeautifulSoup."""
    params = {"start": start, "type": "1"}   # type=1 → Individual Test Solutions

    resp = session.get(CATALOG_URL, params=params, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Try every known card selector ─────────────────────────────────────
    items: list[Tag] = []
    selectors = [
        # SHL uses a table-based catalog with data-entity attributes in some versions
        "div[data-entity-id]",
        "tr[data-href]",
        ".product-catalogue__result",
        ".product-catalogue-table__row",
        "article.product-card",
        # Generic fallback: any link inside the catalog section leading to /solutions/products/
    ]
    for sel in selectors:
        items = soup.select(sel)
        if items:
            logger.debug("Selector '%s' matched %d items", sel, len(items))
            break

    # If still nothing: extract all product links from the page body
    if not items:
        body = soup.find("main") or soup.find("body")
        if body:
            items = [
                a for a in body.find_all("a", href=True)
                if "/solutions/products/" in (a.get("href") or "")
                and "product-catalog" not in (a.get("href") or "")
            ]

    assessments: list[dict] = []
    seen_urls: set[str] = set()

    for item in items:
        # Resolve link
        link = item if item.name == "a" else item.find("a", href=True)
        if not link:
            continue

        href: str = link.get("href", "")
        if not href or "/solutions/products/" not in href:
            continue

        url = href if href.startswith("http") else BASE_URL + href

        # Skip Job Solutions or already seen
        if "job-solution" in url or url in seen_urls:
            continue
        seen_urls.add(url)

        detail = scrape_detail(session, url)
        if detail and detail.get("name"):
            assessments.append(detail)
            logger.info("  ✓ %s", detail["name"])

    # Detect next page
    has_more = bool(
        soup.select_one(".pagination__next:not([disabled]):not(.is-disabled)")
        or soup.find("a", {"rel": "next"})
        or (items and len(items) >= PAGE_SIZE)
    )

    return assessments, has_more


# ── Playwright fallback ───────────────────────────────────────────────────────
def scrape_catalog_playwright() -> list[dict]:
    """
    Playwright-based scraper for when SHL requires JS rendering.
    Requires:  pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    logger.info("Using Playwright (JS rendering) …")
    assessments: list[dict] = []
    seen_urls: set[str] = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page    = browser.new_page()

        start = 0
        while True:
            url = f"{CATALOG_URL}?start={start}&type=1"
            page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1500)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Collect product links
            links = [
                a.get("href") for a in soup.find_all("a", href=True)
                if "/solutions/products/" in (a.get("href") or "")
                and "product-catalog" not in (a.get("href") or "")
            ]

            if not links:
                break

            session = make_session()
            page_count = 0

            for href in links:
                full_url = href if href.startswith("http") else BASE_URL + href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                detail = scrape_detail(session, full_url)
                if detail and detail.get("name"):
                    assessments.append(detail)
                    page_count += 1
                    logger.info("  ✓ %s", detail["name"])

            if page_count < PAGE_SIZE // 2:
                break

            start += PAGE_SIZE

        browser.close()

    return assessments


# ── Orchestration ─────────────────────────────────────────────────────────────
def run() -> list[dict]:
    use_playwright = os.getenv("SHL_USE_PLAYWRIGHT", "0") == "1"
    if use_playwright:
        return scrape_catalog_playwright()

    session    = make_session()
    all_data: list[dict] = []
    seen_urls: set[str]  = set()
    start  = 0
    page   = 1

    while True:
        logger.info("Page %d  (offset=%d) …", page, start)
        try:
            items, has_more = scrape_catalog_page_bs(session, start)
        except requests.RequestException as exc:
            logger.error("Request error: %s", exc)
            if not all_data:
                logger.info("Falling back to Playwright …")
                return scrape_catalog_playwright()
            break

        new = [a for a in items if a["url"] not in seen_urls]
        for a in new:
            seen_urls.add(a["url"])
        all_data.extend(new)
        logger.info("Page %d: %d new  |  total so far: %d", page, len(new), len(all_data))

        if not has_more or not new:
            break

        start += PAGE_SIZE
        page  += 1

    # If BS4 found nothing (JS-rendered page), fall back
    if not all_data:
        logger.info("BS4 found nothing — switching to Playwright …")
        return scrape_catalog_playwright()

    return all_data


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting SHL Individual Test Solutions scrape …")
    catalog = run()

    if not catalog:
        logger.error("Scraper returned 0 assessments. "
                     "Check selectors or set SHL_USE_PLAYWRIGHT=1.")
        return

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=2, ensure_ascii=False)

    logger.info("Wrote %d assessments → %s", len(catalog), OUTPUT_PATH)

    # Quick summary
    print(f"\n{'─'*55}")
    print(f"  {'NAME':<40}  TYPE")
    print(f"{'─'*55}")
    for a in catalog[:10]:
        print(f"  {a['name'][:40]:<40}  {a.get('test_type', '?')}")
    if len(catalog) > 10:
        print(f"  … and {len(catalog) - 10} more")
    print(f"{'─'*55}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing catalog.json")
    args = parser.parse_args()
    if OUTPUT_PATH.exists() and not args.force:
        print(f"catalog.json already exists. Use --force to re-scrape.")
    else:
        main()
