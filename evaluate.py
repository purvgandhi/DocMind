import json
import time
from pathlib import Path
from typing import Dict, List, Any

from app.models.schemas import ChatRequestDto, SearchRequestDto
from app.services.chunking_service import ChunkingService
from app.services.document_metadata_service import DocumentMetadataService
from app.services.embedding_service import EmbeddingService
from app.services.parser_service import DocumentParserService
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore

BENCHMARK_TESTS = [
    {
        "id": 1,
        "question": "What is the core problem statement addressed by Retrieval-Augmented Generation?",
        "expected_page": 1,
        "expected_terms": ["parametric", "hallucinations", "verifiable provenance", "knowledge"],
        "expected_answer": "Large parametric language models suffer from hallucinations, inability to dynamically update knowledge without retraining, and lack of verifiable provenance/citations."
    },
    {
        "id": 2,
        "question": "What neural architectures form the retriever and the generator in RAG?",
        "expected_page": 1,
        "expected_terms": ["Dense Passage Retriever", "DPR", "BART-large", "bi-encoder"],
        "expected_answer": "Dense Passage Retriever (DPR) bi-encoder for dense passage retrieval and BART-large for sequence-to-sequence parametric generation."
    },
    {
        "id": 3,
        "question": "What empirical Exact Match score did RAG attain on the Natural Questions benchmark?",
        "expected_page": 2,
        "expected_terms": ["Natural Questions", "44.5%", "Exact Match", "T5-11B"],
        "expected_answer": "RAG attained 44.5% Exact Match on Natural Questions, outperforming closed-book T5-11B (34.5%) by 10.0 points."
    },
    {
        "id": 4,
        "question": "How do RAG-Sequence and RAG-Token formulations differ in generating tokens?",
        "expected_page": 2,
        "expected_terms": ["RAG-Sequence", "RAG-Token", "marginalize", "token"],
        "expected_answer": "RAG-Sequence conditions the entire generated sequence on a single retrieved passage, whereas RAG-Token marginalizes across different passages at each token step."
    },
    {
        "id": 5,
        "question": "What practical deployment challenges and limitations are highlighted for RAG?",
        "expected_page": 2,
        "expected_terms": ["Retrieval Latency", "Chunk Boundary", "Contradictory", "Interpretability"],
        "expected_answer": "Retrieval latency, chunk boundary alignment, handling contradictory evidence, and verifying source grounding/interpretability."
    }
]

