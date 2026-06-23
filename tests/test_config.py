import pytest
from src.config import settings

def test_config_loads():
    """Smoke test: verify config loads with defaults."""
    assert settings.BM25_K1 == 1.5
    assert settings.BM25_B == 0.75
    assert settings.RANK_ALPHA == 0.7
    assert settings.RANK_BETA == 0.3
    assert settings.MAX_PAPERS == 10000
    assert settings.API_PORT == 8000

def test_weights_sum_to_one():
    """Verify hybrid ranking weights are normalized."""
    assert abs(settings.RANK_ALPHA + settings.RANK_BETA - 1.0) < 0.01
