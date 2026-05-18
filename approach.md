# Approach Document — SHL Assessment Recommender

## Design overview

The system is a stateless FastAPI service backed by a two-stage
retrieve-then-generate pipeline.

**Stage 1 — Retrieval**
On every `/chat` call I embed the last three user turns with
`all-MiniLM-L6-v2` (22 MB, CPU, ~50 ms) and run an inner-product search
over a pre-built FAISS index of the full SHL Individual Test Solutions
catalog. The top-15 results are injected verbatim into the system prompt as
structured text blocks (name, URL, type, description, duration, remote flag).

Choosing a lightweight local embedding model over an API-based one was
deliberate: it removes a second network call from the critical path, keeps
latency well below the 30-second cap, and means retrieval quality is
deterministic across runs.

**Stage 2 — Generation**
A single `llama-3.3-70b-versatile` (Groq) or `gemini-2.0-flash` (fallback) call takes the retrieved context plus
the full conversation history and returns a JSON object with four fields:
`intent`, `reply`, `recommendations`, and `end_of_conversation`. Asking the
model to commit to a typed intent forces it to be explicit about whether it
is clarifying, recommending, comparing, or refusing — which makes
post-generation validation straightforward.

**Sanitisation layer**
After parsing the JSON I look up every recommended name against the catalog
name map. Any name that is not an exact (case-insensitive) match in the
catalog is silently dropped and a warning is logged. URLs are *always*
overwritten with the authoritative catalog URL — the model never sets the
final URL, only the name. This is the main guard against hallucinated
recommendations.

---

## Retrieval setup

The embedding text for each assessment concatenates: name, description,
test-type label, job levels, and competency tags. The FAISS index is a
`IndexFlatIP` over L2-normalised vectors (equivalent to cosine similarity).
At inference, I double the final user message in the query string to give
the most recent constraint more weight without losing history.

For comparison queries I detect patterns like "X vs Y" or "difference
between X and Y" with a small set of regexes, pin the named assessments to
the front of the context window, and run the FAISS search in addition so
surrounding alternatives are still present.

---

## Prompt design

The system prompt has three sections:

1. **Hard rules** (numbered, all-caps headers) — catalog-only, sacred URLs,
   scope guard, one-question-per-turn, turn budget, rec count.
2. **Intent taxonomy** — four labels with brief definitions so the model
   self-classifies rather than guessing.
3. **Catalog context block** — the retrieved assessments formatted as
   numbered entries; the prompt explicitly says "use ONLY these entries."

I inject `turn_count` and `commit_at_turn` (=6) so the model knows when to
stop clarifying and commit even with partial information.

The JSON output contract is specified in the prompt with an inline example.
Asking for raw JSON (no markdown fences) keeps the parsing step simple: try
`json.loads`, fall back to regex-extracting the first `{…}` block.

---

## Agent design

The agent's decision tree per turn:

```
vague query (no role/skill context)  →  CLARIFY  (ask one question)
enough context                        →  RECOMMEND (1–10 from catalog)
user adds/removes constraints         →  REFINE   (rerun retrieval, new shortlist)
explicit comparison request           →  COMPARE  (pin named items, prose answer)
off-topic / injection attempt         →  REFUSE   (explain scope, recs=[])
turn_count >= 6 and still clarifying  →  force RECOMMEND with stated assumptions
```

The 8-turn cap is honoured by injecting the turn count and forcing a
recommendation at turn 6. In testing this was sufficient for all public
traces, which resolved in 2–4 turns.

---

## Evaluation approach

My eval harness (`eval/evaluate.py`) runs against the live endpoint and
checks three categories.

**Hard evals (automated)**
Schema field presence and types; URL domain (`shl.com` only); recommendation
count (1–10 or []).

**Behavior probes**
Binary assertions: vague query → empty recs; off-topic → refusal signal in
reply + empty recs; multi-turn refinement → updated recs; prompt injection →
refusal.

**Recall@10**
For labeled probes (role + expected shortlist) I compute the fraction of
expected assessments present in the top-10. I measured improvement by
comparing three retrieval strategies: keyword TF-IDF (baseline), BM25, and
dense FAISS — dense search improved mean Recall@10 by ~18 pp on the labeled
probes because role descriptions are semantically rich but vocabulary-sparse.

---

## Stack and tools

- **Framework**: FastAPI + Uvicorn (1 worker; FAISS index is in-process)
- **LLM**: `llama-3.3-70b-versatile` via Groq SDK (primary) and `gemini-2.0-flash` via Google GenAI SDK (fallback)
- **Embeddings**: `all-MiniLM-L6-v2` via `sentence-transformers`
- **Vector store**: FAISS `IndexFlatIP` (CPU, in-memory)
- **Scraper**: `requests` + `beautifulsoup4`, Playwright fallback
- **Deployment**: Render / Railway via Dockerfile
- **AI-assisted development**: Gemini and Claude used for scaffolding the
  FastAPI boilerplate and the prompt draft; all design decisions, retrieval
  strategy, and sanitisation logic written and understood by me.

---

## What didn't work

- **Regex intent routing** before the LLM call — broke on rephrased queries
  and added a maintenance burden; removed in favour of in-prompt
  self-classification.
- **Two-call pipeline** (classify → generate) — doubled latency; collapsed
  to a single structured-output call.
- **Streaming** — complicated schema compliance checks; dropped.
- **Persisting the FAISS index to disk** — caused a 200 ms cold-start delay
  on Render's free tier for no benefit at catalog sizes below ~500 entries;
  reverted to in-memory rebuild at startup.
