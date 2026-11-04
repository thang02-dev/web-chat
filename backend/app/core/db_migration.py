import logging
import uuid
from typing import Dict, List, Any
from sqlalchemy import text
from app.core.database import engine, Base
from app.core.security import hash_password

# Import all models to guarantee Base.metadata is fully populated
from app.models.models import (
    User,
    Conversation,
    ConversationMember,
    Message,
    GoldPriceHistory,
)

logger = logging.getLogger("webchat.migration")


MIGRATION_STATEMENTS: List[tuple[str, str]] = [
    # 1. users table columns
    (
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'USER' NOT NULL;",
        "add_users_role"
    ),
    (
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL;",
        "add_users_is_locked"
    ),
    (
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_online BOOLEAN DEFAULT FALSE NOT NULL;",
        "add_users_is_online"
    ),
    (
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMPTZ DEFAULT NOW();",
        "add_users_last_seen"
    ),

    # 2. system_settings table
    (
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            key VARCHAR(50) PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        """,
        "create_system_settings"
    ),

    # 3. gold_price_history table
    (
        """
        CREATE TABLE IF NOT EXISTS gold_price_history (
            id BIGSERIAL PRIMARY KEY,
            gold_type VARCHAR(100) NOT NULL,
            buy_price NUMERIC(15, 2) NOT NULL,
            sell_price NUMERIC(15, 2) NOT NULL,
            price_date VARCHAR(50),
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        """,
        "create_gold_price_history"
    ),

    # 4. gold_price_history indices
    (
        "CREATE INDEX IF NOT EXISTS ix_gold_price_history_gold_type ON gold_price_history (gold_type);",
        "idx_gold_type"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_gold_price_history_updated_at ON gold_price_history (updated_at);",
        "idx_gold_updated_at"
    ),
    (
        "CREATE INDEX IF NOT EXISTS ix_gold_type_updated ON gold_price_history (gold_type, updated_at);",
        "idx_gold_type_updated"
    ),

    # 5. conversations table
    (
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id VARCHAR(36) PRIMARY KEY,
            type VARCHAR(20) DEFAULT 'DIRECT' NOT NULL,
            name VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        "create_conversations"
    ),

    # 6. conversation_members table
    (
        """
        CREATE TABLE IF NOT EXISTS conversation_members (
            id VARCHAR(36) PRIMARY KEY,
            conversation_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            role VARCHAR(20) DEFAULT 'MEMBER' NOT NULL,
            joined_at TIMESTAMPTZ DEFAULT NOW(),
            last_read_message_id VARCHAR(36)
        );
        """,
        "create_conversation_members"
    ),

    # 7. messages table
    (
        """
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR(36) PRIMARY KEY,
            conversation_id VARCHAR(36) NOT NULL,
            sender_id VARCHAR(36) NOT NULL,
            content TEXT NOT NULL,
            client_temp_id VARCHAR(100),
            status VARCHAR(20) DEFAULT 'SENT' NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
        """,
        "create_messages"
    ),
]


async def execute_isolated_statement(sql_query: str, desc: str, params: dict = None) -> Dict[str, Any]:
    """
    Executes a single SQL statement in an independent transaction.
    Guarantees that a failure in one statement does NOT rollback or abort others.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text(sql_query), params or {})
        return {"step": desc, "status": "SUCCESS"}
    except Exception as e:
        logger.warning(f"Migration step '{desc}' returned warning/error (continuing): {e}")
        return {"step": desc, "status": "WARNING", "error": str(e)}


async def seed_admin_and_promote() -> List[Dict[str, Any]]:
    """
    Promotes existing Thang/Admin accounts to ADMIN and guarantees standard admin account exists.
    Uses safe casting id::text for PostgreSQL compatibility.
    """
    results = []

    # 1. Promote Thang / Admin
    promote_sql = "UPDATE users SET role = 'ADMIN' WHERE username IN ('admin', 'thang', 'thanglq01', 'nguyenvana') OR username ILIKE '%thang%';"
    res_promote = await execute_isolated_statement(promote_sql, "promote_admin_accounts")
    results.append(res_promote)

    # 2. Unlock all admins
    unlock_sql = "UPDATE users SET is_locked = FALSE WHERE role = 'ADMIN';"
    res_unlock = await execute_isolated_statement(unlock_sql, "unlock_admins")
    results.append(res_unlock)

    # 3. Rename old conflicting email with safe id::text casting
    rename_sql = "UPDATE users SET email = 'old_admin_' || id::text || '@gmail.com' WHERE email = 'admin@gmail.com' AND username != 'admin';"
    res_rename = await execute_isolated_statement(rename_sql, "rename_conflicting_admin_email")
    results.append(res_rename)

    # 4. Check & insert/update standard admin
    pwd_hash = hash_password("123456")
    try:
        async with engine.begin() as conn:
            check_res = await conn.execute(text("SELECT id FROM users WHERE username = 'admin';"))
            existing = check_res.scalar_one_or_none()
            if existing:
                await conn.execute(
                    text("UPDATE users SET email = 'admin@gmail.com', password_hash = :pwd_hash, role = 'ADMIN', full_name = 'Administrator', is_locked = FALSE WHERE username = 'admin';"),
                    {"pwd_hash": pwd_hash}
                )
                results.append({"step": "update_standard_admin", "status": "SUCCESS", "action": "updated"})
            else:
                admin_id = str(uuid.uuid4())
                await conn.execute(
                    text("INSERT INTO users (id, username, email, password_hash, full_name, avatar_url, role, is_locked, is_online, created_at) "
                         "VALUES (:id, 'admin', 'admin@gmail.com', :pwd_hash, 'Administrator', 'https://api.dicebear.com/7.x/bottts/svg?seed=admin', 'ADMIN', false, false, NOW());"),
                    {"id": admin_id, "pwd_hash": pwd_hash}
                )
                results.append({"step": "create_standard_admin", "status": "SUCCESS", "action": "created"})
    except Exception as e:
        logger.error(f"Error ensuring standard admin: {e}")
        results.append({"step": "ensure_standard_admin", "status": "WARNING", "error": str(e)})

    return results


async def verify_db_schema() -> Dict[str, Any]:
    """
    Inspects PostgreSQL information_schema to verify tables and columns.
    Returns a full diagnostic report.
    """
    report: Dict[str, Any] = {
        "status": "UNKNOWN",
        "tables": [],
        "users_columns": {},
        "gold_price_count": 0,
        "users_count": 0,
    }
    try:
        async with engine.connect() as conn:
            # 1. Check all tables
            res_tables = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """))
            tables = [r[0] for r in res_tables.fetchall()]
            report["tables"] = tables

            # 2. Check users columns
            res_cols = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users';
            """))
            report["users_columns"] = {r[0]: r[1] for r in res_cols.fetchall()}

            # 3. Gold price count
            if "gold_price_history" in tables:
                cnt = await conn.execute(text("SELECT COUNT(*) FROM gold_price_history;"))
                report["gold_price_count"] = cnt.scalar() or 0

            # 4. Users count
            if "users" in tables:
                u_cnt = await conn.execute(text("SELECT COUNT(*) FROM users;"))
                report["users_count"] = u_cnt.scalar() or 0

            # Determine overall health
            has_gold = "gold_price_history" in tables
            has_locked = "is_locked" in report["users_columns"]
            has_role = "role" in report["users_columns"]
            has_settings = "system_settings" in tables

            if has_gold and has_locked and has_role and has_settings:
                report["status"] = "HEALTHY"
            else:
                report["status"] = "PARTIAL"
                report["missing"] = {
                    "gold_price_history": not has_gold,
                    "users.is_locked": not has_locked,
                    "users.role": not has_role,
                    "system_settings": not has_settings,
                }
    except Exception as e:
        logger.error(f"Error during schema verification: {e}")
        report["status"] = "ERROR"
        report["error"] = str(e)

    return report


