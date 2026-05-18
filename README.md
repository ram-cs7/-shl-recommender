# SHL Assessment Recommender

A conversational agent that guides hiring managers from a vague role description
to a grounded shortlist of SHL Individual Test Solutions — in under 8 turns.

---

## Architecture

```
User  ──POST /chat──►  FastAPI
                           │
                    ┌──────▼──────┐
                    │  SHLAgent   │
                    └──┬──────┬───┘
                       │      │
              ┌────────▼──┐  ┌▼──────────────┐
              │ Retriever │  │ Groq / Gemini  │
              │  (FAISS)  │  │  llama-3.3-70b │
              └─────┬─────┘  └───────────────┘
                    │
              ┌─────▼──────┐
              │ catalog.json│  (pre-scraped from shl.com)
              └────────────┘
```

### Key design decisions

| Decision | Rationale |
|---|---|
| FAISS + sentence-transformers | Free, deterministic, no API cost, <60 ms/query on CPU |
| Stateless POST /chat | Matches evaluator contract; no session store needed |
| Structured JSON output from LLM | Prevents schema drift; easier to sanitise |
| Post-generation URL/name validation | Zero tolerance for hallucinated catalog entries |
| Turn-count injection into system prompt | Forces recommendation by turn 6, avoids 8-turn cap |
| Scraper-first, Playwright fallback | Works on SHL's static pages; JS-render fallback if needed |

---

## Quick start

### 1. Clone & install

```bash
git clone <your-repo>
cd shl-recommender
pip install -r requirements.txt
```

### 2. Set your API keys (Groq + Gemini)

```bash
cp .env.example .env
# Edit .env and paste your key
export $(cat .env | xargs)
```

### 3. Scrape the SHL catalog (run once)

```bash
python -m scraper.scrape_catalog
# Writes data/catalog.json
# If JS rendering needed: SHL_USE_PLAYWRIGHT=1 python -m scraper.scrape_catalog
```

### 4. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Run evaluation suite

```bash
python -m eval.evaluate
# Against deployed service:
# BASE_URL=https://your-app.railway.app python -m eval.evaluate
```

---

## API

### `GET /health`
```json
{"status": "ok"}
```

### `POST /chat`

**Request**
```json
{
  "messages": [
    {"role": "user",      "content": "Hiring a Java developer, mid-level"},
    {"role": "assistant", "content": "What key skills should the role require?"},
    {"role": "user",      "content": "Strong problem-solving and stakeholder communication"}
  ]
}
```

**Response**
```json
{
  "reply": "Here are 4 assessments that fit a mid-level Java developer …",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/…", "test_type": "K"},
    {"name": "OPQ32r",       "url": "https://www.shl.com/…", "test_type": "P"}
  ],
  "end_of_conversation": false
}
```

`recommendations` is `[]` when the agent is clarifying or refusing.

---

## Deployment (Railway / Render)

1. Push the repo (with `data/catalog.json` committed).
2. Set `GROQ_API_KEY` (and optionally `GEMINI_API_KEY` for fallback) as environment variables in the dashboard.
3. The platform builds via `Dockerfile`.
4. `/health` cold-start: up to 2 min; subsequent calls: <2 s.

---

## Evaluation approach

See `eval/evaluate.py` for the full harness. It tests:

- **Schema compliance** — every field present, correct types
- **Catalog integrity** — all URLs start with `https://www.shl.com`
- **Behavior probes** — vague query → clarify, off-topic → refuse, context → recommend
- **Recall@10** — labeled test cases measure overlap with expected shortlists

---

## What didn't work

- **Rule-based routing** (regex intent detection) — broke on rephrased queries; replaced with LLM intent classification inside the JSON response.
- **Streaming responses** — complicated schema compliance; dropped in favour of single-call JSON.
- **Caching embeddings to disk** — added 200 ms startup overhead on Render; reverted to in-memory rebuild (fast enough at <200 assessments).
