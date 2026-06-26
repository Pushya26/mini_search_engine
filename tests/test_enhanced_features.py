"""
Tests for enhanced features: compilers, networking, data mining, systems analysis.
"""
import pytest
from src.query_compiler.lexer import tokenize, TType
from src.query_compiler.parser import compile_query, TermNode, BinaryNode, NotNode
from src.analytics.trend_miner import TrendMiner
from src.metrics.collector import MetricsCollector


class TestQueryCompiler:
    """Test boolean query compiler (lexer + parser)."""

    def test_lexer_simple_terms(self):
        """Test lexer tokenizes simple terms."""
        tokens = tokenize("neural network")
        assert tokens[0].type == TType.TERM
        assert tokens[0].value == "neural"
        assert tokens[1].type == TType.TERM
        assert tokens[1].value == "network"
        assert tokens[2].type == TType.EOF

    def test_lexer_operators(self):
        """Test lexer recognizes boolean operators."""
        tokens = tokenize("neural AND network OR system NOT survey")
        types = [t.type for t in tokens]
        assert TType.AND in types
        assert TType.OR in types
        assert TType.NOT in types

    def test_lexer_phrase(self):
        """Test lexer handles exact phrases."""
        tokens = tokenize('"exact phrase"')
        assert tokens[0].type == TType.PHRASE
        assert tokens[0].value == "exact phrase"

    def test_lexer_parentheses(self):
        """Test lexer handles parentheses."""
        tokens = tokenize("(neural OR network)")
        types = [t.type for t in tokens]
        assert TType.LPAREN in types
        assert TType.RPAREN in types

    def test_parser_simple_term(self):
        """Test parser compiles single term."""
        ast = compile_query("neural")
        assert isinstance(ast, TermNode)
        assert ast.term == "neural"

    def test_parser_implicit_and(self):
        """Test parser handles implicit AND."""
        ast = compile_query("neural network")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "AND"
        assert isinstance(ast.left, TermNode)
        assert isinstance(ast.right, TermNode)

    def test_parser_explicit_and(self):
        """Test parser handles explicit AND."""
        ast = compile_query("neural AND network")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "AND"

    def test_parser_or(self):
        """Test parser handles OR operator."""
        ast = compile_query("neural OR network")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "OR"

    def test_parser_not(self):
        """Test parser handles NOT operator."""
        ast = compile_query("neural NOT survey")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "AND"
        assert isinstance(ast.right, NotNode)

    def test_parser_precedence(self):
        """Test parser respects operator precedence (OR < AND < NOT)."""
        ast = compile_query("neural AND network OR system")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "OR"
        # Left side should be AND
        assert isinstance(ast.left, BinaryNode)
        assert ast.left.op == "AND"

    def test_parser_parentheses(self):
        """Test parser handles parentheses for grouping."""
        ast = compile_query("neural AND (network OR system)")
        assert isinstance(ast, BinaryNode)
        assert ast.op == "AND"
        assert isinstance(ast.right, BinaryNode)
        assert ast.right.op == "OR"

    def test_parser_complex_query(self):
        """Test parser handles complex nested query."""
        ast = compile_query("(neural OR deep) AND learning NOT survey")
        assert isinstance(ast, BinaryNode)
        # Should be AND at top level
        assert ast.op == "AND"

    def test_ast_to_dict(self):
        """Test AST serialization to dict."""
        ast = compile_query("neural AND network")
        d = ast.to_dict()
        assert d["type"] == "binary"
        assert d["op"] == "AND"
        assert "left" in d
        assert "right" in d


class TestTrendMiner:
    """Test data mining module."""

    @pytest.fixture
    def miner(self, tmp_path):
        """Create TrendMiner with test data."""
        # Create test papers
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()
        
        import json
        from datetime import datetime, timedelta
        
        # Recent paper
        recent = {
            "doc_id": "1",
            "title": "Transformer Neural Network",
            "abstract": "Deep learning transformer architecture",
            "published": (datetime.utcnow() - timedelta(days=30)).isoformat()
        }
        (papers_dir / "1.json").write_text(json.dumps(recent))
        
        # Old paper
        old = {
            "doc_id": "2",
            "title": "Classical Machine Learning",
            "abstract": "Traditional algorithms",
            "published": (datetime.utcnow() - timedelta(days=200)).isoformat()
        }
        (papers_dir / "2.json").write_text(json.dumps(old))
        
        return TrendMiner(str(papers_dir))

    def test_load_papers(self, miner):
        """Test loading papers from directory."""
        papers = miner.load_papers()
        assert len(papers) == 2
        assert all("title" in p for p in papers)

    def test_mine_trending_terms(self, miner):
        """Test trend analysis."""
        result = miner.mine_trending_terms(window_days=90, top_k=5)
        assert "window_days" in result
        assert "trending" in result
        assert "total_papers" in result
        assert result["total_papers"] == 2

    def test_mine_cooccurrences(self, miner):
        """Test association mining."""
        result = miner.mine_cooccurrences("neural", top_k=5)
        assert "term" in result
        assert result["term"] == "neural"
        assert "cooccurrences" in result
        assert "docs_with_term" in result

    def test_category_trends(self, tmp_path):
        """Test category distribution mining."""
        papers_dir = tmp_path / "papers"
        papers_dir.mkdir()
        
        import json
        paper = {
            "doc_id": "1",
            "title": "Test",
            "categories": ["cs.AI", "cs.LG"]
        }
        (papers_dir / "1.json").write_text(json.dumps(paper))
        
        miner = TrendMiner(str(papers_dir))
        result = miner.mine_category_trends(top_categories=5)
        assert "top_categories" in result
        assert "total_papers" in result


class TestMetricsCollector:
    """Test systems data analysis metrics."""

    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector."""
        c = MetricsCollector()
        c.reset()
        return c

    def test_record_query(self, collector):
        """Test recording query metrics."""
        collector.record_query(50.0, cache_hit=False)
        summary = collector.get_summary()
        assert summary["total_queries"] == 1
        assert summary["cache"]["misses"] == 1

    def test_cache_hit_tracking(self, collector):
        """Test cache hit/miss tracking."""
        collector.record_query(50.0, cache_hit=False)
        collector.record_query(2.0, cache_hit=True)
        
        summary = collector.get_summary()
        assert summary["cache"]["hits"] == 1
        assert summary["cache"]["misses"] == 1
        assert summary["cache"]["hit_rate_pct"] == 50.0

    def test_latency_percentiles(self, collector):
        """Test p50/p95/p99 latency calculation."""
        # Record 100 queries with varying latencies
        for i in range(100):
            collector.record_query(float(i), cache_hit=False)
        
        summary = collector.get_summary()
        assert "latency_ms" in summary
        assert "p50" in summary["latency_ms"]
        assert "p95" in summary["latency_ms"]
        assert "p99" in summary["latency_ms"]
        
        # Check percentiles are in expected range
        assert 40 <= summary["latency_ms"]["p50"] <= 60
        assert 90 <= summary["latency_ms"]["p95"] <= 99

    def test_error_tracking(self, collector):
        """Test error rate tracking."""
        collector.record_query(50.0, cache_hit=False)
        collector.record_error()
        
        summary = collector.get_summary()
        assert summary["errors"] == 1
        assert summary["error_rate_pct"] > 0

    def test_no_data(self, collector):
        """Test metrics with no data."""
        summary = collector.get_summary()
        assert summary["status"] == "no_data"

    def test_reset(self, collector):
        """Test metrics reset."""
        collector.record_query(50.0, cache_hit=False)
        collector.reset()
        summary = collector.get_summary()
        assert summary["total_queries"] == 0
