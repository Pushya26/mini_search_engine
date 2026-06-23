import pytest
from src.index.inverted_index import InvertedIndex
from src.ranker.hybrid import HybridRanker

def test_hybrid_ranking():
    idx = InvertedIndex()
    idx.add_document("doc1", ["neural", "network"])
    idx.add_document("doc2", ["network"])
    idx.add_document("doc3", ["deep", "learning"])
    idx.finalize()
    
    pagerank = {"doc1": 0.1, "doc2": 0.5, "doc3": 0.2}
    
    ranker = HybridRanker(alpha=0.7, beta=0.3)
    results = ranker.rank(idx, ["neural", "network"], pagerank)
    
    assert len(results) == 2
    assert results[0]["doc_id"] in ["doc1", "doc2"]
    assert all("score" in r for r in results)
    assert all("bm25_score" in r for r in results)
    assert all("pagerank_score" in r for r in results)

def test_hybrid_weights():
    idx = InvertedIndex()
    idx.add_document("doc1", ["query"])
    idx.add_document("doc2", ["query"])
    idx.finalize()
    
    # doc2 has much higher PageRank
    pagerank = {"doc1": 0.1, "doc2": 0.9}
    
    ranker_bm25_heavy = HybridRanker(alpha=1.0, beta=0.0)
    ranker_pr_heavy = HybridRanker(alpha=0.0, beta=1.0)
    
    results_bm25 = ranker_bm25_heavy.rank(idx, ["query"], pagerank)
    results_pr = ranker_pr_heavy.rank(idx, ["query"], pagerank)
    
    # With PageRank weight, doc2 should win
    assert results_pr[0]["doc_id"] == "doc2"
