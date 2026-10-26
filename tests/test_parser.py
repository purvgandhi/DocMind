import pytest
from pathlib import Path
from app.services.parser_service import DocumentParserService

def test_parse_sample_pdf():
    pdf_path = Path(__file__).resolve().parent.parent / "sample_documents" / "sample_ai_research.pdf"
    assert pdf_path.exists(), f"Sample PDF missing at {pdf_path}"

    pages = DocumentParserService.parse_pdf(pdf_path)
    assert len(pages) == 2, f"Expected 2 pages, found {len(pages)}"
    assert pages[0]["pageNumber"] == 1
    assert "Retrieval-Augmented Generation" in pages[0]["text"]
    assert pages[1]["pageNumber"] == 2
    assert "Natural Questions" in pages[1]["text"]
    assert pages[0]["charCount"] > 200

def test_parse_empty_file(tmp_path):
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        DocumentParserService.parse_pdf(empty_file)

def test_parse_corrupt_file(tmp_path):
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_text("Not a real PDF file contents")
    with pytest.raises(ValueError, match="Failed to open document"):
        DocumentParserService.parse_pdf(corrupt_file)
