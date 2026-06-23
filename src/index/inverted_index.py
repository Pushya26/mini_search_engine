import orjson
import math
from pathlib import Path
from collections import defaultdict
from .postings import Posting

class InvertedIndex:
    def __init__(self):
        self.index: dict[str, list[Posting]] = defaultdict(list)
        self.doc_lengths: dict[str, int] = {}
        self.num_docs = 0
        self.avg_doc_length = 0
        self.idf_cache: dict[str, float] = {}
    
    def add_document(self, doc_id: str, tokens: list[str]):
        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1
        
        self.doc_lengths[doc_id] = len(tokens)
        
        for term, freq in term_freq.items():
            self.index[term].append(Posting(doc_id, freq))
    
    def finalize(self):
        for term in self.index:
            self.index[term].sort()
        
        self.num_docs = len(self.doc_lengths)
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.num_docs if self.num_docs > 0 else 0
        
        for term, postings in self.index.items():
            df = len(postings)
            self.idf_cache[term] = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)
    
    def get_postings(self, term: str) -> list[Posting]:
        return self.index.get(term, [])
    
    def get_idf(self, term: str) -> float:
        return self.idf_cache.get(term, 0.0)
    
    def save(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        
        index_data = {
            term: [(p.doc_id, p.term_freq) for p in postings]
            for term, postings in self.index.items()
        }
        
        (path / "dictionary.json").write_bytes(orjson.dumps(index_data))
        
        metadata = {
            "num_docs": self.num_docs,
            "avg_doc_length": self.avg_doc_length,
            "doc_lengths": self.doc_lengths,
            "idf_cache": self.idf_cache
        }
        (path / "metadata.json").write_bytes(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))
    
    @classmethod
    def load(cls, path: Path):
        idx = cls()
        
        index_data = orjson.loads((path / "dictionary.json").read_bytes())
        for term, postings_list in index_data.items():
            idx.index[term] = [Posting(doc_id, freq) for doc_id, freq in postings_list]
        
        metadata = orjson.loads((path / "metadata.json").read_bytes())
        idx.num_docs = metadata["num_docs"]
        idx.avg_doc_length = metadata["avg_doc_length"]
        idx.doc_lengths = metadata["doc_lengths"]
        idx.idf_cache = metadata["idf_cache"]
        
        return idx
