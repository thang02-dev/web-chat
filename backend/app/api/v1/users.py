from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import UserResponse, UserRoleUpdate, UserStatsResponse
from app.services.auth_service import get_current_user
from app.services.user_service import UserService
from app.models.models import User
from app.websocket.manager import manager

router = APIRouter(prefix="/users", tags=["Users"])

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: Yêu cầu quyền Quản trị viên (ADMIN)."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập tính năng Quản lý."
        )
    return current_user

@router.get("/admin/list", response_model=List[UserResponse])
async def list_users_for_admin(
    q: Optional[str] = Query(None, max_length=100, description="Tìm theo tên, username hoặc email"),
    role: Optional[str] = Query(None, pattern=r"^(ADMIN|USER)$", description="Lọc theo ADMIN hoặc USER"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Lấy toàn bộ danh sách người dùng kèm phân quyền và trạng thái online."""
    users = await UserService.get_admin_user_list(
        db, query=q, role=role, limit=limit, offset=offset
    )
    resp = []
    for u in users:
        u_resp = UserResponse.model_validate(u)
        u_resp.is_online = manager.is_user_online(u.id)
        resp.append(u_resp)
    return resp

@router.get("/admin/stats", response_model=UserStatsResponse)
async def get_admin_user_stats(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Lấy các chỉ số thống kê người dùng."""
    stats = await UserService.get_user_stats(db)
    # Lấy số người đang online thực tế từ websocket connection pool nếu có
    active_ws_count = len(manager.active_connections)
    if active_ws_count > stats["online_users"]:
        stats["online_users"] = active_ws_count
    return UserStatsResponse(**stats)

@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Chuyển đổi vai trò người dùng (ADMIN <-> USER)."""
    updated_user = await UserService.update_user_role(
        db,
        target_user_id=user_id,
        new_role=payload.role,
        current_admin_id=current_admin.id
    )
    u_resp = UserResponse.model_validate(updated_user)
    u_resp.is_online = manager.is_user_online(updated_user.id)
    return u_resp

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

