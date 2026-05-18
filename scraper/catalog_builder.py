"""
catalog_builder.py — Fetch the official SHL catalog JSON and convert it to
the internal format used by CatalogRetriever.

Usage:
    python -m scraper.catalog_builder          # fetch & write data/catalog.json
    python -m scraper.catalog_builder --dry-run # fetch & print stats only
"""

import argparse
import json
import logging
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

CATALOG_URL = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "catalog.json"

# Map SHL "keys" labels → single-letter type codes used in the API schema
KEYS_TO_CODE: dict[str, str] = {
    "Ability & Aptitude":           "A",
    "Biodata & Situational Judgment": "B",
    "Competencies":                 "C",
    "Development & 360":            "D",
    "Assessment Exercises":         "E",
    "Knowledge & Skills":           "K",
    "Personality & Behavior":       "P",
    "Simulations":                  "S",
}


def infer_test_type(keys: list[str]) -> str:
    """
    Return a comma-separated string of type codes for multi-key items,
    e.g. ["Knowledge & Skills", "Simulations"] → "K,S".
    Preserves the original key order so the primary type comes first.
    """
    codes = [KEYS_TO_CODE.get(k, "?") for k in keys if k in KEYS_TO_CODE]
    return ",".join(dict.fromkeys(codes))   # deduplicate while preserving order


def convert(raw: dict) -> dict:
    """Convert a raw catalog entry (from the SHL JSON) to internal format."""
    keys  = raw.get("keys") or []
    langs = raw.get("languages") or []

    return {
        "name":           raw["name"],
        "url":            raw["link"],        # canonical SHL URL
        "test_type":      infer_test_type(keys),
        "test_type_label": ", ".join(keys),
        "description":    (raw.get("description") or "").strip().replace("\r\n", " ").replace("\n", " "),
        "duration":       raw.get("duration") or "N/A",
        "remote_testing": "Yes" if raw.get("remote") == "yes" else "No",
        "adaptive_irt":   "Yes" if raw.get("adaptive") == "yes" else "No",
        "job_levels":     raw.get("job_levels") or [],
        "languages":      langs,
        "tags":           _build_tags(raw),
        "entity_id":      raw.get("entity_id", ""),
    }


def _build_tags(raw: dict) -> list[str]:
    """Derive searchable tags from name, description, keys and job levels."""
    name        = (raw.get("name") or "").lower()
    desc        = (raw.get("description") or "").lower()
    keys        = [k.lower() for k in (raw.get("keys") or [])]
    job_levels  = [j.lower() for j in (raw.get("job_levels") or [])]

    tags: list[str] = []

    # Programming languages / technologies — picked from name
    for tech in [
        "java", "python", "sql", "javascript", "typescript", ".net", "c#", "c++",
        "angular", "react", "spring", "aws", "docker", "kubernetes", "linux",
        "rust", "go", "r ", "excel", "word", "powerpoint", "hipaa", "sap",
    ]:
        if tech in name or tech in desc:
            tags.append(tech.strip())

    # Role families
    for family in [
        "leadership", "manager", "sales", "customer service", "contact center",
        "graduate", "entry", "engineering", "finance", "healthcare", "developer",
        "analyst", "admin", "safety", "data",
    ]:
        if family in desc or family in name:
            tags.append(family)

    tags.extend(keys)
    tags.extend(job_levels)
    return list(dict.fromkeys(tags))   # deduplicate


def fetch_catalog(url: str) -> list[dict]:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    # The SHL JSON sometimes has invalid control chars in description fields
    import json as _json
    return _json.loads(resp.text, strict=False)


def build(dry_run: bool = False) -> list[dict]:
    logger.info("Fetching catalog from %s …", CATALOG_URL)
    raw_items = fetch_catalog(CATALOG_URL)
    logger.info("Fetched %d raw items.", len(raw_items))

    converted = [convert(r) for r in raw_items if r.get("status") == "ok" and r.get("name")]

    # Stats
    by_type: dict[str, int] = {}
    for a in converted:
        for code in a["test_type"].split(","):
            by_type[code] = by_type.get(code, 0) + 1

    logger.info("Converted %d assessments.", len(converted))
    for code, count in sorted(by_type.items()):
        logger.info("  Type %-3s : %d", code, count)

    if not dry_run:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
            json.dump(converted, fh, indent=2, ensure_ascii=False)
        logger.info("Wrote %d assessments → %s", len(converted), OUTPUT_PATH)

    return converted


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build(dry_run=args.dry_run)
