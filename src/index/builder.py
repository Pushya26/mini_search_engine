import orjson
from pathlib import Path
from tqdm import tqdm
from src.tokenizer.tokenizer import Tokenizer
from .inverted_index import InvertedIndex

class IndexBuilder:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.papers_dir = data_dir / "papers"
        self.index_dir = data_dir / "index"
        self.tokenizer = Tokenizer(use_stemming=True)
    
    def build(self):
        index = InvertedIndex()
        
        paper_files = list(self.papers_dir.glob("*.json"))
        
        for paper_file in tqdm(paper_files, desc="Indexing papers"):
            paper = orjson.loads(paper_file.read_bytes())
            
            title_tokens = self.tokenizer.tokenize(paper["title"])
            abstract_tokens = self.tokenizer.tokenize(paper["abstract"])
            
            # Title weight x3
            all_tokens = title_tokens * 3 + abstract_tokens
            
            index.add_document(paper["doc_id"], all_tokens)
        
        index.finalize()
        index.save(self.index_dir)
        
        return index
