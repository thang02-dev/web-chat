from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import UserResponse, UserRoleUpdate, UserLockUpdate, UserStatsResponse
from app.schemas.gold import CrawlerConfigUpdate, CrawlerConfigResponse, CrawlerCleanupRequest
from app.services.auth_service import get_current_user
from app.services.user_service import UserService
from app.services.gold_crawler_manager import crawler_manager
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
    limit: int = Query(1000, ge=1, le=5000),
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

@router.patch("/{user_id}/lock", response_model=UserResponse)
async def toggle_user_lock(
    user_id: str,
    payload: UserLockUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Khóa hoặc mở khóa tài khoản người dùng."""
    updated_user = await UserService.toggle_user_lock(
        db,
        target_user_id=user_id,
        is_locked=payload.is_locked,
        current_admin_id=current_admin.id
    )
    if payload.is_locked:
        await manager.disconnect_user(user_id)
        await manager.broadcast_all({
            "type": "USER_STATUS",
            "payload": {"user_id": user_id, "is_online": False, "is_locked": True}
        })
    else:
        await manager.broadcast_all({
            "type": "USER_STATUS",
            "payload": {"user_id": user_id, "is_locked": False}
        })
    u_resp = UserResponse.model_validate(updated_user)
    u_resp.is_online = manager.is_user_online(updated_user.id)
    return u_resp

@router.delete("/{user_id}")
async def delete_user_account(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Xóa vĩnh viễn tài khoản người dùng và dữ liệu hội thoại liên quan."""
    deleted_info = await UserService.delete_user(
        db,
        target_user_id=user_id,
        current_admin_id=current_admin.id
    )
    await manager.disconnect_user(user_id)
    if user_id in crawler_manager.notify_user_ids or crawler_manager.notify_user_id == user_id:
        remaining_ids = [uid for uid in crawler_manager.notify_user_ids if uid != user_id]
        await crawler_manager.save_settings(
            db,
            interval_minutes=crawler_manager.interval_minutes,
            is_enabled=crawler_manager.is_enabled,
            notify_user_id=remaining_ids[0] if remaining_ids else None,
            notify_mode=crawler_manager.notify_mode,
            delete_changed_messages=crawler_manager.delete_changed_messages,
            notify_user_ids=remaining_ids
        )
    return {
        "success": True,
        "deleted_user": deleted_info,
        "message": f"Đã xóa tài khoản {deleted_info['full_name']} (@{deleted_info['username']})."
    }

@router.get("/contacts", response_model=List[UserResponse])
async def get_contacts_list(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách người dùng gợi ý / đang hoạt động cho thanh Active Now và tạo nhóm."""
    users = await UserService.get_contacts(db, current_user_id=current_user.id, limit=limit)
    resp = []
    for u in users:
        u_resp = UserResponse.model_validate(u)
        u_resp.is_online = manager.is_user_online(u.id) or bool(u.is_online)
        resp.append(u_resp)
    resp.sort(key=lambda x: (not x.is_online, x.full_name.lower()))
    return resp

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


# ==================== Crawler & System Settings (Admin) ====================

@router.get("/admin/crawler-config", response_model=CrawlerConfigResponse)
async def get_crawler_config(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Lấy trạng thái, chu kỳ, cấu hình nhận tin và lịch sử quét giá vàng của crawler."""
    await crawler_manager._refresh_bot_message_count(db)
    return CrawlerConfigResponse(**crawler_manager.get_status())


@router.post("/admin/crawler-config", response_model=CrawlerConfigResponse)
async def update_crawler_config(
    payload: CrawlerConfigUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Cập nhật chu kỳ quét, trạng thái bật/tắt và cấu hình gửi tin nhắn lịch sử call."""
    if payload.notify_user_ids is not None:
        candidate_ids = [str(uid).strip() for uid in payload.notify_user_ids if uid and str(uid).strip()]
    elif payload.notify_user_id and payload.notify_user_id.strip():
        candidate_ids = [payload.notify_user_id.strip()]
    else:
        candidate_ids = []

    validated_ids = list(dict.fromkeys(candidate_ids))
    for uid in validated_ids:
        target_user = await UserService.get_by_id(db, uid)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tài khoản nhận thông báo ({uid}) không tồn tại."
            )
        if target_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chỉ được chọn tài khoản Quản lý (ADMIN) để nhận tin lịch sử call."
            )

    await crawler_manager.save_settings(
        db,
        interval_minutes=payload.interval_minutes,
        is_enabled=payload.is_enabled,
        notify_user_id=validated_ids[0] if validated_ids else None,
        notify_mode=payload.notify_mode,
        delete_changed_messages=payload.delete_changed_messages,
        notify_user_ids=validated_ids
    )
    return CrawlerConfigResponse(**crawler_manager.get_status())


@router.post("/admin/crawler-trigger")
async def trigger_crawler_now(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Kích hoạt quét giá vàng ngay lập tức và trả về kết quả."""
    result = await crawler_manager.trigger_crawl(source="MANUAL", db=db)
    return result


@router.post("/admin/crawler-cleanup")
async def cleanup_crawler_bot_messages(
    payload: Optional[CrawlerCleanupRequest] = Body(default=None),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """(Admin) Xóa tin nhắn thông báo lịch sử call của bot giá vàng theo chế độ đã chọn."""
    delete_changed = payload.delete_changed_messages if payload is not None else None
    deleted = await crawler_manager.cleanup_bot_messages(db=db, delete_changed=delete_changed)
    used_mode = crawler_manager.delete_changed_messages if delete_changed is None else bool(delete_changed)
    if used_mode:
        msg = f"Đã xóa {deleted} tin nhắn bot (bao gồm cả tin giá vàng có thay đổi)."
    else:
        msg = f"Đã xóa {deleted} tin nhắn giá vàng không thay đổi (giữ lại các tin giá có thay đổi)."
    return {
        "success": True,
        "deleted": deleted,
        "delete_changed_messages": used_mode,
        "message": msg
    }



