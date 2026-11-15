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
from app.core.db_migration import run_database_migrations, verify_db_schema
from app.websocket.manager import manager
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.gold_service import gold_price_service
from app.services.gold_crawler_manager import crawler_manager
from app.api.v1 import auth, users, conversations, gold

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas & running self-healing migrations...")
    try:
        migration_report = await run_database_migrations()
        logger.info(f"Database migration completed. Status: {migration_report.get('status')}")
    except Exception as e:
        logger.error(f"Error during database migration in lifespan: {e}\n{traceback.format_exc()}")

    # Initialize crawler settings from database
    try:
        await crawler_manager.init_from_db()
    except Exception as e:
        logger.warning(f"Error initializing crawler settings from db: {e}")

    # Launch background gold crawler task
    crawler_task = asyncio.create_task(crawler_manager.run_loop())
    crawler_manager._task = crawler_task
    logger.info("Database schemas initialized and background gold crawler started.")

    yield

    logger.info("Stopping background gold crawler...")
    crawler_task.cancel()
    try:
        await crawler_task
    except asyncio.CancelledError:
        pass
    crawler_manager._task = None

    logger.info("Disposing engine connections...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


def _get_cors_headers(request: Request) -> dict:
    """Helper ensuring CORS headers are included even on unhandled exceptions."""
    origin = request.headers.get("origin")
    if not origin:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, User-Agent, DNT, Cache-Control, X-Mx-ReqToken, Keep-Alive, X-Requested-With, If-Modified-Since",
    }


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    headers = dict(exc.headers or {})
    headers.update(_get_cors_headers(request))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}\n{traceback.format_exc()}")
    headers = _get_cors_headers(request)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers=headers
    )


# CORS Middleware - allows origins and any https deployment previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"https?://.*",
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

@app.get("/api/v1/system/migrate", tags=["System"])
@app.post("/api/v1/system/migrate", tags=["System"])
@app.get("/api/migrate", tags=["System"])
@app.post("/api/migrate", tags=["System"])
async def trigger_system_migrate():
    """Manual self-healing database migration trigger."""
    return await run_database_migrations()

@app.middleware("http")
async def keep_crawler_alive_middleware(request: Request, call_next):
    host = request.url.hostname or ""
    if host and host not in ("test", "localhost", "127.0.0.1", "0.0.0.0"):
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme or "https")
        crawler_manager.register_public_url(f"{scheme}://{request.headers.get('host', host)}")
        crawler_manager.ensure_scheduler_alive()
    return await call_next(request)


@app.get("/api/v1/system/db-status", tags=["System"])
@app.get("/api/db-status", tags=["System"])
async def get_db_status():
    """Returns database tables and column health status."""
    return await verify_db_schema()

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "crawler_enabled": crawler_manager.is_enabled,
        "crawler_interval_minutes": crawler_manager.interval_minutes,
        "last_crawl_at": crawler_manager.last_crawl_at.isoformat() if crawler_manager.last_crawl_at else None,
        "next_crawl_at": crawler_manager.next_crawl_at.isoformat() if crawler_manager.next_crawl_at else None
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
    try:
        async with AsyncSessionLocal() as db:
            user = await UserService.get_by_id(db, user_id)
            if not user or getattr(user, "is_locked", False):
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            await UserService.set_online_status(db, user_id, True)
    except Exception as e:
        logger.error(f"Error during websocket authentication check: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

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
                content = (event_payload.get("content") or "").strip()
                client_temp_id = event_payload.get("client_temp_id")
                message_type = event_payload.get("message_type") or "TEXT"
                attachment_url = event_payload.get("attachment_url")
                reply_to_id = event_payload.get("reply_to_id")

                if conversation_id and (content or attachment_url):
                    async with AsyncSessionLocal() as db:
                        try:
                            msg_resp, member_ids = await ChatService.create_message(
                                db,
                                conversation_id=conversation_id,
                                sender_id=user_id,
                                content=content,
                                client_temp_id=client_temp_id,
                                message_type=message_type,
                                attachment_url=attachment_url,
                                reply_to_id=reply_to_id
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

            # 2b. Thả cảm xúc tin nhắn (Reaction)
            elif event_type == "REACT_MESSAGE":
                conversation_id = event_payload.get("conversation_id")
                message_id = event_payload.get("message_id")
                emoji = (event_payload.get("emoji") or "").strip()
                if conversation_id and message_id and emoji:
                    async with AsyncSessionLocal() as db:
                        try:
                            msg_resp, member_ids = await ChatService.toggle_reaction(
                                db, conversation_id, message_id, user_id, emoji
                            )
                            await manager.broadcast_to_users(
                                {
                                    "type": "MESSAGE_REACTION",
                                    "payload": {
                                        "conversation_id": conversation_id,
                                        "message_id": message_id,
                                        "reactions": msg_resp.reactions,
                                        "user_id": user_id,
                                        "emoji": emoji
                                    }
                                },
                                member_ids
                            )
                        except Exception as e:
                            logger.error(f"Error handling REACT_MESSAGE: {e}")

            # 2c. Ghim / Bỏ ghim tin nhắn
            elif event_type == "PIN_MESSAGE":
                conversation_id = event_payload.get("conversation_id")
                message_id = event_payload.get("message_id")
                if conversation_id and message_id:
                    async with AsyncSessionLocal() as db:
                        try:
                            msg_resp, member_ids = await ChatService.toggle_pin_message(
                                db, conversation_id, message_id, user_id
                            )
                            await manager.broadcast_to_users(
                                {
                                    "type": "MESSAGE_PINNED",
                                    "payload": {
                                        "conversation_id": conversation_id,
                                        "message_id": message_id,
                                        "is_pinned": msg_resp.is_pinned,
                                        "message": msg_resp.model_dump(mode="json")
                                    }
                                },
                                member_ids
                            )
                        except Exception as e:
                            logger.error(f"Error handling PIN_MESSAGE: {e}")

            # 2d. Thu hồi tin nhắn
            elif event_type == "RECALL_MESSAGE":
                conversation_id = event_payload.get("conversation_id")
                message_id = event_payload.get("message_id")
                if conversation_id and message_id:
                    async with AsyncSessionLocal() as db:
                        try:
                            msg_resp, member_ids = await ChatService.recall_message(
                                db, conversation_id, message_id, user_id
                            )
                            await manager.broadcast_to_users(
                                {
                                    "type": "MESSAGE_RECALLED",
                                    "payload": {
                                        "conversation_id": conversation_id,
                                        "message_id": message_id,
                                        "message": msg_resp.model_dump(mode="json")
                                    }
                                },
                                member_ids
                            )
                        except Exception as e:
                            logger.error(f"Error handling RECALL_MESSAGE: {e}")

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