async def run_database_migrations() -> Dict[str, Any]:
    """
    Master self-healing migration runner:
    1. Base.metadata.create_all (creates any completely missing tables)
    2. Runs each column / table migration statement in isolation
    3. Promotes admin & guarantees default credentials
    4. Runs verification query and returns complete diagnostics
    """
    logger.info("Starting self-healing database migration...")
    results: List[Dict[str, Any]] = []

    # Step 1: Base.metadata.create_all in isolated transaction
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        results.append({"step": "Base.metadata.create_all", "status": "SUCCESS"})
    except Exception as e:
        logger.warning(f"Base.metadata.create_all warning: {e}")
        results.append({"step": "Base.metadata.create_all", "status": "WARNING", "error": str(e)})

    # Step 2: Run all DDL statements independently
    for sql_stmt, desc in MIGRATION_STATEMENTS:
        res = await execute_isolated_statement(sql_stmt, desc)
        results.append(res)

    # Step 3: Seed and promote admins
    seed_res = await seed_admin_and_promote()
    results.extend(seed_res)

    # Step 4: Verification
    verification = await verify_db_schema()

    logger.info(f"Database migration completed. Schema status: {verification.get('status')}")
    return {
        "status": verification.get("status"),
        "steps": results,
        "verification": verification,
    }
