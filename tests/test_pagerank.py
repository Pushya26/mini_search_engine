import pytest
from src.graph.citation_graph import CitationGraph
from src.graph.pagerank import PageRank

def test_simple_graph():
    graph = CitationGraph()
    graph.add_edge("A", "B")
    graph.add_edge("A", "C")
    graph.add_edge("B", "C")
    graph.add_edge("C", "A")
    
    pr = PageRank()
    scores = pr.compute(graph)
    
    assert len(scores) == 3
    assert all(score > 0 for score in scores.values())
    assert abs(sum(scores.values()) - 1.0) < 0.01

def test_hub_node():
    graph = CitationGraph()
    # Node C is pointed to by all others
    graph.add_edge("A", "C")
    graph.add_edge("B", "C")
    graph.add_edge("C", "C")
    
    pr = PageRank()
    scores = pr.compute(graph)
    
    # C should have highest score
    assert scores["C"] > scores["A"]
    assert scores["C"] > scores["B"]

def test_convergence():
    graph = CitationGraph()
    for i in range(10):
        for j in range(10):
            if i != j:
                graph.add_edge(f"doc{i}", f"doc{j}")
    
    pr = PageRank(max_iter=100)
    scores = pr.compute(graph)
    
    # All nodes should have similar scores in fully connected graph
    values = list(scores.values())
    assert max(values) - min(values) < 0.01
