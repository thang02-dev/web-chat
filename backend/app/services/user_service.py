from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update, delete, func, case
from fastapi import HTTPException, status
from app.models.models import User, Conversation, ConversationMember, Message

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
    async def get_contacts(db: AsyncSession, current_user_id: str, limit: int = 30) -> List[User]:
        stmt = (
            select(User)
            .where(User.id != current_user_id, User.is_locked == False)
            .order_by(User.is_online.desc(), User.last_seen.desc())
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
        limit: int = 1000,
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

        # Ưu tiên hiển thị Quản lý (ADMIN) lên đầu rồi tới Người dùng (USER) theo thời gian tạo mới nhất
        role_priority = case((User.role == "ADMIN", 0), else_=1)
        stmt = stmt.order_by(role_priority, User.created_at.desc()).offset(offset).limit(limit)
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
    async def toggle_user_lock(
        db: AsyncSession,
        target_user_id: str,
        is_locked: bool,
        current_admin_id: str
    ) -> User:
        if target_user_id == current_admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn không thể tự khóa tài khoản của chính mình."
            )

        target_user = await UserService.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng cần khóa/mở khóa không tồn tại."
            )

        target_user.is_locked = is_locked
        if is_locked:
            target_user.is_online = False

        await db.commit()
        await db.refresh(target_user)
        return target_user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        target_user_id: str,
        current_admin_id: str
    ) -> Dict[str, Any]:
        if target_user_id == current_admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn không thể tự xóa tài khoản của chính mình."
            )

        target_user = await UserService.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Người dùng cần xóa không tồn tại."
            )

        if target_user.username.lower() == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa tài khoản Quản trị viên hệ thống (@admin)."
            )

        # Tìm các cuộc hội thoại DIRECT mà user này tham gia để dọn sạch tránh hội thoại mồ côi
        direct_conv_stmt = (
            select(Conversation.id)
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(
                ConversationMember.user_id == target_user_id,
                Conversation.type == "DIRECT"
            )
        )
        direct_conv_res = await db.execute(direct_conv_stmt)
        direct_conv_ids = list(direct_conv_res.scalars().all())

        if direct_conv_ids:
            await db.execute(delete(Message).where(Message.conversation_id.in_(direct_conv_ids)))
            await db.execute(delete(ConversationMember).where(ConversationMember.conversation_id.in_(direct_conv_ids)))
            await db.execute(delete(Conversation).where(Conversation.id.in_(direct_conv_ids)))

        # Xóa tin nhắn và tư cách thành viên còn lại (nếu có trong GROUP chat)
        await db.execute(delete(Message).where(Message.sender_id == target_user_id))
        await db.execute(delete(ConversationMember).where(ConversationMember.user_id == target_user_id))

        deleted_info = {
            "id": target_user.id,
            "username": target_user.username,
            "full_name": target_user.full_name,
            "email": target_user.email,
            "role": target_user.role
        }

        await db.delete(target_user)
        await db.commit()
        return deleted_info

    @staticmethod
    async def get_user_stats(db: AsyncSession) -> Dict[str, int]:
        total_res = await db.execute(select(func.count(User.id)))
        total_users = total_res.scalar_one_or_none() or 0

        admin_res = await db.execute(select(func.count(User.id)).where(User.role == "ADMIN"))
        admin_count = admin_res.scalar_one_or_none() or 0

        user_count = max(0, total_users - admin_count)

        online_res = await db.execute(select(func.count(User.id)).where(User.is_online == True))
        online_users = online_res.scalar_one_or_none() or 0

        locked_res = await db.execute(select(func.count(User.id)).where(User.is_locked == True))
        locked_count = locked_res.scalar_one_or_none() or 0

        return {
            "total_users": total_users,
            "online_users": online_users,
            "admin_count": admin_count,
            "user_count": user_count,
            "locked_count": locked_count
        }

