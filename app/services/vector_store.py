import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class VectorStore:
    """
    In-memory vector store with disk persistence, supporting cosine similarity
    and metadata filtering (matching DocMind's PGVector functionality).
    """

    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.storage_dir / "chunks_metadata.json"
        self.vec_file = self.storage_dir / "chunks_vectors.npy"

        self.chunks: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.empty((0, 384), dtype=np.float32)
        self._load()

    def add_chunks(self, chunks: List[Dict[str, Any]], vectors: np.ndarray):
        """
        Adds chunks and their corresponding normalized embedding vectors.
        """
        if not chunks:
            return

        if len(chunks) != len(vectors):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match vector count ({len(vectors)})")

        # Normalize vectors for cosine similarity (dot product = cosine similarity)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_vectors = (vectors / norms).astype(np.float32)

        self.chunks.extend(chunks)
        if self.vectors.shape[0] == 0:
            self.vectors = normalized_vectors
        else:
            if self.vectors.shape[1] != normalized_vectors.shape[1]:
                # Adapt dimension if needed
                min_dim = min(self.vectors.shape[1], normalized_vectors.shape[1])
                self.vectors = self.vectors[:, :min_dim]
                normalized_vectors = normalized_vectors[:, :min_dim]
            self.vectors = np.vstack([self.vectors, normalized_vectors])

        self._save()
        logger.info(f"Added {len(chunks)} chunks. Total chunks in vector store: {len(self.chunks)}")

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        min_similarity: float = 0.0,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for top_k most similar chunks using cosine similarity.
        Optionally filters by document_id.
        """
        if len(self.chunks) == 0 or self.vectors.shape[0] == 0:
            return []

        # Normalize query vector
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            q_norm = query_vector / norm
        else:
            q_norm = query_vector

        # Ensure dimension match
        dim = self.vectors.shape[1]
        if len(q_norm) != dim:
            if len(q_norm) > dim:
                q_norm = q_norm[:dim]
            else:
                padded = np.zeros(dim, dtype=np.float32)
                padded[:len(q_norm)] = q_norm
                q_norm = padded

        # Compute cosine similarities via dot product
        scores = np.dot(self.vectors, q_norm)

        # Filter by document_id and min_similarity
        candidates = []
        for idx, score in enumerate(scores):
            if score < min_similarity:
                continue

            chunk = self.chunks[idx]
            if document_id and chunk.get("documentId") != document_id:
                continue

            candidates.append({
                "chunk": chunk,
                "score": float(score)
            })

        # Sort descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[:top_k]

        results = []
        for cand in top_candidates:
            c = cand["chunk"].copy()
            c["similarityScore"] = round(cand["score"], 4)
            results.append(c)

        return results

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Returns all chunks belonging to a specific document."""
        return [c for c in self.chunks if c.get("documentId") == document_id]

    def delete_document_chunks(self, document_id: str):
        """Removes all chunks for a document."""
        keep_indices = [i for i, c in enumerate(self.chunks) if c.get("documentId") != document_id]
        if len(keep_indices) == len(self.chunks):
            return

        self.chunks = [self.chunks[i] for i in keep_indices]
        if len(keep_indices) > 0 and self.vectors.shape[0] > 0:
            self.vectors = self.vectors[keep_indices]
        else:
            self.vectors = np.empty((0, 384), dtype=np.float32)

        self._save()
        logger.info(f"Deleted chunks for document {document_id}. Remaining: {len(self.chunks)}")

    def _save(self):
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)
            np.save(str(self.vec_file), self.vectors)
        except Exception as e:
            logger.error(f"Failed to persist vector store: {e}")

    def _load(self):
        try:
            if self.meta_file.exists() and self.vec_file.exists():
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.vectors = np.load(str(self.vec_file))
                logger.info(f"Loaded {len(self.chunks)} existing chunks from vector store.")
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {e}")
            self.chunks = []
            self.vectors = np.empty((0, 384), dtype=np.float32)
