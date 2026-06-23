import pytest
from src.index.inverted_index import InvertedIndex
from src.index.postings import Posting

def test_add_and_retrieve():
    idx = InvertedIndex()
    idx.add_document("doc1", ["neural", "network", "neural"])
    idx.add_document("doc2", ["network", "deep"])
    idx.finalize()
    
    postings = idx.get_postings("neural")
    assert len(postings) == 1
    assert postings[0].doc_id == "doc1"
    assert postings[0].term_freq == 2
    
    postings = idx.get_postings("network")
    assert len(postings) == 2

def test_idf_calculation():
    idx = InvertedIndex()
    idx.add_document("doc1", ["rare", "common"])
    idx.add_document("doc2", ["common"])
    idx.add_document("doc3", ["common"])
    idx.finalize()
    
    rare_idf = idx.get_idf("rare")
    common_idf = idx.get_idf("common")
    
    assert rare_idf > common_idf
    assert rare_idf > 0

def test_doc_length_tracking():
    idx = InvertedIndex()
    idx.add_document("doc1", ["a", "b", "c"])
    idx.add_document("doc2", ["x", "y"])
    idx.finalize()
    
    assert idx.doc_lengths["doc1"] == 3
    assert idx.doc_lengths["doc2"] == 2
    assert idx.avg_doc_length == 2.5
