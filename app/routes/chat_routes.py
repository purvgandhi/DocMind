import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.schemas import ApiResponse, ChatRequestDto, ChatResponseDto, SearchRequestDto, SearchResultDto
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat & Q&A Management"])

def get_rag_service() -> RagService:
    from app.main import rag_service_instance
    return rag_service_instance

@router.post("/query", response_model=ApiResponse[ChatResponseDto])
async def ask_question(
    request: ChatRequestDto,
    rag_service: RagService = Depends(get_rag_service)
):
    """
    Asks a question against all documents or a specific document.
    Returns grounded answer with citations and latency.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    try:
        response_dto = rag_service.ask_question(request)
        return ApiResponse[ChatResponseDto](
            success=True,
            message="Question answered successfully.",
            data=response_dto
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )

@router.post("/search", response_model=ApiResponse[SearchResultDto])
async def search_passages(
    request: SearchRequestDto,
    rag_service: RagService = Depends(get_rag_service)
):
    """
    Performs semantic vector search over documents for clauses, concepts, and facts.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    try:
        result = rag_service.search_passages(request)
        return ApiResponse[SearchResultDto](
            success=True,
            message=f"Found {result.totalMatches} matching passages.",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/stream")
async def stream_question(
    request: ChatRequestDto,
    rag_service: RagService = Depends(get_rag_service)
):
    """
    Streams answer tokens via Server-Sent Events (SSE).
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

    async def event_generator():
        try:
            chat_res = rag_service.ask_question(request)
            answer_text = chat_res.answer

            # Stream words with small realistic delay
            words = answer_text.split(" ")
            for i, word in enumerate(words):
                chunk_str = word + (" " if i < len(words) - 1 else "")
                data = json.dumps({"token": chunk_str})
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.02)

            # Send final payload with citations
            final_data = json.dumps({
                "done": True,
                "conversationId": chat_res.conversationId,
                "citations": [c.model_dump() for c in chat_res.citations],
                "responseTimeMs": chat_res.responseTimeMs
            })
            yield f"data: {final_data}\n\n"

        except Exception as e:
            err_data = json.dumps({"error": str(e)})
            yield f"data: {err_data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
