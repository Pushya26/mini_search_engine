from dataclasses import dataclass

@dataclass
class Posting:
    doc_id: str
    term_freq: int
    
    def __lt__(self, other):
        return self.doc_id < other.doc_id
