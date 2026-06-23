from pydantic import BaseModel

class SearchResult(BaseModel):
    doc_id: str
    title: str
    abstract: str
    authors: list[str]
    score: float
    bm25_score: float
    pagerank_score: float
    pdf_url: str

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    page: int
    size: int
    total_pages: int
    results: list[SearchResult]
    took_ms: int

class StatsResponse(BaseModel):
    num_papers: int
    num_terms: int
    avg_doc_length: float
    index_exists: bool
