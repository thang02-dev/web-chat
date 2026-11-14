import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.database import get_db
from app.main import app

test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_test_db():
    from sqlalchemy import text
    async with test_engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'USER' NOT NULL;"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key VARCHAR(50) PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            );
        """))
    yield
    # Dọn dẹp toàn bộ dữ liệu tạm sinh ra trong quá trình chạy pytest để không làm rác DB thực tế
    async with test_engine.begin() as conn:
        await conn.execute(text("""
            DELETE FROM users
            WHERE username LIKE 'user_%'
               OR username LIKE 'chat_a_%'
               OR username LIKE 'chat_b_%'
               OR username LIKE 'ws_user_%'
               OR username LIKE 'bot_recv_%'
               OR username LIKE 'admin_%';
        """))
        await conn.execute(text("""
            DELETE FROM conversations
            WHERE id NOT IN (SELECT DISTINCT conversation_id FROM conversation_members);
        """))
        await conn.execute(text("""
            DELETE FROM gold_price_history
            WHERE gold_type LIKE 'Vàng Test %'
               OR gold_type LIKE 'Vàng Xóa %'
               OR gold_type LIKE 'Vàng Bot Test %'
               OR gold_type LIKE 'Vàng 9999 %';
        """))

@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
