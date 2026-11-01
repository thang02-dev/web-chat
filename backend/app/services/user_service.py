from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update, func
from fastapi import HTTPException, status
from app.models.models import User

class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def search_users(db: AsyncSession, query: str, current_user_id: str, limit: int = 20) -> List[User]:
        clean_q = query.strip().lstrip("@")
        search_filter = or_(
            User.username.ilike(f"%{clean_q}%"),
            User.full_name.ilike(f"%{clean_q}%"),
            User.email.ilike(f"%{clean_q}%")
        )
        stmt = (
            select(User)
            .where(search_filter, User.id != current_user_id)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def set_online_status(db: AsyncSession, user_id: str, is_online: bool) -> Optional[User]:
        now = datetime.now(timezone.utc)
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_online=is_online, last_seen=now)
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalars().first()

    @staticmethod
    async def get_admin_user_list(
        db: AsyncSession,
        query: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        stmt = select(User)
        filters = []

        if query:
            clean_q = query.strip().lstrip("@")
            filters.append(
                or_(
                    User.username.ilike(f"%{clean_q}%"),
                    User.full_name.ilike(f"%{clean_q}%"),
                    User.email.ilike(f"%{clean_q}%")
                )
            )

        if role and role.upper() in ["ADMIN", "USER"]:
            filters.append(User.role == role.upper())

        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_user_role(
        db: AsyncSession,
        target_user_id: str,
        new_role: str,
        current_admin_id: str
    ) -> User:
        clean_role = new_role.upper().strip()
        if clean_role not in ["ADMIN", "USER"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vai trò không hợp lệ. Chỉ chấp nhận 'ADMIN' (Quản lý) hoặc 'USER' (Người dùng)."
            )

        target_user = await UserService.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng cần thay đổi quyền không tồn tại."
            )

        # Safety check: if admin demoting themselves, ensure at least one other admin exists
        if target_user_id == current_admin_id and clean_role != "ADMIN":
            admin_count_res = await db.execute(
                select(func.count(User.id)).where(User.role == "ADMIN", User.id != current_admin_id)
            )
            other_admins = admin_count_res.scalar_one_or_none() or 0
            if other_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bạn là Quản trị viên duy nhất trong hệ thống. Hãy thăng cấp tài khoản khác trước khi từ bỏ quyền Quản lý."
                )

        target_user.role = clean_role
        await db.commit()
        await db.refresh(target_user)
        return target_user

    @staticmethod
    async def get_user_stats(db: AsyncSession) -> Dict[str, int]:
        total_res = await db.execute(select(func.count(User.id)))
        total_users = total_res.scalar_one_or_none() or 0

        admin_res = await db.execute(select(func.count(User.id)).where(User.role == "ADMIN"))
        admin_count = admin_res.scalar_one_or_none() or 0

        user_count = max(0, total_users - admin_count)

        online_res = await db.execute(select(func.count(User.id)).where(User.is_online == True))
        online_users = online_res.scalar_one_or_none() or 0

        return {
            "total_users": total_users,
            "online_users": online_users,
            "admin_count": admin_count,
            "user_count": user_count
        }

