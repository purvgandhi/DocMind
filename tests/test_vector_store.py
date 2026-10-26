import numpy as np
import pytest
from app.services.vector_store import VectorStore

def test_vector_store_add_search_and_delete(tmp_path):
    store = VectorStore(tmp_path)

    chunks = [
        {"documentId": "doc-A", "chunkIndex": 0, "pageNumber": 1, "text": "Neural retrieval DPR bi-encoder"},
        {"documentId": "doc-A", "chunkIndex": 1, "pageNumber": 2, "text": "Natural Questions benchmark results 44.5 EM"},
        {"documentId": "doc-B", "chunkIndex": 0, "pageNumber": 1, "text": "Unrelated culinary recipe for pasta"}
    ]

    # Deterministic vectors (384-d)
    v1 = np.zeros(384, dtype=np.float32); v1[10] = 1.0; v1[20] = 0.5
    v2 = np.zeros(384, dtype=np.float32); v2[10] = 0.8; v2[30] = 0.6
    v3 = np.zeros(384, dtype=np.float32); v3[100] = 1.0

    vectors = np.array([v1, v2, v3], dtype=np.float32)
    store.add_chunks(chunks, vectors)

    assert len(store.chunks) == 3

    # Query close to v1/v2
    q_vec = np.zeros(384, dtype=np.float32); q_vec[10] = 1.0
    results = store.search(q_vec, top_k=2)

    assert len(results) == 2
    assert results[0]["documentId"] == "doc-A"
    assert results[0]["similarityScore"] > 0.5

    # Filter by documentId
    scoped_results = store.search(q_vec, top_k=5, document_id="doc-B")
    assert len(scoped_results) == 1
    assert scoped_results[0]["documentId"] == "doc-B"

    # Delete doc-A
    store.delete_document_chunks("doc-A")
    assert len(store.chunks) == 1
    assert store.chunks[0]["documentId"] == "doc-B"
