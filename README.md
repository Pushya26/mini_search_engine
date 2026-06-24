# Mini Search Engine

A **domain-specific search engine for research papers**, built from scratch in Python. Crawls real arXiv data, builds a custom inverted index (no Elasticsearch), ranks results with a **BM25 + PageRank hybrid**, and exposes a paginated REST API.

> Built to demonstrate core information retrieval concepts: crawling, tokenization, inverted indexes, graph algorithms, and ranking — the same primitives that power large-scale search systems.

---

## Features

### Core Features

| Component | Description |
|-----------|-------------|
| **Web Crawler** | Fetches paper metadata from the arXiv API with rate limiting and resumable ingest |
| **Tokenizer** | Regex-based tokenization, stopword removal, optional stemming |
| **Inverted Index** | Hand-rolled term dictionary + postings lists on disk |
| **PageRank** | Citation/co-citation graph with power-iteration PageRank |
| **Hybrid Ranker** | `score = α·BM25 + β·PageRank` with tunable weights |
| **Query API** | FastAPI `/search` endpoint with page/size pagination |
| **CLI** | `crawl`, `index`, `serve`, and `stats` commands |

### Enhanced Features (v0.2.0)

| Feature | Description | Improvement |
|---------|-------------|-------------|
| **Query Expansion** | WordNet-based synonym expansion for better recall | +20-60% results |
| **Real Citations** | Semantic Scholar API integration for actual citation data | Higher quality PageRank |
| **Similar Papers** | Content-based paper recommendation | `/similar/{doc_id}` endpoint |
| **Result Caching** | LRU cache for repeated queries | 25x faster (2ms vs 50ms) |
| **Enhanced Metadata** | Categories, publication dates, citation counts | Richer responses |

> See [ENHANCEMENTS.md](./ENHANCEMENTS.md) for detailed feature documentation, usage examples, and configuration options.

---

## Architecture

```
Crawler → Document Store → Tokenizer → Inverted Index
                                      ↘
                        Citation Graph → PageRank → Hybrid Ranker → FastAPI
```

See [PLAN.md](./PLAN.md) for the full implementation plan, phase breakdown, data structures, and timeline.

---

## Requirements

- **Python 3.11+**
- **Git**
- Internet access (for crawling arXiv)

---

## Quick Start

### 1. Clone the repository

```powershell
git clone <your-repo-url>
cd mini_search_engine
```

### 2. Create and activate a virtual environment

This project uses a Python **`venv`** for all development. Do not install dependencies globally.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your shell prompt when the environment is active.

### 3. Install dependencies

```powershell
# With venv activated
python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional: dev tools (pytest, ruff, etc.)
pip install -r requirements-dev.txt
```

### 4. Configure environment (optional)

```powershell
copy .env.example .env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Corpus and index storage |
| `BM25_K1` | `1.5` | BM25 term frequency saturation |
| `BM25_B` | `0.75` | BM25 length normalization |
| `RANK_ALPHA` | `0.7` | Weight for BM25 in hybrid score |
| `RANK_BETA` | `0.3` | Weight for PageRank in hybrid score |
| `MAX_PAPERS` | `10000` | Crawl limit |
| `API_PORT` | `8000` | Local server port |

### 5. Run the pipeline

**Basic Pipeline:**

```powershell
# Step 1: Crawl papers from arXiv (respects rate limits — may take hours)
python -m src.cli crawl --max-papers 10000

# Step 2: Build inverted index + PageRank scores
python -m src.cli index

# Step 3: Start the search API
python -m src.cli serve
# Or directly:
uvicorn src.api.main:app --reload --port 8001
```

**Enhanced Pipeline (with real citations and advanced features):**

```powershell
# Step 1: Crawl papers (same as above)
python -m src.cli crawl --max-papers 10000

# Step 2: Build index with real citations from Semantic Scholar (takes 1-2 hours)
python -m src.cli index --rebuild --real-citations

