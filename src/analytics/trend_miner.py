"""
Data mining module: temporal trend analysis and association mining.
Mines publication-date-bucketed term frequencies to identify emerging topics.
"""
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TrendMiner:
    """
    Mines publication-date-bucketed term frequencies to identify
    emerging topics. Classic data mining: frequent pattern discovery
    over timestamped document corpora.
    """

    def __init__(self, data_dir: str = "./data/papers"):
        self.data_dir = Path(data_dir)
        self._stopwords = {
            "the", "a", "an", "of", "in", "and", "to", "for",
            "is", "are", "was", "were", "with", "this", "that",
            "we", "our", "be", "can", "has", "have", "by", "from",
            "on", "at", "as", "or", "not", "which", "but", "also",
        }

    def load_papers(self) -> list[dict]:
        """Load all papers from data directory."""
        papers = []
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            return []

        for f in self.data_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fp:
                    papers.append(json.load(fp))
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {f}: {e}")
                continue

        return papers

    def mine_trending_terms(self, window_days: int = 90, top_k: int = 20) -> dict:
        """
        Returns terms that appear more frequently in recent papers
        vs. the full corpus baseline (TF-IDF over time windows).

        Args:
            window_days: Look at papers from the last N days
            top_k: Return top N trending terms

        Returns:
            Dictionary with trending terms and their scores
        """
        papers = self.load_papers()
        if not papers:
            return {"window_days": window_days, "trending": {}, "error": "No papers found"}

        cutoff = datetime.utcnow() - timedelta(days=window_days)

        recent_terms: Counter = Counter()
        all_terms: Counter = Counter()

        for p in papers:
            # Extract and tokenize text
            text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
            terms = [
                w for w in text.split()
                if len(w) > 3 and w.isalpha() and w not in self._stopwords
            ]

            all_terms.update(terms)

            # Check if paper is recent
            pub = p.get("published", "")
            try:
                if pub and datetime.fromisoformat(pub[:10]) >= cutoff:
                    recent_terms.update(terms)
            except (ValueError, TypeError):
                pass

        # Calculate trend scores
        n_recent = max(sum(recent_terms.values()), 1)
        n_all = max(sum(all_terms.values()), 1)

        trends = {}
        for term, freq in recent_terms.most_common(200):
            baseline = all_terms[term] / n_all
            recent_rate = freq / n_recent
            # Trend score: how much more frequent in recent vs baseline
            trends[term] = {
                "trend_score": round(recent_rate / (baseline + 1e-9), 3),
                "recent_count": freq,
                "total_count": all_terms[term],
            }

        # Sort by trend score and return top K
        top = sorted(
            trends.items(),
            key=lambda x: x[1]["trend_score"],
            reverse=True
        )

        return {
            "window_days": window_days,
            "total_papers": len(papers),
            "recent_papers": len([p for p in papers
                                 if p.get("published", "")
                                 and datetime.fromisoformat(p["published"][:10]) >= cutoff]),
            "trending": dict(top[:top_k]),
        }

    def mine_cooccurrences(self, term: str, top_k: int = 10) -> dict:
        """
        Association mining: which terms co-occur most with a given term?

        Args:
            term: Target term to find associations
            top_k: Return top N co-occurring terms

        Returns:
            Dictionary with co-occurring terms and frequencies
        """
        papers = self.load_papers()
        if not papers:
            return {"term": term, "cooccurrences": {}, "error": "No papers found"}

        cooccur: Counter = Counter()
        docs_with_term = 0

        for p in papers:
            text = f"{p.get('title', '')} {p.get('abstract', '')}".lower().split()
            # Clean tokens
            tokens = [
                w for w in text
                if len(w) > 3 and w.isalpha() and w not in self._stopwords
            ]

            if term.lower() in tokens:
                docs_with_term += 1
                # Count co-occurrences (exclude the term itself)
                cooccur.update(w for w in tokens if w != term.lower())

        return {
            "term": term,
            "docs_with_term": docs_with_term,
            "total_docs": len(papers),
            "cooccurrences": dict(cooccur.most_common(top_k)),
        }

    def mine_category_trends(self, top_categories: int = 10) -> dict:
        """
        Find trending research categories.

        Returns:
            Dictionary with category distribution and trends
        """
        papers = self.load_papers()
        if not papers:
            return {"categories": {}, "error": "No papers found"}

        category_counts: Counter = Counter()

        for p in papers:
            categories = p.get("categories", [])
            if isinstance(categories, list):
                category_counts.update(categories)

        return {
            "total_papers": len(papers),
            "unique_categories": len(category_counts),
            "top_categories": dict(category_counts.most_common(top_categories)),
        }
