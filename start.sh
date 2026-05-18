#!/usr/bin/env bash
# start.sh — used by Render/Railway as the start command.
# Ensures catalog.json exists before launching uvicorn.
set -e

DATA_DIR="$(dirname "$0")/data"
CATALOG="$DATA_DIR/catalog.json"

mkdir -p "$DATA_DIR"

if [ ! -f "$CATALOG" ]; then
  echo "catalog.json not found — seeding with known SHL assessments …"
  python -m scraper.seed_catalog
  echo "Attempting live scrape in background …"
  python -m scraper.scrape_catalog --force &   # best-effort; doesn't block startup
fi

echo "Starting uvicorn …"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --log-level info
