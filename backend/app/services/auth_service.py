from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.database import get_db
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: UserCreate) -> UserResponse:
        # Check existing username
        existing_username = await UserService.get_by_username(db, data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên người dùng (username) này đã tồn tại trong hệ thống."
            )
        
        # Check existing email
        existing_email = await UserService.get_by_email(db, data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Địa chỉ email này đã được sử dụng."
            )

        clean_user = data.username.lower().strip()

        # Mọi tài khoản đăng ký mới qua form mặc định luôn là USER (Người dùng thường)
        new_user = User(
            username=clean_user,
            email=data.email.lower().strip(),
            full_name=data.full_name.strip(),
            avatar_url=data.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={data.username}",
            password_hash=hash_password(data.password),
            role="USER",
            is_online=False
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return UserResponse.model_validate(new_user)

    @staticmethod
    async def login(db: AsyncSession, data: UserLogin) -> Token:
        ident = data.username_or_email.strip().lower()
        if "@" in ident:
            user = await UserService.get_by_email(db, ident)
        else:
            user = await UserService.get_by_username(db, ident)

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Thông tin đăng nhập không chính xác (sai username/email hoặc mật khẩu)."
            )

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token không hợp lệ hoặc đã hết hạn."
            )
        user_id = payload.get("sub")
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)

        return Token(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu xác thực (thiếu Bearer token)."
        )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn."
        )
    user_id = payload.get("sub")
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản người dùng không tồn tại."
        )
    return user

