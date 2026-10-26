import pytest
from app.services.chunking_service import ChunkingService

def test_chunking_overlap_and_metadata():
    chunker = ChunkingService(chunk_size=300, chunk_overlap=50)
    pages_data = [
        {
            "pageNumber": 1,
            "text": "Paragraph one discusses retrieval-augmented generation. " * 5,
            "charCount": 275
        },
        {
            "pageNumber": 2,
            "text": "Paragraph two explores empirical results on Natural Questions and TriviaQA benchmarks. " * 6,
            "charCount": 528
        }
    ]

    chunks = chunker.chunk_document("doc-123", pages_data)
    assert len(chunks) >= 2
    for idx, c in enumerate(chunks):
        assert c["documentId"] == "doc-123"
        assert c["chunkIndex"] == idx
        assert c["pageNumber"] in [1, 2]
        assert len(c["text"]) > 20

def test_chunking_short_text():
    chunker = ChunkingService(chunk_size=700, chunk_overlap=100)
    pages_data = [{
        "pageNumber": 1,
        "text": "Short document summary text exceeding twenty chars.",
        "charCount": 51
    }]
    chunks = chunker.chunk_document("doc-short", pages_data)
    assert len(chunks) == 1
    assert chunks[0]["pageNumber"] == 1
    assert chunks[0]["text"] == pages_data[0]["text"]
