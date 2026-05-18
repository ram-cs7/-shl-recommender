"""
CatalogRetriever — loads catalog.json, embeds every assessment once at
startup, then serves fast cosine-similarity search via FAISS.

Embedding model : all-MiniLM-L6-v2  (22 MB, runs on CPU, ~50 ms/query)
"""

import json
import logging
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"
EMBED_MODEL   = "all-MiniLM-L6-v2"

TEST_TYPE_LABELS: dict[str, str] = {
    "A": "Ability / Aptitude",
    "B": "Biodata",
    "C": "Competency",
    "K": "Knowledge / Skills",
    "P": "Personality / Behavioural",
    "S": "Simulation",
}


class CatalogRetriever:
    def __init__(self):
        self.catalog: list[dict] = []
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._embeddings: Optional[np.ndarray] = None
        self._url_set: set[str] = set()
        self._name_map: dict[str, dict] = {}

    # ── Public ──────────────────────────────────────────────────────────────

    def build_index(self) -> None:
        """Load catalog and build FAISS inner-product index (= cosine on normalised vecs)."""
        if not CATALOG_PATH.exists():
            raise FileNotFoundError(
                f"Catalog not found at {CATALOG_PATH}. "
                "Run:  python -m scraper.scrape_catalog"
            )

        with CATALOG_PATH.open(encoding="utf-8") as fh:
            self.catalog = json.load(fh)

        if not self.catalog:
            raise ValueError("Catalog is empty — re-run the scraper.")

        logger.info("Embedding %d assessments …", len(self.catalog))
        self._model = SentenceTransformer(EMBED_MODEL)

        texts = [self._to_text(a) for a in self.catalog]
        self._embeddings = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        ).astype(np.float32)

        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(self._embeddings)

        # Fast lookup helpers
        self._url_set  = {a["url"] for a in self.catalog}
        self._name_map = {a["name"].lower(): a for a in self.catalog}

        logger.info("FAISS index ready (%d vectors, dim=%d).", self._index.ntotal, dim)

    def search(self, query: str, k: int = 15) -> list[dict]:
        """Return up to k catalog entries ordered by semantic relevance."""
        if self._index is None or self._model is None:
            raise RuntimeError("Index not built — call build_index() first.")

        q_vec = self._model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)

        scores, indices = self._index.search(q_vec, min(k, len(self.catalog)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.catalog):
                entry = dict(self.catalog[idx])
                entry["_score"] = float(score)
                results.append(entry)
        return results

    def get_by_names(self, names: list[str]) -> list[dict]:
        """Exact or fuzzy lookup by name — used for comparison queries."""
        results = []
        for name in names:
            key = name.lower().strip()
            # Exact match first
            if key in self._name_map:
                results.append(dict(self._name_map[key]))
                continue
            # Partial match fallback
            for catalog_key, assessment in self._name_map.items():
                if key in catalog_key or catalog_key in key:
                    results.append(dict(assessment))
                    break
        return results

    def is_valid_url(self, url: str) -> bool:
        return url in self._url_set

    def is_valid_name(self, name: str) -> bool:
        return name.lower() in self._name_map

    def get_by_name(self, name: str) -> Optional[dict]:
        return self._name_map.get(name.lower())

    def all_urls(self) -> set[str]:
        return self._url_set

    # ── Private ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_text(assessment: dict) -> str:
        """Concatenate all searchable fields into a single string for embedding."""
        parts = [
            assessment.get("name", ""),
            assessment.get("description", ""),
            assessment.get("test_type_label", ""),
            " ".join(assessment.get("job_levels", [])),
            " ".join(assessment.get("competencies", [])),
            " ".join(assessment.get("tags", [])),
        ]
        return " ".join(p for p in parts if p).strip()
