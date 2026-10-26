import os
from pathlib import Path
from typing import Dict, List, Any
import pymupdf  # PyMuPDF

class DocumentParserService:
    """
    Parses documents (PDF, TXT, MD, DOCX) and extracts text per page with metadata.
    Handles invalid, empty, or corrupted files gracefully.
    """

    @staticmethod
    def parse_pdf(file_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts text from each page of a PDF document using PyMuPDF.
        Returns a list of dicts: [{'pageNumber': int, 'text': str, 'charCount': int}]
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found at {file_path}")

        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValueError("The uploaded document is completely empty (0 bytes).")

        pages_data = []
        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            raise ValueError(f"Failed to open document as PDF. Corrupted or invalid format: {str(e)}")

        try:
            if len(doc) == 0:
                raise ValueError("PDF document contains 0 pages.")

            total_extracted_chars = 0
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text").strip()
                char_count = len(text)
                total_extracted_chars += char_count

                pages_data.append({
                    "pageNumber": page_index + 1,
                    "text": text,
                    "charCount": char_count
                })

            if total_extracted_chars == 0:
                raise ValueError("PDF document contains no extractable text (it may be a scanned image-only PDF without OCR).")

        finally:
            doc.close()

        return pages_data

    @staticmethod
    def parse_text(file_path: Path) -> List[Dict[str, Any]]:
        """Parses plain text / markdown files."""
        text = file_path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            raise ValueError("Document file is empty.")
        return [{
            "pageNumber": 1,
            "text": text,
            "charCount": len(text)
        }]

    @classmethod
    def parse_document(cls, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path)
        elif ext in [".txt", ".md", ".csv", ".json"]:
            return cls.parse_text(file_path)
        else:
            # Attempt PDF first, then fallback to text
            try:
                return cls.parse_pdf(file_path)
            except Exception:
                return cls.parse_text(file_path)
