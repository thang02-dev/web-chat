from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import json
import logging
import uuid
import traceback
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base, get_db
from app.core.security import decode_token, hash_password
from app.websocket.manager import manager
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.gold_service import gold_price_service
from app.api.v1 import auth, users, conversations, gold

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

async def scheduled_gold_crawl_loop():
    logger.info("Background gold price crawler loop initialized.")
    await asyncio.sleep(5)  # Let startup finish
    while True:
        try:
            async with AsyncSessionLocal() as db:
                saved = await gold_price_service.crawl_and_save_changed_prices(db)
                if saved > 0:
                    logger.info(f"=== [Gold Scheduler] Đã lưu {saved} bản ghi mới có biến động giá. ===")
                else:
                    logger.debug("=== [Gold Scheduler] Quét xong: không có biến động giá. ===")
        except Exception as e:
            logger.error(f"=== [Gold Scheduler] Lỗi crawl định kỳ: {e} ===")
        await asyncio.sleep(600)  # 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Self-healing database migration for Cloud/Render environments
        try:
            logger.info("Verifying database schema and role column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'USER' NOT NULL;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL;"))
            
            # Promote administrative accounts
            await conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE username IN ('thang', 'thanglq01', 'nguyenvana', 'admin') OR username ILIKE '%thang%';"))
            
            # Ensure standard admin account exists: admin / 123456 / admin@gmail.com
            pwd_hash = hash_password("123456")
            admin_id = str(uuid.uuid4())
            await conn.execute(text("UPDATE users SET email = 'old_admin_' || id || '@gmail.com' WHERE email = 'admin@gmail.com' AND username != 'admin';"))
            
            res = await conn.execute(text("SELECT id FROM users WHERE username = 'admin';"))
            existing = res.scalar_one_or_none()
            if existing:
                await conn.execute(
                    text("UPDATE users SET email = 'admin@gmail.com', password_hash = :pwd_hash, role = 'ADMIN', full_name = 'Administrator' WHERE username = 'admin';"),
                    {"pwd_hash": pwd_hash}
                )
            else:
                await conn.execute(
                    text("INSERT INTO users (id, username, email, password_hash, full_name, avatar_url, role, is_online, created_at) "
                         "VALUES (:id, 'admin', 'admin@gmail.com', :pwd_hash, 'Administrator', 'https://api.dicebear.com/7.x/bottts/svg?seed=admin', 'ADMIN', false, NOW());"),
                    {"id": admin_id, "pwd_hash": pwd_hash}
                )

            # Ensure gold_price_history table & indices exist
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gold_price_history (
                    id BIGSERIAL PRIMARY KEY,
                    gold_type VARCHAR(100) NOT NULL,
                    buy_price NUMERIC(15, 2) NOT NULL,
                    sell_price NUMERIC(15, 2) NOT NULL,
                    price_date VARCHAR(50),
                    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_gold_price_history_gold_type ON gold_price_history (gold_type);
                CREATE INDEX IF NOT EXISTS ix_gold_price_history_updated_at ON gold_price_history (updated_at);
            """))

            logger.info("Database self-healing verification completed successfully.")
        except Exception as e:
            logger.error(f"Error during schema verification: {e}")

    # Launch background gold crawler task
    crawler_task = asyncio.create_task(scheduled_gold_crawl_loop())
    logger.info("Database schemas initialized and background gold crawler started.")

    yield

    logger.info("Stopping background gold crawler...")
    crawler_task.cancel()
    try:
        await crawler_task
    except asyncio.CancelledError:
        pass

    logger.info("Disposing engine connections...")
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(gold.router, prefix=settings.API_V1_STR)
app.include_router(gold.router, prefix="/api")

@app.post("/api/crawl", tags=["Gold Prices"])
@app.post(f"{settings.API_V1_STR}/crawl", tags=["Gold Prices"])
async def trigger_crawl_direct(db: AsyncSession = Depends(get_db)):
    return await gold.trigger_crawl(db)

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME
    }

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    WebSocket Gateway:
    - Xác thực JWT Token tại handshake.
    - Duy trì Presence (Online / Offline).
    - Truyền nhận tin nhắn 2 chiều thời gian thực.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify user exists & set online
    async with AsyncSessionLocal() as db:
        user = await UserService.get_by_id(db, user_id)
        if not user or user.is_locked:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await UserService.set_online_status(db, user_id, True)

    # Register active websocket
    await manager.connect(websocket, user_id)

    # Broadcast user is ONLINE to all
    await manager.broadcast_all({
        "type": "USER_STATUS",
        "payload": {"user_id": user_id, "is_online": True}
    })

    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                msg_json = json.loads(text_data)
            except Exception:
                continue

            event_type = msg_json.get("type")
            event_payload = msg_json.get("payload", {})

            # 1. Heartbeat Ping / Pong
            if event_type in ("PING", "HEARTBEAT"):
                await websocket.send_text(json.dumps({"type": "PONG"}))
                continue

            # 2. Gửi tin nhắn mới
            elif event_type == "SEND_MESSAGE":
                conversation_id = event_payload.get("conversation_id")
                content = event_payload.get("content", "").strip()
                client_temp_id = event_payload.get("client_temp_id")

                if conversation_id and content:
                    async with AsyncSessionLocal() as db:
                        try:
                            msg_resp, member_ids = await ChatService.create_message(
                                db,
                                conversation_id=conversation_id,
                                sender_id=user_id,
                                content=content,
                                client_temp_id=client_temp_id
                            )

                            # Broadcast NEW_MESSAGE tới toàn bộ thành viên phòng
                            await manager.broadcast_to_users(
                                {
                                    "type": "NEW_MESSAGE",
                                    "payload": msg_resp.model_dump(mode="json")
                                },
                                member_ids
                            )

                            # Gửi xác nhận (ACK) về cho sender
                            if client_temp_id:
                                await manager.send_personal_message(
                                    {
                                        "type": "MESSAGE_ACK",
                                        "payload": {
                                            "client_temp_id": client_temp_id,
                                            "message_id": msg_resp.id,
                                            "status": "SENT",
                                            "conversation_id": conversation_id
                                        }
                                    },
                                    user_id
                                )
                        except Exception as e:
                            logger.error(f"Error handling SEND_MESSAGE: {e}")

            # 3. Trạng thái soạn tin (Typing Indicator)
            elif event_type == "TYPING_STATUS":
                conversation_id = event_payload.get("conversation_id")
                is_typing = bool(event_payload.get("is_typing", False))
                if conversation_id:
                    async with AsyncSessionLocal() as db:
                        from app.models.models import ConversationMember
                        from sqlalchemy import select
                        res = await db.execute(
                            select(ConversationMember.user_id).where(
                                ConversationMember.conversation_id == conversation_id
                            )
                        )
                        members = [uid for uid in res.scalars().all() if uid != user_id]
                        await manager.broadcast_to_users(
                            {
                                "type": "TYPING_STATUS",
                                "payload": {
                                    "conversation_id": conversation_id,
                                    "user_id": user_id,
                                    "is_typing": is_typing
                                }
                            },
                            members
                        )

            # 4. Đánh dấu đã đọc (Mark as Read)
            elif event_type == "MARK_AS_READ":
                conversation_id = event_payload.get("conversation_id")
                last_message_id = event_payload.get("last_message_id")
                if conversation_id and last_message_id:
                    async with AsyncSessionLocal() as db:
                        member_ids = await ChatService.mark_messages_as_read(
                            db, conversation_id, user_id, last_message_id
                        )
                        await manager.broadcast_to_users(
                            {
                                "type": "MESSAGE_READ",
                                "payload": {
                                    "conversation_id": conversation_id,
                                    "user_id": user_id,
                                    "last_message_id": last_message_id
                                }
                            },
                            member_ids
                        )

    except WebSocketDisconnect:
        is_fully_offline = manager.disconnect(websocket, user_id)
        if is_fully_offline:
            async with AsyncSessionLocal() as db:
                await UserService.set_online_status(db, user_id, False)
            await manager.broadcast_all({
                "type": "USER_STATUS",
                "payload": {"user_id": user_id, "is_online": False}
            })
    except Exception as e:
        logger.warning(f"Unexpected WebSocket error: {e}")
        is_fully_offline = manager.disconnect(websocket, user_id)
        if is_fully_offline:
            async with AsyncSessionLocal() as db:
                await UserService.set_online_status(db, user_id, False)
            await manager.broadcast_all({
                "type": "USER_STATUS",
                "payload": {"user_id": user_id, "is_online": False}
            })

# Mount Frontend Vue Single Page App (Production Static Serving)
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(
            str(frontend_dist / "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
