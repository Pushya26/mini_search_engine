from nltk.corpus import wordnet
from typing import Set

class QueryExpander:
    def __init__(self, max_synonyms_per_term: int = 2):
        self.max_synonyms = max_synonyms_per_term
        # Download wordnet if needed
        try:
            wordnet.synsets('test')
        except LookupError:
            import nltk
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
    
    def expand(self, query_terms: list[str]) -> list[str]:
        """Expand query with synonyms from WordNet."""
        expanded = set(query_terms)
        
        for term in query_terms:
            synonyms = self._get_synonyms(term)
            # Add top synonyms
            for syn in list(synonyms)[:self.max_synonyms]:
                expanded.add(syn)
        
        return list(expanded)
    
    def _get_synonyms(self, word: str) -> Set[str]:
        """Get synonyms for a word from WordNet."""
        synonyms = set()
        
        for synset in wordnet.synsets(word):
            for lemma in synset.lemmas():
                # Get lemma name and clean it
                syn = lemma.name().lower().replace('_', ' ')
                if syn != word and len(syn) > 2:
                    synonyms.add(syn)
        
        return synonyms
    
    def expand_with_weights(self, query_terms: list[str]) -> dict[str, float]:
        """Expand query and assign weights (original terms weight more)."""
        weights = {}
        
        # Original terms get full weight
        for term in query_terms:
            weights[term] = 1.0
        
        # Synonyms get reduced weight
        for term in query_terms:
            synonyms = self._get_synonyms(term)
            for syn in list(synonyms)[:self.max_synonyms]:
                if syn not in weights:
                    weights[syn] = 0.5  # Synonyms contribute half weight
        
        return weights
