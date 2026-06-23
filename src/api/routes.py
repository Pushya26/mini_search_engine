from fastapi import APIRouter, Query
from src.search.engine import SearchEngine
from src.config import settings
from .schemas import SearchResponse, StatsResponse

router = APIRouter()

_search_engine = None

def get_search_engine():
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine(
            settings.DATA_DIR,
            alpha=settings.RANK_ALPHA,
            beta=settings.RANK_BETA
        )
    return _search_engine

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="Query string"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Results per page")
):
    engine = get_search_engine()
    return engine.search(q, page, size)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/stats", response_model=StatsResponse)
def stats():
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
