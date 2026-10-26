# DocMind AI System Evaluation — Experiment 10

**Document Evaluated:** `sample_ai_research.pdf`  
**Embedding Model:** `sentence_transformer`  
**Recall@5:** 80.0%  
**Citation Page Accuracy:** 60.0%  
**Average Latency:** 32.2 ms  

### Detailed Test Results

| Test # | Question | Expected Page | Top Page | Recall@5 | Citation | Latency |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | What is the core problem statement addressed by Retrieval-Augmented Generation? | Page 1 | Page 1 | PASS | EXACT | 9 ms |
| 2 | What neural architectures form the retriever and the generator in RAG? | Page 1 | Page 1 | PASS | EXACT | 127 ms |
| 3 | What empirical Exact Match score did RAG attain on the Natural Questions benchmark? | Page 2 | Page 2 | PASS | EXACT | 8 ms |
| 4 | How do RAG-Sequence and RAG-Token formulations differ in generating tokens? | Page 2 | Page 1 | PASS | MISMATCH | 7 ms |
| 5 | What practical deployment challenges and limitations are highlighted for RAG? | Page 2 | Page 1 | FAIL | MISMATCH | 10 ms |

### Verifiable Questions, Passages & Grounded Answers

#### Test 1: What is the core problem statement addressed by Retrieval-Augmented Generation?

- **Expected Answer:** Large parametric language models suffer from hallucinations, inability to dynamically update knowledge without retraining, and lack of verifiable provenance/citations.
- **Actual Generated Answer:** Based on Page 1, Page 2 of the document:

Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin
Facebook AI Research (FAIR), University College London, New York University
ABSTRACT
Large pre-trained language models store substantial amounts of factual knowledge in their model parameters. INTRODUCTION & PROBLEM STATEMENT
Large language models trained purely on text prediction (parametric models) parameterize world knowledge within millions o
- Inability to dynamically update knowledge without costly end-to-end retraining.

**Source Provenance:** Grounded in 5 retrieved passage(s) (Page 1, Page 2, Top Similarity Score: 0.5913).
- **Top Match Score:** 0.5913

#### Test 2: What neural architectures form the retriever and the generator in RAG?

- **Expected Answer:** Dense Passage Retriever (DPR) bi-encoder for dense passage retrieval and BART-large for sequence-to-sequence parametric generation.
- **Actual Generated Answer:** Based on Page 1, Page 2 of the document:

SYSTEM ARCHITECTURE & MATHEMATICAL FORMULATION
The RAG pipeline operates via two fundamental components:
- Dense Passage Retriever (DPR): A bi-encoder architecture mapping query x and document chunk z to dense vector embe
  sim(q, d) = <E_q(x), E_d(z)>
  The probability of selecting document chunk z given query x is:
  p(z|x) = exp(sim(q, d)) / sum_j(exp(sim(q, d_j)))
- Parametric Generator: A sequence-to-sequence BART-large model generating target tokens conditioned on the input quer ts, DocMind implements the RAG framework, establishing a hybrid architecture combining parametric
2. CHALLENGES, LIMITATIONS, AND DISCUSSION
Despite strong empirical gains, practical deployment highlights several remaining challenges:
- Retrieval Latency: High latency from vector index lookup and neural encoding during online user queries. - Contradictory Evidence: When retrieved passages contain conflicting information, generative models may synthesize blend
- Interpretability and Source Grounding: Verifying that each claim in the generated answer strictly originates from the cited c

**Source Provenance:** Grounded in 5 retrieved passage(s) (Page 1, Page 2, Top Similarity Score: 0.5021).
- **Top Match Score:** 0.5021

#### Test 3: What empirical Exact Match score did RAG attain on the Natural Questions benchmark?

- **Expected Answer:** RAG attained 44.5% Exact Match on Natural Questions, outperforming closed-book T5-11B (34.5%) by 10.0 points.
- **Actual Generated Answer:** Based on Page 1, Page 2 of the document:

