import pytest
from src.index.inverted_index import InvertedIndex
from src.ranker.bm25 import BM25

def test_bm25_basic():
    idx = InvertedIndex()
    idx.add_document("doc1", ["neural", "network", "neural"])
    idx.add_document("doc2", ["network"])
    idx.finalize()
    
    bm25 = BM25()
    score1 = bm25.score(idx, ["neural"], "doc1")
    score2 = bm25.score(idx, ["neural"], "doc2")
    
    assert score1 > 0
    assert score2 == 0

def test_bm25_term_frequency_saturation():
    idx = InvertedIndex()
    idx.add_document("doc1", ["word"] * 10)
    idx.add_document("doc2", ["word"] * 100)
    idx.finalize()
    
    bm25 = BM25(k1=1.5)
    score1 = bm25.score(idx, ["word"], "doc1")
    score2 = bm25.score(idx, ["word"], "doc2")
    
    # Due to saturation, score shouldn't scale linearly
    assert score2 > score1
    assert score2 < score1 * 10

def test_bm25_length_normalization():
    idx = InvertedIndex()
    idx.add_document("doc1", ["query"] + ["other"] * 100)
    idx.add_document("doc2", ["query"])
    idx.finalize()
    
    bm25 = BM25(b=0.75)
    score1 = bm25.score(idx, ["query"], "doc1")
    score2 = bm25.score(idx, ["query"], "doc2")
    
    # Shorter doc should score higher due to length penalty
    assert score2 > score1
