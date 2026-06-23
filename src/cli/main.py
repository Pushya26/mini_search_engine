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
def index(rebuild: bool = False):
    """Build inverted index and PageRank scores."""
    from src.index.builder import IndexBuilder
    from src.graph.citation_graph import CitationGraph
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
    
    typer.echo("\nBuilding citation graph and computing PageRank...")
    graph = CitationGraph()
    graph.build_from_papers(settings.DATA_DIR / "papers")
    
    pr = PageRank()
    scores = pr.compute(graph)
    
    pagerank_dir.mkdir(parents=True, exist_ok=True)
    (pagerank_dir / "scores.json").write_bytes(orjson.dumps(scores, option=orjson.OPT_INDENT_2))
    
    typer.echo(f"PageRank computed: {len(scores)} nodes")

@app.command()
def serve(port: int = 8000, host: str = "0.0.0.0"):
    """Start the FastAPI search server."""
    import uvicorn
    typer.echo(f"Starting search API on {host}:{port}")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=False)

@app.command()
def stats():
    """Print corpus and index statistics."""
    from pathlib import Path
    papers_dir = settings.DATA_DIR / "papers"
    
    if not papers_dir.exists():
        typer.echo("No data directory found. Run 'crawl' first.")
        return
    
    paper_count = len(list(papers_dir.glob("*.json")))
    typer.echo(f"Papers crawled: {paper_count}")

if __name__ == "__main__":
    app()
