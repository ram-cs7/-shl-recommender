.PHONY: install scrape seed serve eval lint clean

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# ── Catalog ───────────────────────────────────────────────────────────────────
scrape:
	python -m scraper.scrape_catalog

scrape-playwright:
	SHL_USE_PLAYWRIGHT=1 python -m scraper.scrape_catalog

seed:
	python -m scraper.seed_catalog --force

# Attempt real scrape; fall back to seed if it fails
catalog: scrape
	@if [ ! -s data/catalog.json ]; then \
	  echo "Scrape returned nothing — using seed catalog"; \
	  python -m scraper.seed_catalog; \
	fi

# ── Server ────────────────────────────────────────────────────────────────────
serve:
	uvicorn app.main:app --reload --port 8000

serve-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# ── Evaluation ────────────────────────────────────────────────────────────────
eval:
	python -m eval.evaluate

eval-remote:
	BASE_URL=$(URL) python -m eval.evaluate

# ── Docker ───────────────────────────────────────────────────────────────────
docker-build:
	docker build -t shl-recommender .

docker-run:
	docker run -p 8000:8000 \
	  -e GROQ_API_KEY=$(GROQ_API_KEY) \
	  -e GEMINI_API_KEY=$(GEMINI_API_KEY) \
	  -v $(PWD)/data:/app/data \
	  shl-recommender

# ── Lint ──────────────────────────────────────────────────────────────────────
lint:
	python -m py_compile app/main.py app/agent.py app/retriever.py app/prompts.py
	@echo "Syntax OK"

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
