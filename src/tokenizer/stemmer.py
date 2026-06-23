from nltk.stem import PorterStemmer

class Stemmer:
    def __init__(self):
        self._stemmer = PorterStemmer()
    
    def stem(self, word: str) -> str:
        return self._stemmer.stem(word)
