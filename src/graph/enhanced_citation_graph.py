import orjson
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

class EnhancedCitationGraph:
    def __init__(self):
        self.graph: dict[str, list[str]] = defaultdict(list)
        self.reverse_graph: dict[str, list[str]] = defaultdict(list)
        self.nodes: set[str] = set()
        self.citation_counts: dict[str, int] = {}
    
    def add_edge(self, from_doc: str, to_doc: str):
        self.nodes.add(from_doc)
        self.nodes.add(to_doc)
        if to_doc not in self.graph[from_doc]:
            self.graph[from_doc].append(to_doc)
            self.reverse_graph[to_doc].append(from_doc)
    
    def build_from_papers(self, papers_dir: Path, use_real_citations: bool = False):
        """Build citation graph using co-citation or real citation data."""
        papers = []
        for paper_file in tqdm(list(papers_dir.glob("*.json")), desc="Loading papers"):
            paper = orjson.loads(paper_file.read_bytes())
            papers.append(paper)
        
        if use_real_citations:
            self._build_real_citations(papers, papers_dir)
        else:
            self._build_co_citations(papers)
        
        # Add self-loops for ergodicity
        for doc_id in list(self.nodes):
            self.add_edge(doc_id, doc_id)
    
    def _build_co_citations(self, papers):
        """Build graph by connecting papers sharing 2+ categories."""
        for i, p1 in enumerate(tqdm(papers, desc="Building co-citation edges")):
            for p2 in papers[i+1:]:
                shared = len(set(p1["categories"]) & set(p2["categories"]))
                if shared >= 2:
                    self.add_edge(p1["doc_id"], p2["doc_id"])
                    self.add_edge(p2["doc_id"], p1["doc_id"])
    
    def _build_real_citations(self, papers, papers_dir):
        """Build graph using real citation data from Semantic Scholar."""
        from ..crawler.semantic_scholar import SemanticScholarClient
        
        ss_client = SemanticScholarClient()
        citation_cache_path = papers_dir.parent / "citations_cache.json"
        
        # Load cache if exists
        citation_cache = {}
        if citation_cache_path.exists():
            citation_cache = orjson.loads(citation_cache_path.read_bytes())
        
        doc_ids = {p["doc_id"] for p in papers}
        
        for paper in tqdm(papers, desc="Fetching real citations"):
            doc_id = paper["doc_id"]
            
            # Check cache first
            if doc_id in citation_cache:
                citation_data = citation_cache[doc_id]
            else:
                citation_data = ss_client.get_paper_citations(doc_id)
                if citation_data:
                    citation_cache[doc_id] = citation_data
            
            if not citation_data:
                continue
            
            # Add edges for references (papers this paper cites)
            for ref_id in citation_data.get('references', []):
                if ref_id in doc_ids:
                    self.add_edge(doc_id, ref_id)
            
            # Add edges for citations (papers that cite this paper)
            for cit_id in citation_data.get('citations', []):
                if cit_id in doc_ids:
                    self.add_edge(cit_id, doc_id)
            
            # Store citation count for quality scoring
            self.citation_counts[doc_id] = citation_data.get('citation_count', 0)
        
        # Save cache
        citation_cache_path.write_bytes(orjson.dumps(citation_cache))
        ss_client.close()
    
    def get_neighbors(self, doc_id: str) -> list[str]:
        return self.graph.get(doc_id, [])
    
    def get_incoming(self, doc_id: str) -> list[str]:
        return self.reverse_graph.get(doc_id, [])
    
    def get_outdegree(self, doc_id: str) -> int:
        return len(self.graph.get(doc_id, []))
    
    def get_citation_count(self, doc_id: str) -> int:
        return self.citation_counts.get(doc_id, 0)
