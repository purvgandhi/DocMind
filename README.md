# DocMind — AI-Powered Document Question-Answering System (Python RAG)

DocMind is an intelligent document question-answering system built on a complete, genuine Retrieval-Augmented Generation (RAG) architecture. Designed from scratch in Python to fulfill College AI Laboratory Experiment 10 requirements, DocMind replicates the full feature set, visual branding, and interactive workflows of the original Spring Boot application without relying on external Java wrappers.

---

## 🚀 Key Highlights & Architecture

- **PyMuPDF Document Ingestion**: Fast, robust PDF parsing with per-page text tracking, character counts, and corruption detection.
- **Context-Aware Semantic Chunking**: Recursive paragraph and sentence-aware segmentation (700-character chunk size with 100-character sliding window overlap) preserving source page numbers.
- **Dense Neural Vector Retrieval**: Local high-performance semantic embeddings powered by `all-MiniLM-L6-v2` (384-dimensional dense vectors) and NumPy/Cosine similarity search, with automatic zero-dependency Scikit-learn TF-IDF dense vector fallback.
- **Grounded Q&A Synthesis**: Contextually constrained answer generation with explicit page citations (`[Page X, Chunk Y]`), verbatim source snippet provenance, and confidence metrics.
- **Complete REST & SSE Streaming API**: Built with FastAPI, featuring interactive Swagger documentation (`/docs`), document upload/management, and Server-Sent Events (SSE).
- **DocMind Dark Theme UI**: Polished, responsive single-page dashboard featuring Document Chat, Clause/Fact Search, and Document Chunks Inspector.

---

## 📁 Project Structure

```
docmind-python/
├── app/
│   ├── main.py                     # FastAPI application entrypoint, CORS, routes & static mounting
│   ├── config.py                   # Pydantic Settings & environment configuration
│   ├── models/
│   │   └── schemas.py              # Pydantic schemas (ApiResponse, ChatRequestDto, CitationDto, etc.)
│   ├── routes/
│   │   ├── document_routes.py      # /api/v1/documents (upload, list, get, delete, chunks)
│   │   ├── chat_routes.py          # /api/v1/chat (query, search, stream)
│   │   └── auth_routes.py          # /api/v1/auth (login, register, me)
│   └── services/
│       ├── parser_service.py       # PyMuPDF PDF and text extraction with page tracking
│       ├── chunking_service.py     # Recursive character chunker with overlap
│       ├── embedding_service.py    # Local SentenceTransformer & TF-IDF dense vector fallback
│       ├── vector_store.py         # Cosine similarity vector index with disk persistence
│       ├── rag_service.py          # RAG orchestration, grounding, and citation formatting
│       └── document_metadata_service.py # Document state machine and storage
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/app.js               # Reactive client controller
│   │   └── assets/                 # Preserved branding (hero.png, favicon.svg, icons.svg)
│   └── templates/
│       └── index.html              # DocMind dark-slate dashboard (Chat, Search, Chunks)
├── sample_documents/
│   └── sample_ai_research.pdf      # Verifiable 2-page research paper on RAG & DPR
├── tests/
│   ├── test_parser.py              # PyMuPDF extraction tests
│   ├── test_chunker.py             # Chunking & overlap tests
│   ├── test_vector_store.py        # Vector similarity & filtering tests
│   ├── test_rag_pipeline.py        # End-to-end RAG Q&A tests
│   └── test_api_endpoints.py       # FastAPI TestClient integration tests
├── evidence/
│   └── experiment10/               # Genuine application screenshots & evaluation reports
├── evaluate.py                     # AI use case evaluation benchmark script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
└── README.md                       # Comprehensive guide
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.11)
- Modern web browser (Chrome, Edge, Firefox)

### 1. Clone or Extract Project
Navigate to the `docmind-python` directory:
```bash
cd docmind-python
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
*Note: The application operates completely offline with local dense embeddings and grounded synthesis. You do NOT need paid API keys to run or test the system.*

---

## ▶️ Running the Application

### Start the FastAPI Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Open the Application
- **DocMind Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📖 End-to-End Workflow Guide

### 1. Upload a Document
1. Click the **"Upload Document"** button in the top navbar.
2. Drag and drop `sample_documents/sample_ai_research.pdf` (or any custom PDF) into the dropzone.
3. Observe real-time progress: text extraction, chunking, and embedding generation.
4. The document is indexed and appears in the left sidebar with page and chunk counts.

### 2. Ask Questions (Document Chat)
1. Type a natural language question in the chat input bar, e.g.:
   - *"What is the Exact Match score achieved by RAG on Natural Questions?"*
   - *"What neural architectures form the retriever and generator in RAG?"*
2. Press **Ask**.
3. The RAG pipeline retrieves the top-k nearest semantic chunks and generates a grounded response.
4. Expand the **Supporting Sources & Page Citations** drawer to inspect exact page numbers, similarity scores, and verbatim passage snippets.

### 3. Search Clauses & Facts
1. Switch to the **Clause & Fact Search** tab.
2. Enter technical keywords (e.g. `"DPR bi-encoder"`, `"BART-large"`, `"marginalization"`).
3. Adjust the Top Results slider ($k$) or minimum similarity threshold.
4. View matching passages ranked by cosine similarity with match percentage bars.

### 4. Inspect Document Chunks
1. Switch to the **Document Chunks** tab.
2. Select your document from the dropdown.
3. Inspect how raw text was segmented into overlapping 700-character windows with page numbers.

---

## 🧪 Testing & Evaluation

### Run Automated Unit & Integration Tests
Execute all tests using `pytest`:
```bash
pytest -v
```

### Run the AI Use Case Evaluation Benchmark
Execute the reproducible evaluation script:
```bash
python evaluate.py
```
This evaluates the system on 5 verifiable factual queries against `sample_ai_research.pdf`, measuring:
- **Retrieval Recall@5**: Percentage of queries retrieving ground-truth passages.
- **Citation Page Accuracy**: Correctness of attributed page numbers.
- **Source Grounding Rate**: Absence of hallucinations.
- **Response Latency**: End-to-end processing time in milliseconds.

Results are displayed in a formatted console table and persisted to:
- `evidence/experiment10/evaluation_results.json`
- `evidence/experiment10/evaluation_results.md`

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed in active environment | Run `pip install -r requirements.txt` |
| `ValueError: Uploaded document is empty` | 0-byte or corrupted file uploaded | Ensure PDF contains readable text, not empty scans |
| Port 8000 already in use | Another service is using port 8000 | Run `python -m uvicorn app.main:app --port 8080` |
| Fallback to TF-IDF embedding | PyTorch / sentence-transformers downloading or unavailable | System automatically uses Scikit-learn TF-IDF dense vector retrieval without crashing |

---

## 📜 Compliance with College Experiment 10
- **Course**: Artificial Intelligence Laboratory (DJS23IPC302L)
- **Class**: TY-IT
- **Experiment No.**: 10
- **Use Case**: AI-Powered Document Question Answering (Retrieval-Augmented Generation)
- **Original Java Project**: Preserved 100% unchanged in reference directory.
