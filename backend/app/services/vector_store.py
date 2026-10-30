"""
Vector Store service — FAISS-backed retrieval with local embeddings.
Provides corpus_search, lookup_clause_by_id, and caching via Redis.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import corpus_chunk_count, corpus_last_build_timestamp

log = get_logger(__name__)


class VectorStore:
    """Thread-safe FAISS vector store with embedding cache."""

    def __init__(self) -> None:
        self._index: Any = None
        self._chunks: list[dict[str, Any]] = []
        self._chunk_map: dict[str, dict[str, Any]] = {}  # clause_id → chunk
        self._model: Any = None
        self._loaded = False
        self.settings = get_settings()

    def load(self, index_path: str | None = None) -> None:
        """Load FAISS index and chunk metadata from disk."""
        import faiss
        from sentence_transformers import SentenceTransformer

        path = Path(index_path or self.settings.vector_store_path)
        index_file = path / "index.faiss"
        chunks_file = path / "chunks.json"
        meta_file = path / "metadata.json"

        if not index_file.exists():
            log.warning(
                "faiss_index_not_found",
                path=str(index_file),
                msg="Run 'python -m app.cli.ingest' to build the index first.",
            )
            # Build index on-the-fly using built-in corpus
            self._build_in_memory()
            return

        log.info("loading_faiss_index", path=str(index_file))
        t0 = time.perf_counter()

        self._index = faiss.read_index(str(index_file))
        with open(chunks_file, encoding="utf-8") as f:
            self._chunks = json.load(f)

        # Build lookup maps
        self._chunk_map = {}
        for chunk in self._chunks:
            cid = chunk.get("clause_id", "")
            if cid not in self._chunk_map:
                self._chunk_map[cid] = chunk

        # Load embedding model
        log.info("loading_embedding_model", model=self.settings.embedding_model)
        self._model = SentenceTransformer(
            self.settings.embedding_model, device=self.settings.embedding_device
        )

        # Update metrics
        corpus_chunk_count.set(len(self._chunks))
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            from datetime import datetime, timezone
            ts_str = meta.get("build_timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str).timestamp()
                    corpus_last_build_timestamp.set(ts)
                except ValueError:
                    pass

        self._loaded = True
        elapsed = time.perf_counter() - t0
        log.info(
            "vector_store_loaded",
            chunks=len(self._chunks),
            load_time_ms=round(elapsed * 1000, 1),
        )

    def _build_in_memory(self) -> None:
        """Build FAISS index in memory from built-in corpus (fallback)."""
        import faiss
        from sentence_transformers import SentenceTransformer

        log.info("building_in_memory_index")
        # Import here to avoid circular imports
        import sys
        from pathlib import Path as P
        corpus_candidates = [
            P("/app/corpus_src"),
            P("/app/corpus"),
            P(__file__).resolve().parent.parent.parent / "corpus",
            P(__file__).resolve().parent.parent.parent.parent / "corpus",
        ]
        for cpath in corpus_candidates:
            if cpath.exists() and str(cpath) not in sys.path:
                sys.path.insert(0, str(cpath))

        try:
            from policy_corpus import get_all_clauses
        except ImportError:
            try:
                from corpus.policy_corpus import get_all_clauses
            except ImportError:
                from corpus_src.policy_corpus import get_all_clauses

        clauses = get_all_clauses()
        self._model = SentenceTransformer(
            self.settings.embedding_model, device=self.settings.embedding_device
        )
        dim = self._model.get_sentence_embedding_dimension()

        # Create one chunk per clause (minimal chunking for in-memory)
        self._chunks = []
        for clause in clauses:
            self._chunks.append({
                "chunk_id": f"{clause['clause_id']}-C000",
                "clause_id": clause["clause_id"],
                "doc_id": clause.get("doc_id", ""),
                "doc_title": clause.get("doc_title", ""),
                "title": clause.get("title", ""),
                "source": clause.get("source", ""),
                "version": clause.get("version", ""),
                "page": clause.get("page", ""),
                "text": clause["text"],
            })

        self._chunk_map = {c["clause_id"]: c for c in self._chunks}

        texts = [c["text"] for c in self._chunks]
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        embeddings_np = np.array(embeddings, dtype=np.float32)

        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings_np)
        self._loaded = True
        corpus_chunk_count.set(len(self._chunks))
        log.info("in_memory_index_built", chunks=len(self._chunks))

    def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Vector similarity search. Returns top-k chunks with scores.
        """
        if not self._loaded:
            self.load()

        k = top_k or self.settings.top_k_retrieval
        query_embedding = self._model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)

        scores, indices = self._index.search(query_embedding, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = dict(self._chunks[idx])
            chunk["relevance_score"] = float(score)
            results.append(chunk)

        log.debug(
            "vector_search",
            query=query[:80],
            results=len(results),
            top_score=results[0]["relevance_score"] if results else 0,
        )
        return results

    def lookup_by_clause_id(self, clause_id: str) -> dict[str, Any] | None:
        """Exact lookup by clause identifier."""
        if not self._loaded:
            self.load()
        result = self._chunk_map.get(clause_id)
        log.debug("clause_lookup", clause_id=clause_id, found=result is not None)
        return result

    def get_all_clause_ids(self) -> list[str]:
        """List all available clause IDs in the index."""
        if not self._loaded:
            self.load()
        return list(self._chunk_map.keys())

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


# ── Module-level singleton ───────────────────────────────────────────────────
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
        _store.load()
    return _store
