from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
import uuid

T = TypeVar("T")

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Role(str, Enum):
    ROLE_USER = "ROLE_USER"
    ROLE_ADMIN = "ROLE_ADMIN"

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CitationDto(BaseModel):
    documentId: str
    fileName: str
    chunkIndex: int
    pageNumber: int
    snippet: str
    similarityScore: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentMetadataDto(BaseModel):
    id: str
    filename: str
    contentType: str = "application/pdf"
    fileSize: int
    totalPages: int = 1
    totalChunks: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    errorMessage: Optional[str] = None
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class DocumentResponseDto(BaseModel):
    id: str
    fileName: str
    fileSize: int
    status: DocumentStatus
    chunksCreated: int
    message: str
    userId: Optional[int] = 1

class ChatRequestDto(BaseModel):
    question: str
    documentId: Optional[str] = None
    topK: Optional[int] = 5
    minSimilarity: Optional[float] = 0.0
    conversationId: Optional[str] = None

class ChatResponseDto(BaseModel):
    answer: str
    conversationId: str
    citations: List[CitationDto] = Field(default_factory=list)
    responseTimeMs: int

class SearchRequestDto(BaseModel):
    query: str
    documentId: Optional[str] = None
    topK: Optional[int] = 5
    similaritySearch: Optional[float] = 0.0

class SearchResultDto(BaseModel):
    query: str
    totalMatches: int
    matches: List[CitationDto] = Field(default_factory=list)

class ChunkDto(BaseModel):
    documentId: str
    chunkIndex: int
    pageNumber: int
    text: str
    charCount: int
    similarityScore: Optional[float] = None

class UserDto(BaseModel):
    id: int = 1
    username: str = "docmind_user"
    email: str = "user@docmind.ai"
    role: Role = Role.ROLE_USER

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    accessToken: str = "demo-docmind-jwt-token"
    user: UserDto = Field(default_factory=UserDto)

class RegisterUserRequest(BaseModel):
    username: str
    email: str
    password: str
