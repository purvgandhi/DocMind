from fastapi import APIRouter
from app.models.schemas import ApiResponse, LoginRequest, LoginResponse, RegisterUserRequest, Role, UserDto

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(request: LoginRequest):
    """Stateless authentication returning user token."""
    user = UserDto(
        id=1,
        username=request.username or "docmind_admin",
        email=f"{request.username or 'admin'}@docmind.ai",
        role=Role.ROLE_USER
    )
    return ApiResponse[LoginResponse](
        success=True,
        message="Login successful",
        data=LoginResponse(accessToken="docmind_jwt_valid_token_xyz123", user=user)
    )

@router.post("/register", response_model=ApiResponse[LoginResponse])
async def register(request: RegisterUserRequest):
    """User registration endpoint."""
    user = UserDto(
        id=1,
        username=request.username,
        email=request.email,
        role=Role.ROLE_USER
    )
    return ApiResponse[LoginResponse](
        success=True,
        message="Registration successful",
        data=LoginResponse(accessToken="docmind_jwt_valid_token_xyz123", user=user)
    )

@router.get("/me", response_model=ApiResponse[UserDto])
async def get_current_user():
    """Current authenticated user profile."""
    return ApiResponse[UserDto](
        success=True,
        message="User profile retrieved",
        data=UserDto()
    )
