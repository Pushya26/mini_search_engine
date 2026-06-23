from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Paths
    DATA_DIR: Path = Path("./data")
    
    # BM25 parameters
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    
    # Hybrid ranking weights
    RANK_ALPHA: float = 0.7
    RANK_BETA: float = 0.3
    
    # Crawling
    MAX_PAPERS: int = 10000
    
    # API
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