EMPIRICAL RESULTS & METRICS
Evaluation was conducted using Exact Match (EM) accuracy and Token F1-score:
- Natural Questions: RAG achieved 44.5% Exact Match, outperforming closed-book T5-11B (34.5%) by 10.0 points. - WebQuestions: RAG attained 45.2% Exact Match. - TriviaQA: RAG attained 56.8% Exact Match, surpassing REALM (40.4%) and baseline models. EXPERIMENTAL DATASETS & BENCHMARKS
We evaluated the framework on standard knowledge-intensive question answering datasets:
- Natural Questions (NQ): Google search queries with human-annotated answers from Wikipedia.

**Source Provenance:** Grounded in 5 retrieved passage(s) (Page 1, Page 2, Top Similarity Score: 0.5696).
- **Top Match Score:** 0.5696

#### Test 4: How do RAG-Sequence and RAG-Token formulations differ in generating tokens?

- **Expected Answer:** RAG-Sequence conditions the entire generated sequence on a single retrieved passage, whereas RAG-Token marginalizes across different passages at each token step.
- **Actual Generated Answer:** Based on Page 1, Page 2 of the document:

TRAINING, CHUNKING, AND MARGINALIZATION
The document corpus is segmented into non-overlapping or sliding-window overlapping text chunks of 100 to 200 words (ap
Two formulation variants are supported:
- RAG-Sequence: The model selects a single retrieved document chunk to condition the entire generated sequence y:
  p_RAG-Seq(y|x) = sum_{z in Top-k} p(z|x) * prod_{t} p(y_t | x, z, y_{1:t-1})
- RAG-Token: The model marginalizes across different retrieved chunks at each individual token step, allowing multi-docum
4. SYSTEM ARCHITECTURE & MATHEMATICAL FORMULATION
The RAG pipeline operates via two fundamental components:
- Dense Passage Retriever (DPR): A bi-encoder architecture mapping query x and document chunk z to dense vector embe
  sim(q, d) = <E_q(x), E_d(z)>
  The probability of selecting document chunk z given query x is:
  p(z|x) = exp(sim(q, d)) / sum_j(exp(sim(q, d_j)))
- Parametric Generator: A sequence-to-sequence BART-large model generating target tokens conditioned on the input quer

**Source Provenance:** Grounded in 5 retrieved passage(s) (Page 1, Page 2, Top Similarity Score: 0.4706).
- **Top Match Score:** 0.4706

#### Test 5: What practical deployment challenges and limitations are highlighted for RAG?

- **Expected Answer:** Retrieval latency, chunk boundary alignment, handling contradictory evidence, and verifying source grounding/interpretability.
- **Actual Generated Answer:** Based on Page 1, Page 2 of the document:

ts, DocMind implements the RAG framework, establishing a hybrid architecture combining parametric
2. SYSTEM ARCHITECTURE & MATHEMATICAL FORMULATION
The RAG pipeline operates via two fundamental components:
- Dense Passage Retriever (DPR): A bi-encoder architecture mapping query x and document chunk z to dense vector embe
  sim(q, d) = <E_q(x), E_d(z)>
  The probability of selecting document chunk z given query x is:
  p(z|x) = exp(sim(q, d)) / sum_j(exp(sim(q, d_j)))
- Parametric Generator: A sequence-to-sequence BART-large model generating target tokens conditioned on the input quer EMPIRICAL RESULTS & METRICS
Evaluation was conducted using Exact Match (EM) accuracy and Token F1-score:
- Natural Questions: RAG achieved 44.5% Exact Match, outperforming closed-book T5-11B (34.5%) by 10.0 points. - TriviaQA: RAG attained 56.8% Exact Match, surpassing REALM (40.4%) and baseline models.

**Source Provenance:** Grounded in 5 retrieved passage(s) (Page 1, Page 2, Top Similarity Score: 0.2450).
- **Top Match Score:** 0.2450