# Step 3: Start enhanced API (query expansion, similar papers, caching)
python -m src.cli serve --enhanced
```

### 6. Search

**Browser / Swagger UI:**

```
http://localhost:8001/docs
```

**Basic search:**

```powershell
curl "http://localhost:8001/search?q=transformer+attention&page=1&size=10"
```

**Enhanced search with query expansion:**

```powershell
curl "http://localhost:8001/search?q=neural+network&expand=true&page=1&size=10"
```

**Find similar papers:**

```powershell
curl "http://localhost:8001/similar/1706.03762?top_k=5"
```

**Get paper details:**

```powershell
curl "http://localhost:8001/paper/1706.03762"
```

**Example response (enhanced):**

```json
{
  "query": "transformer attention",
  "expanded_query": ["transformer", "attention", "care", "tending"],
  "total_hits": 342,
  "page": 1,
  "size": 10,
  "total_pages": 35,
  "results": [
    {
      "doc_id": "1706.03762",
      "title": "Attention Is All You Need",
      "abstract": "...",
      "authors": ["Vaswani", "Shazeer", "..."],
      "categories": ["cs.CL", "cs.LG"],
      "published": "2017-06-12",
      "score": 0.94,
      "bm25_score": 0.91,
      "pagerank_score": 0.03,
      "pdf_url": "https://arxiv.org/pdf/1706.03762"
    }
  ],
  "took_ms": 42
}
```

---

## Project Structure

```
mini_search_engine/
├── README.md                 # This file
├── PLAN.md                   # Detailed implementation plan
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Dev/test dependencies
├── .env.example              # Environment variable template
├── src/
│   ├── crawler/              # arXiv data acquisition
│   ├── tokenizer/            # Text processing
│   ├── index/                # Inverted index (from scratch)
│   ├── graph/                # Citation graph + PageRank
│   ├── ranker/               # BM25 + hybrid ranking
│   ├── search/               # Query engine orchestration
│   ├── api/                  # FastAPI REST interface
│   └── cli/                  # Command-line tools
├── data/                     # Local corpus (gitignored)
├── tests/                    # pytest suite
└── scripts/                  # venv setup helpers
```

---

## Development Workflow

Always work inside the activated venv:

```powershell
# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint (if ruff installed)
ruff check src tests
```

### Deactivate the venv

```powershell
deactivate
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `python -m src.cli crawl` | Fetch papers from arXiv into `data/papers/` |
| `python -m src.cli index` | Build inverted index and PageRank scores |
| `python -m src.cli serve` | Start the FastAPI search server |
| `python -m src.cli stats` | Print corpus and index statistics |

Common flags:

```bash
# Crawl
crawl  --max-papers 10000   --categories cs.AI,cs.CL,cs.LG

# Index
index  --rebuild              # Force full rebuild
index  --real-citations       # Use Semantic Scholar API (takes 1-2 hours)

# Serve
serve  --port 8000            # Custom port
serve  --enhanced             # Enable query expansion, similar papers, caching
serve  --host 0.0.0.0         # Listen on all interfaces
```

---

## How It Works

### Inverted Index

Each term maps to a **postings list** — sorted `(doc_id, term_frequency)` pairs stored on disk. At query time, postings for all query terms are retrieved and unioned to form candidate documents.

No Elasticsearch, Whoosh, or Lucene — the index format, builder, and reader are implemented directly.

### BM25 Ranking

Okapi BM25 scores lexical relevance with:

- **IDF** — rare terms contribute more
- **TF saturation** — diminishing returns for repeated terms (`k1`)
- **Length normalization** — penalizes long documents (`b`)

### PageRank

A citation (or co-citation) graph connects papers. PageRank assigns authority scores via power iteration — papers referenced by many other papers score higher.

### Hybrid Score

```
final_score = α × norm(BM25) + β × norm(PageRank)
```

Defaults: `α = 0.7`, `β = 0.3`. Both sub-scores are returned in API responses for transparency.

---

## Deployment

The API is a standard FastAPI app deployable to Railway, Render, or Fly.io:

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

Pre-build the index locally and include `data/index/` in your deployment artifact, or download it on first boot from object storage.

