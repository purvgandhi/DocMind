import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import UploadFile

from app.config import settings
from app.models.schemas import DocumentMetadataDto, DocumentResponseDto, DocumentStatus
from app.services.chunking_service import ChunkingService
from app.services.document_parser_service import DocumentParserService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class DocumentMetadataService:
    """
    Manages document lifecycle, ingestion, metadata persistence,
    chunking, and embedding orchestration.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.chunking_service = chunking_service

        self.storage_file = settings.data_dir / "documents_metadata.json"
        self.documents: Dict[str, DocumentMetadataDto] = {}
        self._load()

    def list_documents(self) -> List[DocumentMetadataDto]:
        """Returns all documents sorted by creation date descending."""
        docs = list(self.documents.values())
        docs.sort(key=lambda x: x.createdAt, reverse=True)
        return docs

    def get_document(self, doc_id: str) -> Optional[DocumentMetadataDto]:
        return self.documents.get(doc_id)

    async def ingest_document(self, file: UploadFile) -> DocumentResponseDto:
        """
        Receives an uploaded file, extracts text, chunks, embeds, and saves metadata.
        Prevents duplicate entries by replacing prior versions of the same filename.
        """
        filename = file.filename or "uploaded_document.pdf"
        
        # Deduplication check: remove prior version of the document with matching filename
        for old_id, old_meta in list(self.documents.items()):
            if old_meta.filename.strip().lower() == filename.strip().lower():
                logger.info(f"Replacing duplicate document '{filename}' (ID: {old_id}) with new upload.")
                self.delete_document(old_id)

        doc_id = str(uuid.uuid4())
        file_path = settings.upload_dir / f"{doc_id}_{filename}"

        # Read file contents
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise ValueError(f"Uploaded file '{filename}' is empty (0 bytes).")

        # Save to disk
        with open(file_path, "wb") as f:
            f.write(content)

        # Register initial metadata
        now_str = datetime.utcnow().isoformat()
        metadata = DocumentMetadataDto(
            id=doc_id,
            filename=filename,
            contentType=file.content_type or "application/pdf",
            fileSize=file_size,
            totalPages=1,
            totalChunks=0,
            status=DocumentStatus.PROCESSING,
            createdAt=now_str,
            updatedAt=now_str
        )
        self.documents[doc_id] = metadata
        self._save()

        try:
            # 1. Parse document into pages
            pages_data = DocumentParserService.parse_document(file_path, filename)
            metadata.totalPages = len(pages_data)

            # 2. Chunk document text
            chunks = self.chunking_service.chunk_document(doc_id, pages_data)
            for c in chunks:
                c["fileName"] = filename

            metadata.totalChunks = len(chunks)

            # 3. Generate embeddings
            texts = [c["text"] for c in chunks]
            vectors = self.embedding_service.embed_texts(texts)

            # 4. Store in vector store
            self.vector_store.add_chunks(chunks, vectors)

            # 5. Mark completed
            metadata.status = DocumentStatus.COMPLETED
            metadata.updatedAt = datetime.utcnow().isoformat()
            self._save()

            return DocumentResponseDto(
                id=doc_id,
                fileName=filename,
                fileSize=file_size,
                status=DocumentStatus.COMPLETED,
                chunksCreated=len(chunks),
                message=f"Successfully indexed '{filename}' with {len(chunks)} chunks across {metadata.totalPages} pages."
            )

        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}", exc_info=True)
            metadata.status = DocumentStatus.FAILED
            metadata.errorMessage = str(e)
            metadata.updatedAt = datetime.utcnow().isoformat()
            self._save()
            raise ValueError(f"Document processing failed: {str(e)}")

    def ingest_local_file(self, source_path: Path, filename: Optional[str] = None) -> DocumentResponseDto:
        """Synchronously ingests a local file on disk without requiring HTTP UploadFile."""
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
        
        target_name = filename or source_path.name
        
        # Deduplication check
        for old_id, old_meta in list(self.documents.items()):
            if old_meta.filename.strip().lower() == target_name.strip().lower():
                self.delete_document(old_id)

        doc_id = str(uuid.uuid4())
        dest_path = settings.upload_dir / f"{doc_id}_{target_name}"
        
        with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
            dst.write(src.read())
            
        file_size = dest_path.stat().st_size
        now_str = datetime.utcnow().isoformat()
        metadata = DocumentMetadataDto(
            id=doc_id,
            filename=target_name,
            contentType="application/pdf" if target_name.endswith(".pdf") else "text/plain",
            fileSize=file_size,
            totalPages=1,
            totalChunks=0,
            status=DocumentStatus.PROCESSING,
            createdAt=now_str,
            updatedAt=now_str
        )
        self.documents[doc_id] = metadata
        self._save()
        
        try:
            pages_data = DocumentParserService.parse_document(dest_path, target_name)
            metadata.totalPages = len(pages_data)
            chunks = self.chunking_service.chunk_document(doc_id, pages_data)
            for c in chunks:
                c["fileName"] = target_name
            metadata.totalChunks = len(chunks)
            texts = [c["text"] for c in chunks]
            vectors = self.embedding_service.embed_texts(texts)
            self.vector_store.add_chunks(chunks, vectors)
            metadata.status = DocumentStatus.COMPLETED
            metadata.updatedAt = datetime.utcnow().isoformat()
            self._save()
            return DocumentResponseDto(
                id=doc_id,
                fileName=target_name,
                fileSize=file_size,
                status=DocumentStatus.COMPLETED,
                chunksCreated=len(chunks),
                message=f"Indexed {target_name}"
            )
        except Exception as e:
            metadata.status = DocumentStatus.FAILED
            metadata.errorMessage = str(e)
            self._save()
            raise e

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and its indexed vectors."""
        if doc_id in self.documents:
            # Delete vectors
            self.vector_store.delete_document_chunks(doc_id)
            # Remove metadata
            doc = self.documents.pop(doc_id)
            self._save()
            # Remove file from disk
            for f in settings.upload_dir.glob(f"{doc_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            return True
        return False

    def _save(self):
        try:
            data = {k: v.model_dump() for k, v in self.documents.items()}
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist document metadata: {e}")

    def _load(self):
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for k, v in raw.items():
                        self.documents[k] = DocumentMetadataDto(**v)
                logger.info(f"Loaded {len(self.documents)} document records.")
        except Exception as e:
            logger.warning(f"Failed to load document metadata: {e}")
