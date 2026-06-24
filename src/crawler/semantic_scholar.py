import httpx
import time
from typing import Optional

class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT = 1.0  # 1 second between requests
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.last_request = 0
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request = time.time()
    
    def get_paper_citations(self, arxiv_id: str) -> Optional[dict]:
        """Get paper metadata and citations from Semantic Scholar."""
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/paper/arXiv:{arxiv_id}"
            params = {
                "fields": "paperId,title,citations,references,citationCount,referenceCount"
            }
            
            response = self.client.get(url, params=params)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Extract arXiv IDs from references
            references = []
            for ref in data.get('references', []):
                if ref.get('externalIds', {}).get('ArXiv'):
                    references.append(ref['externalIds']['ArXiv'])
            
            # Extract arXiv IDs from citations
            citations = []
            for cit in data.get('citations', []):
                if cit.get('externalIds', {}).get('ArXiv'):
                    citations.append(cit['externalIds']['ArXiv'])
            
            return {
                'arxiv_id': arxiv_id,
                'references': references,
                'citations': citations,
                'citation_count': data.get('citationCount', 0),
                'reference_count': data.get('referenceCount', 0)
            }
            
        except Exception as e:
            print(f"Error fetching {arxiv_id}: {e}")
            return None
    
    def close(self):
        self.client.close()
