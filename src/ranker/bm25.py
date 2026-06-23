from src.index.inverted_index import InvertedIndex

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
    
    def score(self, index: InvertedIndex, query_terms: list[str], doc_id: str) -> float:
        score = 0.0
        doc_length = index.doc_lengths.get(doc_id, 0)
        
        if doc_length == 0:
            return 0.0
        
        for term in query_terms:
            idf = index.get_idf(term)
            
            # Find term frequency in this document
            tf = 0
            for posting in index.get_postings(term):
                if posting.doc_id == doc_id:
                    tf = posting.term_freq
                    break
            
            if tf > 0:
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / index.avg_doc_length)
                score += idf * (numerator / denominator)
        
        return score
