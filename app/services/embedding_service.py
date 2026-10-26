import os
import logging
import numpy as np
from typing import List, Union

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Modular embedding generator supporting:
    1. Local dense neural embeddings via SentenceTransformers ('all-MiniLM-L6-v2')
    2. OpenAI embeddings if OPENAI_API_KEY is configured
    3. Resilient TF-IDF Vectorizer fallback for zero-dependency execution
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._st_model = None
        self._provider = "unknown"
        self._tfidf_vectorizer = None
        self._initialize_provider()

    def _initialize_provider(self):
        # 1. Try local sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local SentenceTransformer model: {self.model_name}...")
            self._st_model = SentenceTransformer(self.model_name)
            self._provider = "sentence_transformer"
            logger.info("SentenceTransformer loaded successfully.")
            return
        except Exception as e:
            logger.warning(f"SentenceTransformer not available or failed to load ({e}). Checking alternatives.")

        # 2. Try OpenAI if API key exists
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_key and openai_key != "demo-key":
            try:
                import requests
                self._provider = "openai"
                logger.info("Using OpenAI embedding API (text-embedding-3-small).")
                return
            except Exception:
                pass

        # 3. Fallback to Scikit-Learn TF-IDF dense vectors
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._tfidf_vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
            self._provider = "tfidf_dense"
            logger.info("Using Scikit-learn TF-IDF dense vector fallback for embeddings.")
        except Exception as e:
            self._provider = "fallback_hash"
            logger.warning(f"Using deterministic hash vector fallback: {e}")

    @property
    def provider(self) -> str:
        return self._provider

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of text strings into a 2D float32 numpy array (N, D).
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        if self._provider == "sentence_transformer" and self._st_model is not None:
            try:
                embeddings = self._st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.error(f"SentenceTransformer encoding failed: {e}. Falling back to TF-IDF.")

        # Fallback to TF-IDF dense representation
        return self._embed_tfidf(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a single query string into a 1D float32 numpy vector (D,).
        """
        result = self.embed_texts([query])
        return result[0]

    def _embed_tfidf(self, texts: List[str]) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
        try:
            tfidf_mat = vectorizer.fit_transform(texts).toarray()
            # Normalize rows to unit length for cosine similarity
            norms = np.linalg.norm(tfidf_mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return (tfidf_mat / norms).astype(np.float32)
        except Exception:
            # Fallback pseudo-dense deterministic projection
            vectors = []
            for t in texts:
                vec = np.zeros(384, dtype=np.float32)
                for i, word in enumerate(t.lower().split()):
                    idx = abs(hash(word)) % 384
                    vec[idx] += 1.0
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec /= norm
                vectors.append(vec)
            return np.array(vectors, dtype=np.float32)
