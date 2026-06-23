from .citation_graph import CitationGraph
from tqdm import tqdm

class PageRank:
    def __init__(self, damping: float = 0.85, max_iter: int = 100, tolerance: float = 1e-6):
        self.damping = damping
        self.max_iter = max_iter
        self.tolerance = tolerance
    
    def compute(self, graph: CitationGraph) -> dict[str, float]:
        nodes = list(graph.nodes)
        n = len(nodes)
        
        if n == 0:
            return {}
        
        # Initialize uniform scores
        scores = {node: 1.0 / n for node in nodes}
        
        with tqdm(total=self.max_iter, desc="PageRank iterations") as pbar:
            for iteration in range(self.max_iter):
                new_scores = {}
                
                for node in nodes:
                    rank_sum = 0.0
                    
                    # Sum contributions from incoming edges only
                    for incoming_node in graph.get_incoming(node):
                        outdegree = graph.get_outdegree(incoming_node)
                        if outdegree > 0:
                            rank_sum += scores[incoming_node] / outdegree
                    
                    new_scores[node] = (1 - self.damping) / n + self.damping * rank_sum
                
                # Check convergence
                diff = sum(abs(new_scores[node] - scores[node]) for node in nodes)
                scores = new_scores
                
                pbar.update(1)
                pbar.set_postfix({"diff": f"{diff:.6f}"})
                
                if diff < self.tolerance:
                    pbar.total = iteration + 1
                    pbar.refresh()
                    break
        
        return scores
