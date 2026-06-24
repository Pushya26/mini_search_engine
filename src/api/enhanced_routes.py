from fastapi import APIRouter, Query, HTTPException
from src.search.enhanced_engine import EnhancedSearchEngine
from src.config import settings
from .schemas import SearchResponse, StatsResponse, SimilarPapersResponse

router = APIRouter()

_search_engine = None

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
    engine = get_search_engine()
    return engine.search(q, page, size, expand_query=expand)

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
