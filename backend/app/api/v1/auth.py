from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest
from app.services.auth_service import AuthService, get_current_user
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Đăng ký tài khoản người dùng mới."""
    return await AuthService.register(db, data)

@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Đăng nhập bằng username hoặc email và nhận access token + refresh token."""
    return await AuthService.login(db, data)

@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Làm mới Access Token khi token cũ hết hạn."""
    return await AuthService.refresh(db, data.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Lấy thông tin tài khoản đang đăng nhập."""
    return UserResponse.model_validate(current_user)

