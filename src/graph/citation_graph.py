import orjson
from pathlib import Path
from collections import defaultdict

class CitationGraph:
    def __init__(self):
        self.graph: dict[str, list[str]] = defaultdict(list)
        self.reverse_graph: dict[str, list[str]] = defaultdict(list)
        self.nodes: set[str] = set()
    
    def add_edge(self, from_doc: str, to_doc: str):
        self.nodes.add(from_doc)
        self.nodes.add(to_doc)
        if to_doc not in self.graph[from_doc]:
            self.graph[from_doc].append(to_doc)
            self.reverse_graph[to_doc].append(from_doc)
    
    def build_from_papers(self, papers_dir: Path):
        from tqdm import tqdm
        
        papers = []
        for paper_file in tqdm(list(papers_dir.glob("*.json")), desc="Loading papers"):
            paper = orjson.loads(paper_file.read_bytes())
            papers.append(paper)
        
        # Only connect papers sharing 2+ categories (much more selective)
        for i, p1 in enumerate(tqdm(papers, desc="Building edges")):
            for p2 in papers[i+1:]:
                shared = len(set(p1["categories"]) & set(p2["categories"]))
                if shared >= 2:
                    self.add_edge(p1["doc_id"], p2["doc_id"])
                    self.add_edge(p2["doc_id"], p1["doc_id"])
        
        # Add self-loops for ergodicity
        for doc_id in list(self.nodes):
            self.add_edge(doc_id, doc_id)
    
    def get_neighbors(self, doc_id: str) -> list[str]:
        return self.graph.get(doc_id, [])
    
    def get_outdegree(self, doc_id: str) -> int:
        return len(self.graph.get(doc_id, []))
    
    def get_incoming(self, doc_id: str) -> list[str]:
        return self.reverse_graph.get(doc_id, [])
