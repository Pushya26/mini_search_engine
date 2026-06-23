import orjson
from pathlib import Path
from tqdm import tqdm
from .arxiv_client import ArxivClient

class Fetcher:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.papers_dir = data_dir / "papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.client = ArxivClient()
    
    def _paper_exists(self, doc_id: str) -> bool:
        return (self.papers_dir / f"{doc_id}.json").exists()
    
    def _save_paper(self, paper: dict):
        path = self.papers_dir / f"{paper['doc_id']}.json"
        path.write_bytes(orjson.dumps(paper, option=orjson.OPT_INDENT_2))
    
    def fetch(self, categories: list[str], max_papers: int):
        total_fetched = 0
        
        for category in categories:
            query = f"cat:{category}"
            start = 0
            batch_size = 100
            
            with tqdm(desc=f"Fetching {category}", unit=" papers") as pbar:
                while total_fetched < max_papers:
                    try:
                        papers = self.client.search(query, start=start, max_results=batch_size)
                        
                        if not papers:
                            break
                        
                        new_count = 0
                        for paper in papers:
                            if not self._paper_exists(paper["doc_id"]):
                                self._save_paper(paper)
                                new_count += 1
                                total_fetched += 1
                                pbar.update(1)
                                
                                if total_fetched >= max_papers:
                                    break
                        
                        if new_count == 0:
                            break
                        
                        start += batch_size
                        
                    except Exception as e:
                        print(f"\nError fetching batch: {e}")
                        break
            
            if total_fetched >= max_papers:
                break
        
        self.client.close()
        return total_fetched