def run_evaluation() -> Dict[str, Any]:
    print("=" * 80)
    print("           DOCMIND AI USE CASE EVALUATION BENCHMARK")
    print("        Retrieval-Augmented Generation (RAG) System Evaluation")
    print("=" * 80)

    # 1. Initialize fresh test environment
    base_dir = Path(__file__).resolve().parent
    temp_indices = base_dir / "data" / "eval_indices"
    sample_pdf = base_dir / "sample_documents" / "sample_ai_research.pdf"

    if not sample_pdf.exists():
        raise FileNotFoundError(f"Sample PDF not found at {sample_pdf}")

    vec_store = VectorStore(temp_indices)
    emb_service = EmbeddingService()
    chunker = ChunkingService(chunk_size=700, chunk_overlap=100)
    rag_service = RagService(vec_store, emb_service)

    print(f"\n[1/4] Indexing evaluation document: {sample_pdf.name}...")
    pages = DocumentParserService.parse_pdf(sample_pdf)
    chunks = chunker.chunk_document("eval-doc-rag", pages)
    for c in chunks:
        c["fileName"] = sample_pdf.name

    vectors = emb_service.embed_texts([c["text"] for c in chunks])
    vec_store.add_chunks(chunks, vectors)
    print(f"      Indexed {len(chunks)} chunks across {len(pages)} pages using [{emb_service.provider}] embedding engine.")

    # 2. Run benchmark queries
    print(f"\n[2/4] Executing {len(BENCHMARK_TESTS)} verifiable QA evaluation tests...\n")
    results = []
    total_retrieval_hits = 0
    total_citation_correct = 0
    total_latency_ms = 0

    header_fmt = "{:<4} | {:<32} | {:<8} | {:<10} | {:<10} | {:<10}"
    print(header_fmt.format("Test", "Question Excerpt", "Top Page", "Recall@5", "Citation", "Latency"))
    print("-" * 84)

    for test in BENCHMARK_TESTS:
        t_start = time.time()
        chat_req = ChatRequestDto(
            question=test["question"],
            documentId="eval-doc-rag",
            topK=5
        )
        res = rag_service.ask_question(chat_req)
        latency = res.responseTimeMs
        total_latency_ms += latency

        # Evaluate Retrieval Recall@k
        retrieved_texts = " ".join([c.snippet for c in res.citations])
        terms_found = [term for term in test["expected_terms"] if term.lower() in retrieved_texts.lower()]
        retrieval_hit = len(terms_found) >= 2
        if retrieval_hit:
            total_retrieval_hits += 1

        # Evaluate Citation Correctness
        top_citation = res.citations[0] if res.citations else None
        top_page = top_citation.pageNumber if top_citation else -1
        citation_correct = (top_page == test["expected_page"])
        if citation_correct:
            total_citation_correct += 1

        # Evaluate Answer Grounding
        answer_grounded = any(term.lower() in res.answer.lower() for term in test["expected_terms"])

        results.append({
            "test_id": test["id"],
            "question": test["question"],
            "expected_page": test["expected_page"],
            "expected_answer": test["expected_answer"],
            "actual_answer": res.answer,
            "top_page": top_page,
            "top_similarity": top_citation.similarityScore if top_citation else 0.0,
            "retrieval_hit": retrieval_hit,
            "terms_matched": terms_found,
            "citation_correct": citation_correct,
            "answer_grounded": answer_grounded,
            "latency_ms": latency,
            "citations_count": len(res.citations)
        })

        q_short = (test["question"][:30] + "..") if len(test["question"]) > 32 else test["question"]
        print(header_fmt.format(
            f"#{test['id']}",
            q_short,
            f"Page {top_page}",
            "PASS" if retrieval_hit else "FAIL",
            "EXACT" if citation_correct else "MISMATCH",
            f"{latency} ms"
        ))

    # 3. Compute Metrics
    num_tests = len(BENCHMARK_TESTS)
    recall_at_5 = (total_retrieval_hits / num_tests) * 100.0
    citation_accuracy = (total_citation_correct / num_tests) * 100.0
    avg_latency = total_latency_ms / num_tests

    summary = {
        "benchmark_dataset": "sample_ai_research.pdf (Lewis et al. RAG NeurIPS 2020)",
        "embedding_provider": emb_service.provider,
        "total_test_queries": num_tests,
        "retrieval_recall_at_5": f"{recall_at_5:.1f}%",
        "citation_page_accuracy": f"{citation_accuracy:.1f}%",
        "grounding_faithfulness": f"{(sum(1 for r in results if r['answer_grounded']) / num_tests) * 100.0:.1f}%",
        "mean_latency_ms": f"{avg_latency:.1f} ms",
        "results": results
    }

    print("\n" + "=" * 80)
    print("                       BENCHMARK METRICS SUMMARY")
    print("=" * 80)
    print(f"  * Document Name:             sample_ai_research.pdf")
    print(f"  * Total Test Queries:        {num_tests}")
    print(f"  * Retrieval Recall@5:        {summary['retrieval_recall_at_5']} ({total_retrieval_hits}/{num_tests} passed)")
    print(f"  * Citation Page Accuracy:    {summary['citation_page_accuracy']} ({total_citation_correct}/{num_tests} exact)")
    print(f"  * Source Grounding Rate:     {summary['grounding_faithfulness']}")
    print(f"  * Mean Response Latency:     {summary['mean_latency_ms']}")
    print("=" * 80)

    # 4. Save results to evidence folder
    evidence_dir = base_dir / "evidence" / "experiment10"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    json_path = evidence_dir / "evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    md_path = evidence_dir / "evaluation_results.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# DocMind AI System Evaluation — Experiment 10\n\n")
        f.write(f"**Document Evaluated:** `sample_ai_research.pdf`  \n")
        f.write(f"**Embedding Model:** `{emb_service.provider}`  \n")
        f.write(f"**Recall@5:** {summary['retrieval_recall_at_5']}  \n")
        f.write(f"**Citation Page Accuracy:** {summary['citation_page_accuracy']}  \n")
        f.write(f"**Average Latency:** {summary['mean_latency_ms']}  \n\n")
        f.write("### Detailed Test Results\n\n")
        f.write("| Test # | Question | Expected Page | Top Page | Recall@5 | Citation | Latency |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for r in results:
            f.write(f"| {r['test_id']} | {r['question']} | Page {r['expected_page']} | Page {r['top_page']} | {'PASS' if r['retrieval_hit'] else 'FAIL'} | {'EXACT' if r['citation_correct'] else 'MISMATCH'} | {r['latency_ms']} ms |\n")
        f.write("\n### Verifiable Questions, Passages & Grounded Answers\n\n")
        for r in results:
            f.write(f"#### Test {r['test_id']}: {r['question']}\n\n")
            f.write(f"- **Expected Answer:** {r['expected_answer']}\n")
            f.write(f"- **Actual Generated Answer:** {r['actual_answer']}\n")
            f.write(f"- **Top Match Score:** {r['top_similarity']:.4f}\n\n")

    print(f"\n[3/4] Saved evaluation JSON: {json_path}")
    print(f"[4/4] Saved evaluation Markdown: {md_path}\n")

    return summary

if __name__ == "__main__":
    run_evaluation()
