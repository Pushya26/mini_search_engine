import pytest
from src.search.query_expansion import QueryExpander

def test_query_expansion_basic():
    expander = QueryExpander(max_synonyms_per_term=2)
    
    original = ["network"]
    expanded = expander.expand(original)
    
    # Should include original term
    assert "network" in expanded
    # Should add some synonyms
    assert len(expanded) >= len(original)

def test_query_expansion_with_weights():
    expander = QueryExpander(max_synonyms_per_term=2)
    
    weights = expander.expand_with_weights(["neural", "network"])
    
    # Original terms should have full weight
    assert weights.get("neural") == 1.0
    assert weights.get("network") == 1.0
    
    # Synonyms should have reduced weight
    for term, weight in weights.items():
        if term not in ["neural", "network"]:
            assert weight < 1.0

def test_no_expansion_for_unknown_words():
    expander = QueryExpander(max_synonyms_per_term=2)
    
    # Made-up word should not expand
    original = ["xyzabc123"]
    expanded = expander.expand(original)
    
    assert len(expanded) == 1
    assert "xyzabc123" in expanded
