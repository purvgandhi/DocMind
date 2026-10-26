import pytest
from app.models.schemas import ChatRequestDto, SearchRequestDto
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_service import RagService

def test_rag_pipeline_search_and_query(tmp_path):
    vec_store = VectorStore(tmp_path)
    emb_service = EmbeddingService()
    rag_service = RagService(vec_store, emb_service)

    chunks = [
        {
            "documentId": "test-doc-1",
            "fileName": "sample_ai_research.pdf",
            "chunkIndex": 0,
            "pageNumber": 1,
            "text": "Retrieval-Augmented Generation (RAG) combines a Dense Passage Retriever (DPR) with a sequence-to-sequence BART-large generator."
        },
        {
            "documentId": "test-doc-1",
            "fileName": "sample_ai_research.pdf",
            "chunkIndex": 1,
            "pageNumber": 2,
            "text": "On the Natural Questions benchmark, RAG achieved 44.5% Exact Match, outperforming closed-book T5-11B by 10.0 points."
        }
    ]

    texts = [c["text"] for c in chunks]
    vectors = emb_service.embed_texts(texts)
    vec_store.add_chunks(chunks, vectors)

    # Test Search
    s_req = SearchRequestDto(query="What is the score on Natural Questions?", topK=2)
    s_res = rag_service.search_passages(s_req)
    assert s_res.totalMatches > 0
    assert s_res.matches[0].pageNumber in [1, 2]

    # Test Chat Q&A
    c_req = ChatRequestDto(question="What model does RAG use for generation?", topK=2)
    c_res = rag_service.ask_question(c_req)
    assert c_res.answer != ""
    assert len(c_res.citations) > 0
    assert c_res.responseTimeMs >= 0
    assert c_res.citations[0].fileName == "sample_ai_research.pdf"
