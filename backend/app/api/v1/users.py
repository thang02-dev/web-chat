from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import UserResponse
from app.services.auth_service import get_current_user
from app.services.user_service import UserService
from app.models.models import User
from app.websocket.manager import manager

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm username hoặc tên đầy đủ"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tìm kiếm người dùng trong hệ thống theo username hoặc tên."""
    users = await UserService.search_users(db, query=q, current_user_id=current_user.id)
    resp = []
    for u in users:
        u_resp = UserResponse.model_validate(u)
        u_resp.is_online = manager.is_user_online(u.id)
        resp.append(u_resp)
    return resp

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy thông tin chi tiết của một người dùng."""
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại.")
    u_resp = UserResponse.model_validate(user)
    u_resp.is_online = manager.is_user_online(user.id)
    return u_resp

