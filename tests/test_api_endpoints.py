import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["status"] == "UP"
    assert "embeddingProvider" in data["data"]

def test_list_documents_endpoint():
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

def test_auth_login():
    res = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "accessToken" in data["data"]

def test_upload_and_chat_e2e():
    sample_pdf = Path(__file__).resolve().parent.parent / "sample_documents" / "sample_ai_research.pdf"
    assert sample_pdf.exists()

    # 1. Upload
    with open(sample_pdf, "rb") as f:
        res = client.post("/api/v1/documents/upload", files={"file": ("sample_ai_research.pdf", f, "application/pdf")})
    assert res.status_code == 200
    upload_data = res.json()
    assert upload_data["success"] is True
    doc_id = upload_data["data"]["id"]
    assert upload_data["data"]["chunksCreated"] > 0

    # 2. Get document metadata
    doc_res = client.get(f"/api/v1/documents/{doc_id}")
    assert doc_res.status_code == 200
    assert doc_res.json()["data"]["filename"] == "sample_ai_research.pdf"

    # 3. Get Chunks
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    assert len(chunks_res.json()["data"]) > 0

    # 4. Search
    search_res = client.post("/api/v1/chat/search", json={
        "query": "DPR bi-encoder",
        "documentId": doc_id,
        "topK": 3
    })
    assert search_res.status_code == 200
    assert search_res.json()["data"]["totalMatches"] > 0

    # 5. Query / Chat
    chat_res = client.post("/api/v1/chat/query", json={
        "question": "What is the Exact Match score achieved by RAG on Natural Questions?",
        "documentId": doc_id,
        "topK": 3
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()["data"]
    assert "44.5%" in chat_data["answer"] or "Natural Questions" in chat_data["answer"]
    assert len(chat_data["citations"]) > 0
    assert chat_data["citations"][0]["pageNumber"] in [1, 2]
