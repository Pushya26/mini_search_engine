from pydantic import BaseModel
from typing import Optional

class SearchResult(BaseModel):
    doc_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published: str
    score: float
    bm25_score: float
    pagerank_score: float
    pdf_url: str

class SearchResponse(BaseModel):
    query: str
    expanded_query: Optional[list[str]] = None
    total_hits: int
    page: int
    size: int
    total_pages: int
    results: list[SearchResult]
    took_ms: int

class SimilarPapersResponse(BaseModel):
    doc_id: str
    similar_papers: list[SearchResult]

class StatsResponse(BaseModel):
    num_papers: int
    num_terms: int
    avg_doc_length: float
    index_exists: bool
