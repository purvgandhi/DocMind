import os
import time
import uuid
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.config import settings
from app.models.schemas import ChatRequestDto, ChatResponseDto, CitationDto, SearchRequestDto, SearchResultDto
from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RagService:
    """
    Core Retrieval-Augmented Generation (RAG) Service for DocMind.
    Performs vector similarity search, context grounding, answer generation,
    and verifiable source citation attribution.
    """

    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def search_passages(self, request: SearchRequestDto) -> SearchResultDto:
        """
        Executes semantic search over indexed document chunks.
        """
        query_vector = self.embedding_service.embed_query(request.query)
        matches_raw = self.vector_store.search(
            query_vector=query_vector,
            top_k=request.topK or settings.top_k,
            min_similarity=request.similaritySearch or settings.min_similarity,
            document_id=request.documentId
        )

        citations = []
        for m in matches_raw:
            citations.append(CitationDto(
                documentId=m.get("documentId", ""),
                fileName=m.get("fileName", "Document"),
                chunkIndex=m.get("chunkIndex", 0),
                pageNumber=m.get("pageNumber", 1),
                snippet=m.get("text", "")[:350],
                similarityScore=m.get("similarityScore", 0.0),
                metadata={"charCount": m.get("charCount", len(m.get("text", "")))}
            ))

        return SearchResultDto(
            query=request.query,
            totalMatches=len(citations),
            matches=citations
        )

    def ask_question(self, request: ChatRequestDto) -> ChatResponseDto:
        """
        Main Q&A pipeline:
        1. Embed question
        2. Retrieve top-k relevant document chunks
        3. Synthesize grounded answer
        4. Package citations and latency
        """
        start_time = time.time()
        conv_id = request.conversationId or str(uuid.uuid4())

        # 1. Embed query
        query_vec = self.embedding_service.embed_query(request.question)

        # 2. Retrieve relevant chunks
        top_k = request.topK or settings.top_k
        min_sim = request.minSimilarity or settings.min_similarity
        matched_chunks = self.vector_store.search(
            query_vector=query_vec,
            top_k=top_k,
            min_similarity=min_sim,
            document_id=request.documentId
        )

        # 3. Format citations
        citations: List[CitationDto] = []
        for m in matched_chunks:
            snippet = m.get("text", "")[:350].strip()
            if len(m.get("text", "")) > 350:
                snippet += "..."
            citations.append(CitationDto(
                documentId=m.get("documentId", ""),
                fileName=m.get("fileName", "Document"),
                chunkIndex=m.get("chunkIndex", 0),
                pageNumber=m.get("pageNumber", 1),
                snippet=snippet,
                similarityScore=m.get("similarityScore", 0.0),
                metadata={"charCount": m.get("charCount", 0)}
            ))

        # 4. Generate answer grounded in context
        if not matched_chunks:
            answer = (
                "I could not find any relevant information in the uploaded document(s) matching your question. "
                "Please verify that the document has been fully indexed, or try rephrasing your query."
            )
        else:
            answer = self._generate_grounded_answer(request.question, matched_chunks)

        latency_ms = int((time.time() - start_time) * 1000)

        return ChatResponseDto(
            answer=answer,
            conversationId=conv_id,
            citations=citations,
            responseTimeMs=latency_ms
        )

    def _generate_grounded_answer(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Generates answer via configured LLM if available, otherwise employs
        high-fidelity local extractive and contextual grounding.
        """
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

        # Try OpenAI if valid key provided
        if openai_key and openai_key != "demo-key":
            try:
                import requests
                context_str = "\n\n---\n\n".join(
                    [f"[Page {c.get('pageNumber', 1)}, Chunk {c.get('chunkIndex', 0)}]: {c.get('text', '')}" for c in chunks]
                )
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.openai_chat_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are DocMind, an intelligent document QA assistant. "
                                "Answer the user question accurately and truthfully using ONLY the provided document context. "
                                "Always cite the specific page numbers [Page X] when stating facts."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Document Context:\n{context_str}\n\nQuestion: {question}"
                        }
                    ],
                    "temperature": 0.2
                }
                res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenAI call failed ({e}). Falling back to local grounded synthesis.")

        # Local Grounded QA Synthesizer (Zero hallucination, fully grounded in retrieved chunks)
        return self._synthesize_local_grounded_answer(question, chunks)

    def _synthesize_local_grounded_answer(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesizes a structured, highly factual answer directly from retrieved chunks
        with explicit page grounding and semantic sentence ranking.
        """
        top_chunk = chunks[0]
        page_refs = sorted(list(set(c.get("pageNumber", 1) for c in chunks)))
        pages_str = ", ".join([f"Page {p}" for p in page_refs])

        # Tokenize question terms
        stop_words = {"what", "is", "the", "a", "an", "how", "does", "explain", "in", "of", "and", "to", "for", "with", "are"}
        q_terms = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_-]+\b', question) if w.lower() not in stop_words and len(w) > 2]

        # Extract best matching sentences across retrieved chunks
        best_sentences: List[Tuple[str, int, float]] = []

        for chunk in chunks[:3]:
            page_no = chunk.get("pageNumber", 1)
            text = chunk.get("text", "")
            raw_sents = re.split(r'(?<=[.!?])\s+', text)
            for sent in raw_sents:
                clean_s = sent.strip()
                if len(clean_s) < 25 or clean_s.endswith(":") or clean_s.isdigit():
                    continue

                # Score sentence by overlap with question terms + density
                s_lower = clean_s.lower()
                overlap = sum(1 for term in q_terms if term in s_lower)
                if overlap > 0:
                    score = overlap * 1.5 + (chunk.get("similarityScore", 0.5))
                    best_sentences.append((clean_s, page_no, score))

        best_sentences.sort(key=lambda x: x[2], reverse=True)

        # Deduplicate sentences while preserving top content
        selected_sents = []
        seen_texts = set()
        for s, p, sc in best_sentences:
            normalized = s[:50].lower()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                selected_sents.append((s, p))
            if len(selected_sents) >= 4:
                break

        # Build response body
        if selected_sents:
            synthesized_body = " ".join([s for s, p in selected_sents])
            primary_answer = f"Based on {pages_str} of the document:\n\n{synthesized_body}"
        else:
            # Fallback to the most representative excerpt of top chunk
            top_snippet = top_chunk.get("text", "").strip()
            first_para = top_snippet.split("\n\n")[0]
            primary_answer = f"Based on {pages_str} of the document:\n\n{first_para}"

        answer = (
            f"{primary_answer}\n\n"
            f"**Source Provenance:** Grounded in {len(chunks)} retrieved passage(s) "
            f"({pages_str}, Top Similarity Score: {top_chunk.get('similarityScore', 0.0):.4f})."
        )
        return answer
