import re
from .stopwords import STOPWORDS
from .stemmer import Stemmer

class Tokenizer:
    def __init__(self, use_stemming: bool = True):
        self.use_stemming = use_stemming
        self.stemmer = Stemmer() if use_stemming else None
        self.pattern = re.compile(r'[a-z0-9]+')
    
    def tokenize(self, text: str) -> list[str]:
        text = text.lower()
        tokens = self.pattern.findall(text)
        tokens = [t for t in tokens if len(t) >= 2 and t not in STOPWORDS]
        
        if self.use_stemming:
            tokens = [self.stemmer.stem(t) for t in tokens]
        
        return tokens
