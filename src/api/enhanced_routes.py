from fastapi import APIRouter, Query, HTTPException
from src.search.enhanced_engine import EnhancedSearchEngine
from src.config import settings
from .schemas import SearchResponse, StatsResponse, SimilarPapersResponse
from src.query_compiler.parser import compile_query
from src.analytics.trend_miner import TrendMiner
from src.metrics.collector import metrics
import time

router = APIRouter()

_search_engine = None
_trend_miner = None

def get_search_engine():
    global _search_engine
    if _search_engine is None:
        _search_engine = EnhancedSearchEngine(
            settings.DATA_DIR,
            alpha=settings.RANK_ALPHA,
            beta=settings.RANK_BETA,
            use_query_expansion=True
        )
    return _search_engine

def get_trend_miner():
    global _trend_miner
    if _trend_miner is None:
        _trend_miner = TrendMiner(str(settings.DATA_DIR / "papers"))
    return _trend_miner

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Query string"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Results per page"),
    expand: bool = Query(True, description="Enable query expansion with synonyms")
):
    """
    Search papers with BM25 + PageRank hybrid ranking.
    
    Features:
    - Query expansion with synonyms (controlled by 'expand' parameter)
    - Result caching for repeated queries
    - Hybrid ranking: 70% BM25 + 30% PageRank
    """
    start = time.perf_counter()
    engine = get_search_engine()
    result = engine.search(q, page, size, expand_query=expand)
    
    # Record metrics
    latency_ms = (time.perf_counter() - start) * 1000
    # Check if result came from cache (if took_ms is very low, likely cached)
    cache_hit = result.get("took_ms", latency_ms) < 5
    metrics.record_query(latency_ms, cache_hit)
    
    return result

@router.get("/similar/{doc_id}")
def get_similar(
    doc_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar papers")
):
    """
    Find papers similar to the given paper.
    
    Uses the paper's title and abstract to find related work.
    """
    engine = get_search_engine()
    similar = engine.get_similar_papers(doc_id, top_k)
    
    if not similar:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "doc_id": doc_id,
        "similar_papers": similar
    }

@router.get("/paper/{doc_id}")
def get_paper(doc_id: str):
    """Get full paper metadata by ID."""
    engine = get_search_engine()
    paper = engine._get_paper(doc_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return paper

@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.2.0"}

@router.get("/stats", response_model=StatsResponse)
def stats():
    """Get corpus and index statistics."""
    index_dir = settings.DATA_DIR / "index"
    papers_dir = settings.DATA_DIR / "papers"
    
    if not index_dir.exists():
        return {
            "num_papers": 0,
            "num_terms": 0,
            "avg_doc_length": 0.0,
            "index_exists": False
        }
    
    import orjson
    metadata = orjson.loads((index_dir / "metadata.json").read_bytes())
    
    return {
        "num_papers": metadata["num_docs"],
        "num_terms": len(metadata["idf_cache"]),
        "avg_doc_length": metadata["avg_doc_length"],
        "index_exists": True
    }


# ============================================================================
# NEW ENDPOINTS: Networking, Compilers, Data Mining, Systems Analysis
# ============================================================================

@router.get("/query/parse")
def parse_query(q: str = Query(..., description="Query string to parse")):
    """
    Compile boolean query to AST (Abstract Syntax Tree).
    
    Demonstrates compiler design: lexer → parser → AST.
    Supports: AND, OR, NOT, parentheses, exact phrases.
    
    Examples:
        - "neural network" → AND(TERM(neural), TERM(network))
        - "neural AND (network OR system)" → AND(TERM(neural), OR(TERM(network), TERM(system)))
        - "transformer NOT survey" → AND(TERM(transformer), NOT(TERM(survey)))
    """
    try:
        ast = compile_query(q)
        return {
            "query": q,
            "ast": repr(ast),
            "ast_json": ast.to_dict(),
            "status": "compiled"
        }
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Query syntax error: {str(e)}")


@router.get("/analytics/trends")
def trending_topics(
    window: int = Query(90, ge=1, le=730, description="Time window in days"),
    top_k: int = Query(20, ge=5, le=100, description="Number of trending terms")
):
    """
    Data mining: identify emerging research topics.
    
    Analyzes temporal term frequency patterns to surface
    topics that are growing in popularity.
    
    Returns trend scores: (recent_frequency / baseline_frequency).
    """
    miner = get_trend_miner()
    return miner.mine_trending_terms(window_days=window, top_k=top_k)


@router.get("/analytics/cooccurrence")
def cooccurrence(
    term: str = Query(..., description="Term to find associations"),
    top_k: int = Query(10, ge=5, le=50, description="Number of co-occurring terms")
):
    """
    Association mining: find terms that co-occur with a given term.
    
    Uses frequency-based association rule mining to identify
    related research topics.
    """
    miner = get_trend_miner()
    return miner.mine_cooccurrences(term, top_k)


@router.get("/analytics/categories")
def category_trends(
    top_k: int = Query(10, ge=5, le=50, description="Number of top categories")
):
    """
    Analyze research category distribution.
    
    Shows which arXiv categories are most represented in the corpus.
    """
    miner = get_trend_miner()
    return miner.mine_category_trends(top_categories=top_k)


@router.get("/metrics")
def get_metrics():
    """
    Systems data analysis: real-time performance metrics.
    
    Tracks:
        - p50/p95/p99 query latency percentiles
        - Cache hit/miss rates
        - Total throughput
        - Error rates
    
    Demonstrates systems observability and performance analysis.
    """
    return metrics.get_summary()
