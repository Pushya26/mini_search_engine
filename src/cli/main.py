import typer
from pathlib import Path
from src.config import settings
from src.crawler.fetcher import Fetcher

app = typer.Typer()

@app.command()
def crawl(max_papers: int = 10000, categories: str = "cs.AI,cs.CL,cs.LG"):
    """Fetch papers from arXiv."""
    cats = [c.strip() for c in categories.split(",")]
    fetcher = Fetcher(settings.DATA_DIR)
    
    typer.echo(f"Starting crawl: max_papers={max_papers}, categories={cats}")
    count = fetcher.fetch(cats, max_papers)
    typer.echo(f"Fetched {count} papers to {settings.DATA_DIR / 'papers'}")

@app.command()
def index(rebuild: bool = False, real_citations: bool = False):
    """
    Build inverted index and PageRank scores.
    
    Args:
        rebuild: Force rebuild even if index exists
        real_citations: Use Semantic Scholar API for real citation data (slower but better quality)
    """
    from src.index.builder import IndexBuilder
    from src.graph.enhanced_citation_graph import EnhancedCitationGraph
    from src.graph.pagerank import PageRank
    import orjson
    
    index_dir = settings.DATA_DIR / "index"
    pagerank_dir = settings.DATA_DIR / "pagerank"
    
    if index_dir.exists() and pagerank_dir.exists() and not rebuild:
        typer.echo("Index already exists. Use --rebuild to force rebuild.")
        return
    
    typer.echo("Building inverted index...")
    builder = IndexBuilder(settings.DATA_DIR)
    idx = builder.build()
    typer.echo(f"Index built: {idx.num_docs} docs, {len(idx.index)} terms, avg_dl={idx.avg_doc_length:.1f}")
    
    if real_citations:
        typer.echo("\nBuilding citation graph with REAL citation data from Semantic Scholar...")
        typer.echo("(This may take 1-2 hours due to API rate limits)")
    else:
        typer.echo("\nBuilding citation graph with co-citation (papers sharing 2+ categories)...")
    
    graph = EnhancedCitationGraph()
    graph.build_from_papers(settings.DATA_DIR / "papers", use_real_citations=real_citations)
    
    typer.echo(f"Graph built: {len(graph.nodes)} nodes, {sum(len(edges) for edges in graph.graph.values())} edges")
    
    typer.echo("\nComputing PageRank...")
    pr = PageRank()
    scores = pr.compute(graph)
    
    pagerank_dir.mkdir(parents=True, exist_ok=True)
    (pagerank_dir / "scores.json").write_bytes(orjson.dumps(scores, option=orjson.OPT_INDENT_2))
    
    # Save citation counts if using real data
    if real_citations and graph.citation_counts:
        (pagerank_dir / "citation_counts.json").write_bytes(
            orjson.dumps(graph.citation_counts, option=orjson.OPT_INDENT_2)
        )
        typer.echo(f"Citation counts saved for {len(graph.citation_counts)} papers")
    
    typer.echo(f"PageRank computed: {len(scores)} nodes")

@app.command()
def serve(port: int = 8000, host: str = "0.0.0.0", enhanced: bool = True):
    """
    Start the FastAPI search server.
    
    Args:
        port: Port to bind to
        host: Host to bind to
        enhanced: Use enhanced API with query expansion and similar papers
    """
    import uvicorn
    
    if enhanced:
        typer.echo(f"Starting ENHANCED search API on {host}:{port}")
        typer.echo("Features: Query expansion, similar papers, result caching")
        uvicorn.run("src.api.enhanced_main:app", host=host, port=port, reload=False)
    else:
        typer.echo(f"Starting basic search API on {host}:{port}")
        uvicorn.run("src.api.main:app", host=host, port=port, reload=False)

@app.command()
def stats():
    """Print corpus and index statistics."""
    import orjson
    papers_dir = settings.DATA_DIR / "papers"
    index_dir = settings.DATA_DIR / "index"
    pagerank_dir = settings.DATA_DIR / "pagerank"
    
    if not papers_dir.exists():
        typer.echo("No data directory found. Run 'crawl' first.")
        return
    
    paper_count = len(list(papers_dir.glob("*.json")))
    typer.echo(f"Papers crawled: {paper_count}")
    
    if index_dir.exists():
        metadata = orjson.loads((index_dir / "metadata.json").read_bytes())
        typer.echo(f"Terms indexed: {len(metadata['idf_cache'])}")
        typer.echo(f"Avg document length: {metadata['avg_doc_length']:.1f} tokens")
    
    if pagerank_dir.exists():
        scores = orjson.loads((pagerank_dir / "scores.json").read_bytes())
        typer.echo(f"PageRank scores: {len(scores)} papers")
        
        citation_counts_path = pagerank_dir / "citation_counts.json"
        if citation_counts_path.exists():
            citation_counts = orjson.loads(citation_counts_path.read_bytes())
            avg_citations = sum(citation_counts.values()) / len(citation_counts)
            typer.echo(f"Avg citations per paper: {avg_citations:.1f}")

if __name__ == "__main__":
    app()
