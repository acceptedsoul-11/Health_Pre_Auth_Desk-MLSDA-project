"""
CLI Ingestion Pipeline (D2) — idempotent corpus indexing tool.
Usage:
    python -m app.cli.ingest [--corpus-path PATH] [--force-rebuild]

Tracks and exposes:
  - Build timestamp
  - Source version
  - Chunk count
  - Throughput (chunks/sec)
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

# Patch path for CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

console = Console()


def _load_corpus() -> list[dict[str, Any]]:
    """Load corpus from structured Python module or PDFs."""
    try:
        # Try to load from corpus directory PDF files first
        for cdir in [
            Path("/app/corpus_src/raw"),
            Path("/app/corpus/raw"),
            Path(__file__).resolve().parent.parent.parent / "corpus" / "raw",
            Path(__file__).resolve().parent.parent.parent.parent / "corpus" / "raw",
        ]:
            if cdir.exists():
                pdfs = list(cdir.glob("*.pdf"))
                if pdfs:
                    return _load_from_pdfs(pdfs)
    except Exception as e:
        console.print(f"[yellow]PDF loading failed ({e}), using built-in corpus.[/yellow]")

    # Fall back to built-in synthetic corpus
    import sys
    for cpath in [
        Path("/app/corpus_src"),
        Path("/app/corpus"),
        Path(__file__).resolve().parent.parent.parent / "corpus",
        Path(__file__).resolve().parent.parent.parent.parent / "corpus",
    ]:
        if cpath.exists() and str(cpath) not in sys.path:
            sys.path.insert(0, str(cpath))

    try:
        from policy_corpus import get_all_clauses
        return get_all_clauses()
    except ImportError:
        try:
            from corpus.policy_corpus import get_all_clauses
            return get_all_clauses()
        except ImportError:
            from corpus_src.policy_corpus import get_all_clauses
            return get_all_clauses()


def _load_from_pdfs(pdf_paths: list[Path]) -> list[dict[str, Any]]:
    """Extract text from PDFs using pdfplumber."""
    import pdfplumber
    clauses = []
    for pdf_path in pdf_paths:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    clauses.append({
                        "clause_id": f"PDF-{pdf_path.stem}-P{page_num:03d}",
                        "title": f"{pdf_path.stem} — Page {page_num}",
                        "text": text.strip(),
                        "doc_id": pdf_path.stem,
                        "doc_title": pdf_path.stem,
                        "source": str(pdf_path),
                        "version": "pdf-extracted",
                        "page": str(page_num),
                    })
    return clauses


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += chunk_size - chunk_overlap
    return chunks


def _build_index(
    clauses: list[dict[str, Any]],
    output_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    embedding_device: str,
) -> dict[str, Any]:
    """
    Build FAISS index from clauses.
    Returns metadata dict.
    """
    import faiss
    from sentence_transformers import SentenceTransformer

    console.print(f"\n[cyan]Loading embedding model: {embedding_model}[/cyan]")
    model = SentenceTransformer(embedding_model, device=embedding_device)
    dim = model.get_sentence_embedding_dimension()
    console.print(f"[green]Model loaded. Embedding dimension: {dim}[/green]")

    # ── Chunk all clauses ─────────────────────────────────────────────────────
    all_chunks: list[dict[str, Any]] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Chunking documents...", total=len(clauses))
        for clause in clauses:
            text = clause["text"]
            # Rough word-count-based chunking (approx tokens)
            chunks = _chunk_text(text, chunk_size=chunk_size // 4, chunk_overlap=chunk_overlap // 4)
            for i, chunk_text in enumerate(chunks):
                all_chunks.append({
                    "chunk_id": f"{clause['clause_id']}-C{i:03d}",
                    "clause_id": clause["clause_id"],
                    "doc_id": clause.get("doc_id", ""),
                    "doc_title": clause.get("doc_title", ""),
                    "title": clause.get("title", ""),
                    "source": clause.get("source", ""),
                    "version": clause.get("version", ""),
                    "page": clause.get("page", ""),
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                })
            progress.advance(task)

    console.print(f"[green]Total chunks: {len(all_chunks)}[/green]")

    # ── Embed chunks ─────────────────────────────────────────────────────────
    texts = [c["text"] for c in all_chunks]
    t0 = time.perf_counter()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding chunks...", total=len(texts))
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        progress.update(task, completed=len(texts))

    elapsed = time.perf_counter() - t0
    throughput = len(all_chunks) / elapsed if elapsed > 0 else 0

    # ── Build FAISS index ─────────────────────────────────────────────────────
    console.print("[cyan]Building FAISS index (IndexFlatIP for cosine similarity)...[/cyan]")
    embeddings_np = np.array(embeddings, dtype=np.float32)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_np)

    # ── Persist ────────────────────────────────────────────────────────────────
    output_path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_path / "index.faiss"))

    # Save chunk metadata
    with open(output_path / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    # Save build metadata
    build_ts = datetime.now(timezone.utc).isoformat()
    versions = list({c.get("version", "unknown") for c in clauses})
    metadata = {
        "build_timestamp": build_ts,
        "source_versions": versions,
        "chunk_count": len(all_chunks),
        "clause_count": len(clauses),
        "embedding_model": embedding_model,
        "embedding_device": embedding_device,
        "embedding_dim": dim,
        "chunk_size_words": chunk_size // 4,
        "chunk_overlap_words": chunk_overlap // 4,
        "throughput_chunks_per_sec": round(throughput, 2),
        "index_type": "IndexFlatIP",
        "faiss_index_path": str(output_path / "index.faiss"),
        "chunks_json_path": str(output_path / "chunks.json"),
    }
    with open(output_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


@click.command()
@click.option(
    "--output-path",
    default=None,
    help="Output directory for FAISS index. Defaults to corpus/processed/faiss_index",
)
@click.option(
    "--chunk-size",
    default=512,
    type=int,
    show_default=True,
    help="Target chunk size in tokens (approximate)",
)
@click.option(
    "--chunk-overlap",
    default=64,
    type=int,
    show_default=True,
    help="Overlap between consecutive chunks in tokens",
)
@click.option(
    "--embedding-model",
    default="all-MiniLM-L6-v2",
    show_default=True,
    help="SentenceTransformer model name",
)
@click.option(
    "--embedding-device",
    default="cpu",
    show_default=True,
    help="Device for embedding (cpu/cuda)",
)
@click.option(
    "--force-rebuild",
    is_flag=True,
    default=False,
    help="Force rebuild even if index already exists",
)
def main(
    output_path: str | None,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    embedding_device: str,
    force_rebuild: bool,
) -> None:
    """
    Idempotent corpus ingestion pipeline for the Pre-Authorization Desk.

    Parses, chunks, embeds, and indexes the Star Health Insurance corpus
    into a FAISS vector store using local embedding models (zero API cost).
    """
    console.print("\n[bold blue]═══ Health Insurance Pre-Auth Corpus Ingestion ═══[/bold blue]\n")

    # Resolve output path
    if output_path is None:
        base = Path(__file__).resolve().parent.parent.parent.parent
        out_dir = base / "corpus" / "processed" / "faiss_index"
    else:
        out_dir = Path(output_path)

    # Idempotency check
    metadata_path = out_dir / "metadata.json"
    if metadata_path.exists() and not force_rebuild:
        with open(metadata_path) as f:
            existing = json.load(f)
        console.print(
            f"[yellow]Index already exists (built: {existing.get('build_timestamp', 'unknown')}, "
            f"chunks: {existing.get('chunk_count', 0)}). Use --force-rebuild to overwrite.[/yellow]"
        )
        _print_metadata_table(existing)
        return

    # Load corpus
    console.print("[cyan]Loading corpus...[/cyan]")
    clauses = _load_corpus()
    console.print(f"[green]Loaded {len(clauses)} clauses/sections.[/green]")

    # Build index
    metadata = _build_index(
        clauses=clauses,
        output_path=out_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
        embedding_device=embedding_device,
    )

    # Display results
    console.print("\n[bold green]✓ Ingestion complete![/bold green]\n")
    _print_metadata_table(metadata)


def _print_metadata_table(metadata: dict[str, Any]) -> None:
    table = Table(title="Index Metadata", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Build Timestamp", metadata.get("build_timestamp", "N/A"))
    table.add_row("Source Versions", str(metadata.get("source_versions", [])))
    table.add_row("Clause Count", str(metadata.get("clause_count", "N/A")))
    table.add_row("Chunk Count", str(metadata.get("chunk_count", "N/A")))
    table.add_row("Embedding Model", str(metadata.get("embedding_model", "N/A")))
    table.add_row("Embedding Dim", str(metadata.get("embedding_dim", "N/A")))
    table.add_row(
        "Throughput (chunks/sec)",
        str(metadata.get("throughput_chunks_per_sec", "N/A")),
    )
    table.add_row("Index Type", str(metadata.get("index_type", "N/A")))

    console.print(table)


if __name__ == "__main__":
    main()
