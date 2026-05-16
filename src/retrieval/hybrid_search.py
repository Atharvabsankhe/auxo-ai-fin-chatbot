from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict
from src.models import DocumentChunk
from src.retrieval.vector_store import VectorStore


class HybridRetriever:
    """Combines dense (Gemini embeddings) and sparse (BM25) retrieval with RRF."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.chunks: List[DocumentChunk] = []
        self.bm25 = None

    def index_chunks(self, chunks: List[DocumentChunk]):
        self.chunks.extend(chunks)

        # Rebuild BM25 index over all chunks
        tokenized_corpus = [chunk.content.lower().split() for chunk in self.chunks]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

        # Add to vector store (handles batching internally)
        self.vector_store.add_chunks(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.chunks or self.bm25 is None:
            return []

        # --- Dense search ---
        dense_results = self.vector_store.search(query, top_k=top_k * 2)

        # --- Sparse search (BM25) ---
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        top_n = np.argsort(bm25_scores)[::-1][: top_k * 2]
        sparse_results = []
        for idx in top_n:
            if bm25_scores[idx] > 0:
                chunk = self.chunks[idx]
                sparse_results.append({
                    "id": chunk.id,
                    "content": chunk.content,
                    "metadata": {
                        "source": chunk.source,
                        "page": chunk.page if chunk.page is not None else -1,
                        "type": chunk.type,
                        "quarter": chunk.quarter or "Unknown",
                    },
                    "bm25_score": float(bm25_scores[idx]),
                })

        # --- Reciprocal Rank Fusion ---
        return self._rrf(dense_results, sparse_results, top_k)

    @staticmethod
    def _rrf(dense_results: List[Dict], sparse_results: List[Dict], top_k: int, k: int = 60) -> List[Dict]:
        """Reciprocal Rank Fusion to merge dense and sparse results."""
        scores: Dict[str, dict] = {}

        for rank, res in enumerate(dense_results):
            doc_id = res["id"]
            if doc_id not in scores:
                scores[doc_id] = {"score": 0.0, "doc": res}
            scores[doc_id]["score"] += 1.0 / (k + rank + 1)

        for rank, res in enumerate(sparse_results):
            doc_id = res["id"]
            if doc_id not in scores:
                scores[doc_id] = {"score": 0.0, "doc": res}
            scores[doc_id]["score"] += 1.0 / (k + rank + 1)

        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_results[:top_k]]
