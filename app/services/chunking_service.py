import re
from typing import Any, Dict, List

class ChunkingService:
    """
    Splits extracted document page texts into overlapping chunks
    while preserving page numbers and semantic paragraph boundaries.
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document_id: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunks page text while retaining page numbers.
        Returns list of chunks with metadata.
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_index = 0

        for page in pages_data:
            page_number = page["pageNumber"]
            page_text = page["text"].strip()
            if not page_text:
                continue

            # Split by double newline (paragraphs) or sentences if text is long
            page_chunks = self._split_text_with_overlap(page_text)

            for chunk_text in page_chunks:
                chunk_text_clean = chunk_text.strip()
                if len(chunk_text_clean) < 20:  # Skip tiny fragments
                    continue

                chunks.append({
                    "documentId": document_id,
                    "chunkIndex": global_chunk_index,
                    "pageNumber": page_number,
                    "text": chunk_text_clean,
                    "charCount": len(chunk_text_clean)
                })
                global_chunk_index += 1

        return chunks

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """
        Recursive character splitting with overlap.
        """
        if len(text) <= self.chunk_size:
            return [text]

        # Break text into paragraphs or sentences
        paragraphs = re.split(r'\n{2,}|\r\n{2,}', text)
        result: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph itself is larger than chunk size, split by sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current_chunk) + len(sent) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {sent}".strip()
                    else:
                        if current_chunk:
                            result.append(current_chunk)
                            # Apply overlap from end of current_chunk
                            overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                            overlap_text = current_chunk[overlap_start:].strip()
                            current_chunk = f"{overlap_text} {sent}".strip()
                        else:
                            # Sentence itself exceeds chunk size, hard slice
                            for i in range(0, len(sent), self.chunk_size - self.chunk_overlap):
                                result.append(sent[i:i + self.chunk_size])
                            current_chunk = ""
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = f"{current_chunk}\n\n{para}".strip()
                else:
                    if current_chunk:
                        result.append(current_chunk)
                        overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                        overlap_text = current_chunk[overlap_start:].strip()
                        current_chunk = f"{overlap_text}\n\n{para}".strip()
                    else:
                        current_chunk = para

        if current_chunk:
            result.append(current_chunk)

        return result
