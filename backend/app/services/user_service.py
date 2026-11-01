from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
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