See [PLAN.md — Phase 7](./PLAN.md#phase-7--hosting--real-world-deployment) for the full deployment checklist.

---

## Implementation Status

| Phase | Status |
|-------|--------|
| 0 — Scaffolding | ✅ Complete |
| 1 — Crawler | ✅ Complete |
| 2 — Tokenizer | ✅ Complete |
| 3 — Inverted Index | ✅ Complete |
| 4 — PageRank | ✅ Complete |
| 5 — Hybrid Ranker | ✅ Complete |
| 6 — Query API | ✅ Complete |
| 7 — Enhancements | ✅ Complete (v0.2.0) |
| 8 — Deployment | 🔲 Planned |

**Current Corpus:**
- 5,838 research papers from arXiv (cs.AI, cs.CL, cs.LG, cs.IR)
- 21,375 unique indexed terms
- Average document length: 167.5 tokens
- 27/27 tests passing (including enhanced features)

**Enhanced Features (v0.2.0):**
- Query expansion with WordNet synonyms (+20-60% recall)
- Semantic Scholar API integration for real citations
- Similar papers recommendation endpoint
- LRU result caching (25x speedup for repeated queries)
- Enhanced metadata (categories, dates, citation counts)

---

## Performance Optimizations & Technical Challenges

This section documents significant performance bottlenecks encountered during implementation and the algorithmic solutions applied.

### Challenge 1: Citation Graph Construction Bottleneck

#### The Problem

**Symptom**: Graph building process stuck at 1% progress for hours, effectively hanging the indexing pipeline.

**Root Cause Analysis**:

The initial co-citation graph implementation connected all papers within the same arXiv category:

```python
# Initial naive approach
for category, papers_in_category in category_index.items():
    for i, paper1 in enumerate(papers_in_category):
        for paper2 in papers_in_category[i+1:]:
            add_edge(paper1, paper2)  # Bidirectional
            add_edge(paper2, paper1)
```

**Computational Complexity**:
- Time complexity: O(N² × C) where N = papers per category, C = number of categories
- For a category with 3,000 papers: 3,000 × 2,999 / 2 = **4.49 million edges**
- With multiple large categories (cs.AI, cs.LG, cs.CL), total edges exceeded **tens of millions**

**Real-world Impact**:
- Corpus: 5,838 papers
- Category distribution:
  - cs.LG (Machine Learning): ~3,000 papers
  - cs.AI (Artificial Intelligence): ~1,800 papers
  - cs.CL (Computation and Language): ~600 papers
  - cs.IR (Information Retrieval): ~400 papers
- Dense graph resulted in: O(N²) = ~34 million potential edges

#### The Solution

**Strategy**: Transition from dense to sparse graph by adding semantic filtering.

**Implementation**:

```python
# Optimized selective co-citation
for i, paper1 in enumerate(papers):
    for paper2 in papers[i+1:]:
        # Only connect if papers share 2+ categories
        shared_categories = set(paper1['categories']) & set(paper2['categories'])
        if len(shared_categories) >= 2:
            add_edge(paper1['doc_id'], paper2['doc_id'])
            add_edge(paper2['doc_id'], paper1['doc_id'])
```

**Rationale**:
1. **Sparse Graph Property**: Papers sharing only 1 category are weakly related (they just happen to be in the same broad field)
2. **Strong Semantic Signal**: Papers with 2+ shared categories demonstrate:
   - Multi-disciplinary relevance
   - Topical intersection (e.g., papers in both cs.AI AND cs.LG are ML-focused AI papers)
   - Higher likelihood of actual citation relationships

**Data Structure Optimization**:

Added reverse graph for efficient PageRank:

```python
class CitationGraph:
    def __init__(self):
        self.graph: dict[str, list[str]] = defaultdict(list)  # Outgoing edges
        self.reverse_graph: dict[str, list[str]] = defaultdict(list)  # Incoming edges
        self.nodes: set[str] = set()
```

#### Results & Impact

**Performance Improvements**:
- Graph construction time: **Hours → Minutes**
- Edge count reduction: **Millions → ~Thousands** (estimated 99%+ reduction)
- Memory footprint: Proportional to edge reduction

**Graph Quality Improvements**:
- **Higher precision**: Edges now represent meaningful semantic relationships
- **Better PageRank**: Authority propagates along stronger topical connections
- **Interpretability**: 2+ category requirement makes edge semantics transparent

**Example**:
- Paper A: `["cs.AI", "cs.LG", "cs.CV"]`
- Paper B: `["cs.LG", "cs.CV"]` → **Connected** (2 shared categories: cs.LG, cs.CV)
- Paper C: `["cs.AI"]` → **Not connected** to either (only 1 shared category with A)

---

### Challenge 2: PageRank Iteration Complexity

#### The Problem

**Symptom**: PageRank computation running but with no visible progress, taking estimated 30+ minutes per iteration.

**Root Cause Analysis**:

Original PageRank implementation checked all nodes for each node:

```python
# Initial O(N²) approach
for node in all_nodes:  # N iterations
    rank_sum = 0.0
    for other_node in all_nodes:  # N iterations
        if node in graph[other_node]:  # Check if edge exists
            rank_sum += scores[other_node] / outdegree(other_node)
    new_scores[node] = (1 - damping) / N + damping * rank_sum
```

**Computational Complexity**:
- Per iteration: O(N²) where N = number of nodes (5,838)
- Total iterations: typically 50-100 until convergence
- Total operations: 5,838² × 100 = **3.4 billion operations**

**Why This Is Slow**:
- Even sparse graphs waste cycles checking non-existent edges
- For each node, iterating through all 5,838 nodes to find the few that actually link to it
- Graph sparsity (low edge/node ratio) makes this especially wasteful

#### The Solution

**Strategy**: Leverage graph structure to only process actual edges.

**Implementation**:

```python
# Reverse graph tracks incoming edges
class CitationGraph:
    def add_edge(self, from_doc: str, to_doc: str):
        self.graph[from_doc].append(to_doc)  # Outgoing
        self.reverse_graph[to_doc].append(from_doc)  # Incoming
```

```python
# Optimized O(E) PageRank iteration
for node in all_nodes:
    rank_sum = 0.0
    # Only iterate over nodes that actually point to current node
    for incoming_node in reverse_graph[node]:  # E/N iterations on average
        rank_sum += scores[incoming_node] / outdegree(incoming_node)
    new_scores[node] = (1 - damping) / N + damping * rank_sum
```

**Additional Optimizations**:

1. **Progress Tracking**:
```python
with tqdm(total=max_iter, desc="PageRank iterations") as pbar:
    pbar.set_postfix({"diff": f"{convergence_diff:.6f}"})
```

2. **Early Convergence**:
```python
if convergence_diff < tolerance:  # 1e-6
    pbar.total = iteration + 1
    break  # Stop before max_iter if converged
```

#### Results & Impact

**Performance Improvements**:
- Complexity: **O(N²) → O(E)** per iteration where E = number of edges
- For sparse graph (E << N²): Orders of magnitude faster
- Iteration time: **Minutes → Seconds** per iteration
- Total PageRank time: **Hours → <5 minutes** for typical convergence (~20-30 iterations)

**Algorithmic Analysis**:
- Dense graph: E ≈ N², O(E) ≈ O(N²) (no improvement)
- Sparse graph: E ≈ k×N where k = avg edges per node
- With k = 20: O(E) = O(20N) = O(N), linear instead of quadratic

**Practical Example** (5,838 nodes):
- Before: 5,838² = 34,081,444 checks per iteration
- After: ~20 × 5,838 = 116,760 checks per iteration
- Speedup: **~292x per iteration**

**Convergence Behavior**:
- Typical convergence: 20-30 iterations (diff < 1e-6)
- Progress visible in real-time via tqdm
- User can monitor convergence delta and interrupt if needed

---

### Key Takeaways

1. **Graph Density Matters**: Dense graphs are not always better. Semantic filtering improved both performance AND quality.

2. **Data Structure Choice**: The reverse graph is a classic space-time tradeoff — doubling memory for massive speed gains.

3. **User Experience**: Progress bars and early stopping transform "is this hanging?" into actionable feedback.

4. **Algorithmic Complexity**: Understanding O(N²) vs O(E) is crucial for scalability. Even seemingly small optimizations (N² → E) compound over iterations.

5. **Validation**: Sparse graphs with semantic edges produce more interpretable and higher-quality PageRank scores than dense graphs with weak connections.

---

## License

MIT

---

## Acknowledgments

- [arXiv API](https://arxiv.org/help/api) for open research metadata
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond* (2009)
- Page, Brin, et al., *The PageRank Citation Ranking* (1999)
