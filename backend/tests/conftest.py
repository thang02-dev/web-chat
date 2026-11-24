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
        await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);"))
        await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS theme VARCHAR(30) DEFAULT 'ocean' NOT NULL;"))
        await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS quick_emoji VARCHAR(16) DEFAULT '👍' NOT NULL;"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(20) DEFAULT 'TEXT' NOT NULL;"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_url TEXT;"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS reply_to_id VARCHAR(36);"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS reactions TEXT DEFAULT '{}' NOT NULL;"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_recalled BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key VARCHAR(50) PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_sources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                url TEXT NOT NULL,
                interval_minutes INTEGER NOT NULL DEFAULT 10,
                is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                extract_rules TEXT,
                last_scan_at TIMESTAMPTZ,
                last_status VARCHAR(20) NOT NULL DEFAULT 'NEVER',
                last_message TEXT,
                last_row_count INTEGER NOT NULL DEFAULT 0,
                last_duration_ms INTEGER,
                last_strategy VARCHAR(30),
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
            );
        """))
        await conn.execute(text("""
            ALTER TABLE gold_price_history
            ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES gold_sources(id) ON DELETE CASCADE;
        """))
        await conn.execute(text("""
            INSERT INTO gold_sources (name, url, interval_minutes, is_enabled, sort_order)
            SELECT 'Hiệu Vàng Trữ', 'https://hieuvangtru.vn', 10, TRUE, 0
            WHERE NOT EXISTS (SELECT 1 FROM gold_sources);
        """))
        await conn.execute(text("""
            INSERT INTO gold_sources (name, url, interval_minutes, is_enabled, sort_order)
            SELECT 'Ngọc Thịnh Jewelry', 'https://ngocthinh-jewelry.vn', 10, TRUE, 1
            WHERE (SELECT COUNT(*) FROM gold_sources) = 1
              AND NOT EXISTS (SELECT 1 FROM gold_sources WHERE url LIKE '%ngocthinh%');
        """))
        await conn.execute(text("""
            UPDATE gold_price_history
            SET source_id = (SELECT id FROM gold_sources ORDER BY sort_order ASC, id ASC LIMIT 1)
            WHERE source_id IS NULL
              AND EXISTS (SELECT 1 FROM gold_sources);
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
