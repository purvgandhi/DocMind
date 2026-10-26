from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from app.config import settings

from app.models.schemas import ApiResponse, ChunkDto, DocumentMetadataDto, DocumentResponseDto
from app.services.document_metadata_service import DocumentMetadataService

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management"])

# Dependency placeholder will be set in main.py
def get_doc_service() -> DocumentMetadataService:
    from app.main import doc_service_instance
    return doc_service_instance

@router.post("/upload", response_model=ApiResponse[DocumentResponseDto])
async def upload_document(
    file: UploadFile = File(...),
    doc_service: DocumentMetadataService = Depends(get_doc_service)
):
    """Uploads, parses, chunks, and indexes a single document (PDF, TXT, MD)."""
    try:
        res = await doc_service.ingest_document(file)
        return ApiResponse[DocumentResponseDto](
            success=True,
            message=res.message,
            data=res
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal indexing error: {str(e)}")

@router.post("/upload-multiple", response_model=ApiResponse[List[DocumentResponseDto]])
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    doc_service: DocumentMetadataService = Depends(get_doc_service)
):
    """Uploads and indexes multiple documents."""
    results = []
    errors = []
    for file in files:
        try:
            res = await doc_service.ingest_document(file)
            results.append(res)
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    if not results and errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors))

    msg = f"Processed {len(results)} of {len(files)} files successfully."
    if errors:
        msg += f" Failures: {'; '.join(errors)}"

    return ApiResponse[List[DocumentResponseDto]](
        success=True,
        message=msg,
        data=results
    )

@router.get("", response_model=ApiResponse[List[DocumentMetadataDto]])
async def list_documents(doc_service: DocumentMetadataService = Depends(get_doc_service)):
    """Retrieves all indexed documents."""
    docs = doc_service.list_documents()
    return ApiResponse[List[DocumentMetadataDto]](
        success=True,
        message="Fetched documents successfully.",
        data=docs
    )

@router.get("/{doc_id}", response_model=ApiResponse[DocumentMetadataDto])
async def get_document(doc_id: str, doc_service: DocumentMetadataService = Depends(get_doc_service)):
    """Retrieves metadata for a specific document."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {doc_id} not found.")
    return ApiResponse[DocumentMetadataDto](
        success=True,
        message="Document found.",
        data=doc
    )

@router.delete("/{doc_id}", response_model=ApiResponse[dict])
async def delete_document(doc_id: str, doc_service: DocumentMetadataService = Depends(get_doc_service)):
    """Deletes a document and all of its associated vector embeddings."""
    success = doc_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {doc_id} not found.")
    return ApiResponse[dict](
        success=True,
        message=f"Document {doc_id} deleted successfully.",
        data={"deleted": True, "id": doc_id}
    )

@router.get("/{doc_id}/chunks", response_model=ApiResponse[List[ChunkDto]])
async def get_document_chunks(doc_id: str, doc_service: DocumentMetadataService = Depends(get_doc_service)):
    """Returns all text chunks generated for a specific document."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID {doc_id} not found.")

    raw_chunks = doc_service.vector_store.get_document_chunks(doc_id)
    chunk_dtos = [
        ChunkDto(
            documentId=c.get("documentId", doc_id),
            chunkIndex=c.get("chunkIndex", 0),
            pageNumber=c.get("pageNumber", 1),
            text=c.get("text", ""),
            charCount=c.get("charCount", len(c.get("text", ""))),
            similarityScore=c.get("similarityScore")
        )
        for c in raw_chunks
    ]
    return ApiResponse[List[ChunkDto]](
        success=True,
        message=f"Fetched {len(chunk_dtos)} chunks for document.",
        data=chunk_dtos
    )

@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str, doc_service: DocumentMetadataService = Depends(get_doc_service)):
    """Serves the actual binary document file for browser inline reading or download."""
    doc = doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {doc_id} not found.")
    
    matches = list(settings.upload_dir.glob(f"{doc_id}_*"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document binary file not found on disk.")
    
    file_path = matches[0]
    return FileResponse(
        path=str(file_path),
        filename=doc.filename,
        media_type=doc.contentType or "application/pdf"
    )
