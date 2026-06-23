import time
import httpx
from xml.etree import ElementTree as ET

class ArxivClient:
    BASE_URL = "https://export.arxiv.org/api/query"
    RATE_LIMIT = 3.0
    
    def __init__(self):
        self.last_request = 0
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self.last_request = time.time()
    
    def search(self, query: str, start: int = 0, max_results: int = 100) -> list[dict]:
        self._rate_limit()
        
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        return self._parse_response(response.text)
    
    def _parse_response(self, xml_text: str) -> list[dict]:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
        papers = []
        for entry in root.findall("atom:entry", ns):
            doc_id = entry.find("atom:id", ns).text.split("/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
            categories = [c.attrib["term"] for c in entry.findall("atom:category", ns)]
            published = entry.find("atom:published", ns).text
            
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            pdf_url = pdf_link.attrib["href"] if pdf_link is not None else f"https://arxiv.org/pdf/{doc_id}"
            
            papers.append({
                "doc_id": doc_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "categories": categories,
                "published": published,
                "pdf_url": pdf_url,
                "references": []
            })
        
        return papers
    
    def close(self):
        self.client.close()
