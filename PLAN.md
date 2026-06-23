# Mini Search Engine — Implementation Plan

A domain-specific search engine for **research papers**, built from scratch in Python. No Elasticsearch or Lucene — every core IR component is implemented by hand to demonstrate understanding of crawling, indexing, graph algorithms, and ranking.

---

## Table of Contents

1. [Goals & Success Criteria](#1-goals--success-criteria)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Phase 0 — Environment & Scaffolding](#phase-0--environment--scaffolding)
6. [Phase 1 — Data Acquisition (Crawler)](#phase-1--data-acquisition-crawler)
7. [Phase 2 — Tokenizer & Text Processing](#phase-2--tokenizer--text-processing)
8. [Phase 3 — Inverted Index (From Scratch)](#phase-3--inverted-index-from-scratch)
9. [Phase 4 — Citation Graph & PageRank](#phase-4--citation-graph--pagerank)
10. [Phase 5 — BM25 + PageRank Hybrid Ranking](#phase-5--bm25--pagerank-hybrid-ranking)
11. [Phase 6 — Query Interface & Pagination](#phase-6--query-interface--pagination)
12. [Phase 7 — Hosting & Real-World Deployment](#phase-7--hosting--real-world-deployment)
13. [Testing Strategy](#testing-strategy)
14. [Performance Targets](#performance-targets)
15. [Risks & Mitigations](#risks--mitigations)
16. [Timeline Estimate](#timeline-estimate)
17. [Interview Talking Points](#interview-talking-points)

---

## 1. Goals & Success Criteria

### Primary Goals

| Goal | Description |
|------|-------------|
| **Crawl real data** | Ingest ≥ 10,000 research papers (title, abstract, authors, categories, citations) |
| **Custom inverted index** | Term dictionary + postings lists on disk; no off-the-shelf search library |
| **Hybrid ranking** | BM25 (lexical relevance) combined with PageRank (graph authority) |
| **Queryable API** | REST endpoint with paginated results, sub-second latency on indexed corpus |
| **Hosted & demo-ready** | Public URL where anyone can search the corpus |

### Non-Goals (Scope Control)

- Full PDF text extraction (start with metadata + abstract only)
- Real-time incremental indexing (batch rebuild is fine for v1)
- Multi-language support (English only in v1)
- Distributed crawling or sharded index (single-machine architecture)

### Definition of Done

- [ ] `python -m src.cli crawl` fetches and stores papers
- [ ] `python -m src.cli index` builds inverted index + PageRank scores
- [ ] `GET /search?q=transformer&page=1&size=10` returns ranked, paginated JSON
- [ ] README documents setup, architecture, and design decisions
- [ ] Deployed instance searchable on live data

---

## 2. Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Crawler   │────▶│  Document    │────▶│   Tokenizer     │
│  (arXiv API)│     │  Store (JSON)│     │  + Normalizer   │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                     ┌─────────────────────────────┼─────────────────────────────┐
                     ▼                             ▼                             ▼
              ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
              │  Inverted   │              │  Citation   │              │  Document   │
              │  Index      │              │  Graph      │              │  Lengths    │
              │  (postings) │              │  (edges)    │              │  (for BM25) │
              └──────┬──────┘              └──────┬──────┘              └──────┬──────┘
                     │                            │                            │
                     └────────────────────────────┼────────────────────────────┘
                                                  ▼
                                          ┌───────────────┐
                                          │    Ranker     │
                                          │ BM25 × α +    │
                                          │ PageRank × β  │
                                          └───────┬───────┘
                                                  ▼
                                          ┌───────────────┐
                                          │  FastAPI      │
                                          │  /search      │
                                          │  (pagination) │
                                          └───────────────┘
```

### Data Flow

1. **Ingest**: Crawler pulls paper metadata from arXiv API (respecting rate limits).
2. **Store**: Each paper saved as a JSON record with stable `doc_id`.
3. **Index**: Tokenizer processes title (weight ×3) and abstract (weight ×1); builds postings lists.
4. **Graph**: Citation/reference edges extracted where available; PageRank computed offline.
5. **Serve**: Query tokenized → postings intersected/unioned → BM25 scored → blended with PageRank → paginated response.

---

## 3. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Rich IR ecosystem, fast prototyping |
| Env | `venv` + `pip` | Isolated deps, no Docker required for dev |
| HTTP client | `httpx` | Async-capable, clean API for arXiv |
| Web framework | FastAPI | Auto OpenAPI docs, async, production-ready |
| Serialization | `orjson` | Fast JSON read/write for document store |
| Storage | Flat files + SQLite | Simple, portable, no external DB server |
| CLI | `typer` | Typed CLI for crawl / index / serve |
| Tests | `pytest` | Standard Python testing |
| Deployment | Railway / Render / Fly.io | Free tier, easy Python deploy |

---

## 4. Project Structure

```
mini_search_engine/
├── README.md
├── PLAN.md
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── src/
│   ├── __init__.py
│   ├── config.py                 # Settings via env vars
│   │
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── arxiv_client.py       # arXiv API wrapper with rate limiting
│   │   ├── fetcher.py            # Batch fetch + dedup
│   │   └── models.py             # Paper dataclass
│   │
│   ├── tokenizer/
│   │   ├── __init__.py
│   │   ├── tokenizer.py          # Regex + lowercase + stopword removal
│   │   ├── stemmer.py            # Optional Porter stemmer (hand-rolled or NLTK)
│   │   └── stopwords.py          # English stopword list
│   │
│   ├── index/
│   │   ├── __init__.py
│   │   ├── inverted_index.py     # Term → postings list builder & loader
│   │   ├── postings.py           # Posting: (doc_id, term_freq, field_flags)
│   │   ├── dictionary.py         # Lexicon on disk (term → offset in postings file)
│   │   └── builder.py            # Offline index construction pipeline
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── citation_graph.py     # Adjacency list from paper references
│   │   └── pagerank.py           # Power iteration PageRank
│   │
│   ├── ranker/
│   │   ├── __init__.py
│   │   ├── bm25.py               # Okapi BM25 implementation
│   │   └── hybrid.py             # score = α·BM25_norm + β·PageRank_norm
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   └── engine.py             # Query parsing → retrieval → ranking
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   ├── routes.py             # /search, /health, /stats
│   │   └── schemas.py            # Pydantic response models
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py               # crawl | index | serve | stats
│
├── data/                         # Gitignored — local corpus
│   ├── raw/                      # Raw API responses
│   ├── papers/                   # Normalized JSON per paper
│   ├── index/                    # Serialized inverted index
│   │   ├── dictionary.bin
│   │   ├── postings.bin
│   │   └── metadata.json         # doc count, avg dl, idf cache
│   └── pagerank/                 # Precomputed PageRank scores
│       └── scores.json
│
├── tests/
│   ├── test_tokenizer.py
│   ├── test_inverted_index.py
│   ├── test_bm25.py
│   ├── test_pagerank.py
│   ├── test_hybrid_ranker.py
│   └── test_search_api.py
│
└── scripts/
    ├── setup_venv.ps1            # Windows venv bootstrap
    └── setup_venv.sh             # Unix venv bootstrap
```

---

## Phase 0 — Environment & Scaffolding

**Duration**: 0.5 day

### Tasks

1. Create `requirements.txt` with pinned core deps.
2. Add `.gitignore` (venv, `data/`, `__pycache__`, `.env`).
3. Implement `src/config.py` with paths and tunable constants (BM25 k1/b, α/β weights).
4. Scaffold CLI entry points: `crawl`, `index`, `serve`.
5. Add `pytest` + one smoke test.

### Deliverable

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

All green (even if most tests are placeholders).

---

## Phase 1 — Data Acquisition (Crawler)

**Duration**: 2 days

### Data Source: arXiv API

- **Endpoint**: `http://export.arxiv.org/api/query`
- **Fields**: `id`, `title`, `summary` (abstract), `author`, `category`, `published`, `link`
- **Rate limit**: 1 request / 3 seconds (built into client)
- **Seed queries**: `cat:cs.AI`, `cat:cs.CL`, `cat:cs.LG`, `cat:cs.IR` to build a CS-focused corpus

### Paper Model

```python
@dataclass
class Paper:
    doc_id: str          # arXiv ID, e.g. "2301.00001"
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published: str       # ISO date
    pdf_url: str
    references: list[str]  # arXiv IDs if extractable; empty OK for v1
```

### Citation Data Strategy

arXiv API does not expose citation graphs directly. Options (pick one for v1):

| Option | Effort | Quality |
|--------|--------|---------|
| **A. Semantic Scholar API** | Medium | Real citation edges |
| **B. Co-citation proxy** | Low | Papers sharing categories co-linked |
| **C. Manual seed graph** | Low | Demo only |

**Recommendation**: Start with **Option B** (category co-occurrence + random walk prior) for PageRank demo, then upgrade to **Option A** for interview depth.

### Crawler Features

- [ ] Resumable fetch (skip already-stored `doc_id`)
- [ ] Exponential backoff on HTTP errors
- [ ] Progress logging (`tqdm`)
- [ ] Configurable max papers (`--max-papers 10000`)

### Deliverable

`data/papers/` contains ≥ 10,000 JSON files; `python -m src.cli stats` reports corpus size.

---

## Phase 2 — Tokenizer & Text Processing

**Duration**: 1 day

### Pipeline

```
raw text → lowercase → regex tokenize → stopword filter → optional stem
```

### Tokenizer Spec

| Rule | Detail |
|------|--------|
| Token pattern | `[a-z0-9]+` after lowercasing |
| Min length | 2 characters |
| Stopwords | ~130 English function words (custom list, no external lib required) |
| Stemming | Porter stemmer (implement or use `nltk` — document choice in README) |
| Field weighting | Title tokens counted 3× in term frequency during indexing |

### Deliverable

Unit tests confirming:
- `"Transformers are ALL you need!"` → `["transform", "need"]` (with stemming)
- Empty / punctuation-only input → `[]`

---

## Phase 3 — Inverted Index (From Scratch)

**Duration**: 3 days

This is the **core technical artifact**. No Whoosh, no Elasticsearch.

### Index Components

#### 3.1 Term Dictionary (Lexicon)

Sorted map: `term → (postings_offset, postings_count, document_frequency)`

Stored as a binary file or JSON for simplicity in v1; upgrade to front-coded lexicon later.

#### 3.2 Postings List

For each term, a sorted list of postings:

```python
@dataclass
class Posting:
    doc_id: str
    term_freq: int      # Weighted (title ×3 + abstract ×1)
    positions: list[int]  # Optional for phrase queries (v2)
```

On disk: variable-byte or simple struct packing (`struct.pack`).

#### 3.3 Index Metadata

```json
{
  "num_docs": 10234,
  "avg_doc_length": 187.4,
  "total_terms": 84321,
  "built_at": "2026-06-23T12:00:00Z"
}
```

### Build Algorithm

```
for each paper in data/papers/:
    tokens_title = tokenizer(title) × 3
    tokens_abstract = tokenizer(abstract)
    merge → term_freq map
    for each (term, tf) in term_freq:
        append Posting(doc_id, tf) to in-memory postings[term]

sort each postings list by doc_id
write dictionary + postings to disk
compute IDF for all terms: log((N - df + 0.5) / (df + 0.5) + 1)
```

### Query Retrieval

For query `q = [t1, t2, ..., tk]`:

1. Look up postings for each term (skip OOV terms).
2. **OR retrieval** (union doc IDs) for v1; AND for precision mode (v2).
3. Pass candidate doc IDs to ranker.

### Deliverable

- Index builds in < 5 min for 10K docs on laptop
- `lookup("transformer")` returns sorted postings in O(log n + k)

---

## Phase 4 — Citation Graph & PageRank

**Duration**: 2 days

### Graph Construction

```python
# Adjacency: paper_id → [referenced_paper_ids]
graph: dict[str, list[str]]
```

For v1 with co-citation proxy:
- Connect papers that share ≥ 2 arXiv categories (undirected edge).
- Add self-loop + damping to ensure ergodicity.

### PageRank Algorithm

Classic power iteration:

```
PR(p) = (1 - d) / N + d × Σ PR(q) / outdegree(q)
```

| Parameter | Default |
|-----------|---------|
| Damping `d` | 0.85 |
| Max iterations | 100 |
| Convergence threshold | 1e-6 L1 norm delta |

Store result: `data/pagerank/scores.json` → `{doc_id: float}`.

### Deliverable

- PageRank converges in < 100 iterations
- Top-10 PageRank papers are plausible (survey papers, foundational work)
- Unit test on 4-node toy graph with known expected scores

---

## Phase 5 — BM25 + PageRank Hybrid Ranking

**Duration**: 2 days

### BM25 (Okapi)

```
IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)

score(D, Q) = Σ IDF(t) × (tf(t,D) × (k1 + 1)) / (tf(t,D) + k1 × (1 - b + b × |D|/avgdl))
```

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `k1` | 1.5 | Term frequency saturation |
| `b` | 0.75 | Length normalization |

### Hybrid Score

```
final_score(D, Q) = α × normalize(BM25(D, Q)) + β × normalize(PageRank(D))
```

| Parameter | Default |
|-----------|---------|
| `α` | 0.7 |
| `β` | 0.3 |

Normalization: min-max over candidate set per query (prevents scale mismatch).

### Tunable via Config

Expose `α`, `β`, `k1`, `b` in `.env` for experimentation without code changes.

### Deliverable

- Query `"attention mechanism transformer"` ranks Vaswani et al. (or similar) highly
- Hybrid beats BM25-only on authority queries (e.g., `"deep learning survey"`)

---

## Phase 6 — Query Interface & Pagination

**Duration**: 2 days

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/search` | Main search endpoint |
| GET | `/health` | Liveness check |
| GET | `/stats` | Corpus + index statistics |
| GET | `/docs` | Swagger UI (auto via FastAPI) |

### `/search` Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Query string |
| `page` | int | 1 | Page number (1-indexed) |
| `size` | int | 10 | Results per page (max 50) |

### Response Schema

```json
{
  "query": "transformer attention",
  "total_hits": 342,
  "page": 1,
  "size": 10,
  "total_pages": 35,
  "results": [
    {
      "doc_id": "1706.03762",
      "title": "Attention Is All You Need",
      "abstract": "...",
      "authors": ["Vaswani", "..."],
      "score": 0.94,
      "bm25_score": 0.91,
      "pagerank_score": 0.03,
      "pdf_url": "https://arxiv.org/pdf/1706.03762"
    }
  ],
  "took_ms": 42
}
```

### Pagination Logic

```
offset = (page - 1) × size
candidates = rank_all(query)          # full ranked list
return candidates[offset : offset + size]
```

For large result sets, cap ranked list at 1000 docs before pagination (document in API).

### Optional: Simple Web UI

Minimal HTML page with search box + result cards (single `static/index.html` served by FastAPI). Nice for demo, not required for v1 API.

### Deliverable

- API returns correct pagination metadata
- p95 latency < 200ms for 10K doc corpus
- Integration tests with `httpx.AsyncClient`

---

## Phase 7 — Hosting & Real-World Deployment

**Duration**: 1 day

### Pre-Deploy Checklist

- [ ] Index + PageRank files bundled or built in CI
- [ ] `PORT` env var respected
- [ ] Health check endpoint configured
- [ ] Corpus subset committed OR downloaded on first boot (prefer pre-built index artifact)

### Recommended Platform: Railway or Render

1. Push repo to GitHub.
2. Connect Railway/Render project.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. Upload pre-built `data/index/` as part of repo (under size limits) or use object storage.

### Corpus Size Management

| Docs | Index Size (est.) | Strategy |
|------|-------------------|----------|
| 10K | ~50 MB | Commit to repo or release artifact |
| 100K | ~500 MB | S3/R2 bucket, download on boot |

### Deliverable

Public URL, e.g. `https://mini-search-engine.up.railway.app/search?q=bert`

---

## Testing Strategy

| Layer | Test Type | Examples |
|-------|-----------|----------|
| Tokenizer | Unit | Stemming, stopwords, edge cases |
| Inverted Index | Unit | Build, lookup, df/idf correctness |
| BM25 | Unit | Known score on toy corpus |
| PageRank | Unit | 4-node graph, convergence |
| Hybrid Ranker | Unit | α/β weighting, normalization |
| Search Engine | Integration | End-to-end query → ranked results |
| API | Integration | Pagination, empty query, OOV query |
| Crawler | Mock | Mock httpx responses, rate limit |

Run: `pytest -v --cov=src`

---

## Performance Targets

| Metric | Target (10K docs) |
|--------|-------------------|
| Index build time | < 5 minutes |
| Query latency (p95) | < 200 ms |
| Memory at serve time | < 512 MB |
| Crawl throughput | ~1 paper/sec (rate-limited) |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No real citation data from arXiv | Weak PageRank signal | Use Semantic Scholar API or co-citation proxy |
| Index too large for free hosting | Deploy fails | Ship 10K subset; document scaling path |
| arXiv rate limits slow crawl | Delays ingest | Resume-able crawler; crawl overnight |
| Stemming hurts recall | Missed results | Make stemming optional via config |
| BM25-only queries dominate | PageRank invisible | Tune α/β; show both scores in API response |

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 0 — Scaffolding | 0.5 day | 0.5 day |
| 1 — Crawler | 2 days | 2.5 days |
| 2 — Tokenizer | 1 day | 3.5 days |
| 3 — Inverted Index | 3 days | 6.5 days |
| 4 — PageRank | 2 days | 8.5 days |
| 5 — Hybrid Ranker | 2 days | 10.5 days |
| 6 — API + Pagination | 2 days | 12.5 days |
| 7 — Deploy | 1 day | 13.5 days |
| Buffer + polish | 1.5 days | **~15 days** |

---

## Interview Talking Points

When presenting this project, emphasize:

1. **Why inverted index?** — O(1) term lookup + O(k) postings scan vs. linear doc scan.
2. **BM25 intuition** — TF saturation + length normalization; why not raw TF-IDF.
3. **PageRank intuition** — Random surfer model; authority vs. relevance.
4. **Hybrid trade-off** — Lexical match finds relevant docs; graph signal boosts authoritative surveys.
5. **Pagination at rank time** — Full ranking then slice; trade-off vs. WAND/max-score optimization.
6. **Scaling path** — Sharding by term range, skip lists, compressed postings (PForDelta), MapReduce index build.

---

## Next Steps After v1

- [ ] Phrase queries with positional index
- [ ] Query expansion (pseudo-relevance feedback)
- [ ] Learning-to-rank on click data
- [ ] PDF full-text extraction pipeline
- [ ] Incremental index updates
- [ ] Benchmark against Elasticsearch on same corpus
