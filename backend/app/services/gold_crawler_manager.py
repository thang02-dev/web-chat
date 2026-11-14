import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Union

import httpx
from sqlalchemy import text, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.models import User, Message, ConversationMember, GoldPriceHistory
from app.services.gold_service import gold_price_service
from app.services.chat_service import ChatService
from app.websocket.manager import manager

logger = logging.getLogger("webchat.gold.crawler_manager")

VN_TZ = timezone(timedelta(hours=7))
BOT_TEMP_ID_PREFIX = "gold_bot_"


def _format_vnd(val: Optional[Union[Decimal, float, int]]) -> str:
    if val is None:
        return "0đ"
    try:
        num = int(round(float(val)))
        return f"{num:,}".replace(",", ".") + "đ"
    except Exception:
        return f"{val}đ"


def _format_delta(delta: Optional[float]) -> str:
    if delta is None or delta == 0:
        return ""
    sign = "▲ +" if delta > 0 else "▼ -"
    return f" ({sign}{_format_vnd(abs(delta))})"


class GoldCrawlerManager:
    def __init__(self):
        self.interval_minutes: int = 10
        self.is_enabled: bool = True
        self.is_crawling: bool = False
        self.last_crawl_at: Optional[datetime] = None
        self.last_crawl_status: str = "IDLE"  # "IDLE", "SUCCESS", "ERROR"
        self.last_crawl_count: int = 0
        self.last_crawl_message: str = "Hệ thống sẵn sàng"
        self.next_crawl_at: Optional[datetime] = None
        self.recent_logs: List[Dict] = []

        # Cấu hình gửi tin nhắn lịch sử call từ Admin -> Tài khoản nhận
        self.notify_user_id: Optional[str] = None
        self.notify_mode: str = "ALWAYS"  # "ALWAYS" (Mỗi lần call) | "CHANGE_ONLY" (Chỉ khi giá thay đổi)
        self.sender_username: str = "admin"
        self.last_cleanup_date: Optional[str] = None
        self.bot_message_count: int = 0

        # Keep-Alive chống spin-down trên Cloud
        self.public_base_url: Optional[str] = (
            os.getenv("RENDER_EXTERNAL_URL")
            or os.getenv("PUBLIC_BACKEND_URL")
            or None
        )
        self._last_keepalive_at: float = 0.0

        self._sleep_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @asynccontextmanager
    async def _session_scope(self, db: Optional[AsyncSession] = None):
        if db is not None:
            yield db
        else:
            async with AsyncSessionLocal() as session:
                yield session

    @staticmethod
    async def _upsert_setting(db: AsyncSession, key: str, value: str):
        await db.execute(
            text("""
                INSERT INTO system_settings (key, value, updated_at)
                VALUES (:key, :val, NOW())
                ON CONFLICT (key) DO UPDATE SET value = :val, updated_at = NOW();
            """),
            {"key": key, "val": value}
        )

    def register_public_url(self, base_url: str):
        """Ghi nhận URL public của server để tự động gửi Keep-Alive ping chống ngủ đông."""
        if not base_url:
            return
        cleaned = base_url.rstrip("/")
        if any(h in cleaned for h in ("localhost", "127.0.0.1", "0.0.0.0", "test")):
            return
        if self.public_base_url != cleaned:
            self.public_base_url = cleaned
            logger.info(f"Registered public backend URL for keep-alive: {self.public_base_url}")

    async def init_from_db(self, db: Optional[AsyncSession] = None):
        """Khởi tạo cấu hình crawler và khôi phục lịch sử quét từ bảng system_settings."""
        try:
            async with self._session_scope(db) as session:
                res = await session.execute(text("SELECT key, value FROM system_settings;"))
                settings_map = {row[0]: row[1] for row in res.fetchall()}

                if "crawler_interval_minutes" in settings_map:
                    try:
                        self.interval_minutes = max(1, min(1440, int(settings_map["crawler_interval_minutes"])))
                    except ValueError:
                        pass

                if "crawler_enabled" in settings_map:
                    self.is_enabled = settings_map["crawler_enabled"].lower() in ("true", "1", "yes")

                if "crawler_notify_user_id" in settings_map:
                    val_uid = settings_map["crawler_notify_user_id"].strip()
                    self.notify_user_id = val_uid if val_uid else None

                if "crawler_notify_mode" in settings_map:
                    val_mode = settings_map["crawler_notify_mode"].strip().upper()
                    if val_mode in ("ALWAYS", "CHANGE_ONLY"):
                        self.notify_mode = val_mode

                if "crawler_last_cleanup_date" in settings_map:
                    self.last_cleanup_date = settings_map["crawler_last_cleanup_date"].strip() or None

                if "public_backend_url" in settings_map and not self.public_base_url:
                    self.register_public_url(settings_map["public_backend_url"].strip())

                if "crawler_last_state" in settings_map:
                    try:
                        state_data = json.loads(settings_map["crawler_last_state"])
                        if state_data.get("last_crawl_at"):
                            dt = datetime.fromisoformat(state_data["last_crawl_at"])
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            self.last_crawl_at = dt
                        self.last_crawl_status = state_data.get("last_crawl_status", self.last_crawl_status)
                        self.last_crawl_count = int(state_data.get("last_crawl_count", 0))
                        self.last_crawl_message = state_data.get("last_crawl_message", self.last_crawl_message)
                    except Exception as e:
                        logger.warning(f"Could not parse crawler_last_state: {e}")

                if "crawler_recent_logs" in settings_map:
                    try:
                        logs_data = json.loads(settings_map["crawler_recent_logs"])
                        if isinstance(logs_data, list):
                            self.recent_logs = logs_data[:25]
                    except Exception as e:
                        logger.warning(f"Could not parse crawler_recent_logs: {e}")

                # Nếu chưa có last_crawl_at trong system_settings, lấy mốc mới nhất từ gold_price_history
                if self.last_crawl_at is None:
                    max_res = await session.execute(select(func.max(GoldPriceHistory.updated_at)))
                    max_dt = max_res.scalar_one_or_none()
                    if max_dt:
                        if max_dt.tzinfo is None:
                            max_dt = max_dt.replace(tzinfo=timezone.utc)
                        self.last_crawl_at = max_dt
                        self.last_crawl_status = "SUCCESS"
                        self.last_crawl_message = "Đã đồng bộ từ lịch sử giá vàng gần nhất."

                # Đếm số lượng tin nhắn bot hiện tại
                await self._refresh_bot_message_count(session)

                # Kiểm tra nếu đã qua ngày mới (00:00 VN) trong lúc server tắt thì dọn dẹp ngay
                today_vn = datetime.now(VN_TZ).strftime("%Y-%m-%d")
                if self.last_cleanup_date is None:
                    self.last_cleanup_date = today_vn
                    await self._upsert_setting(session, "crawler_last_cleanup_date", today_vn)
                    await session.commit()
                elif self.last_cleanup_date != today_vn:
                    await self.cleanup_bot_messages(db=session, new_date_str=today_vn)

            # Tính toán next_crawl_at dựa trên last_crawl_at
            now_utc = datetime.now(timezone.utc)
            if self.is_enabled:
                if self.last_crawl_at is None:
                    self.next_crawl_at = now_utc
                else:
                    candidate = self.last_crawl_at + timedelta(minutes=self.interval_minutes)
                    self.next_crawl_at = candidate if candidate > now_utc else now_utc
            else:
                self.next_crawl_at = None

            logger.info(
                f"GoldCrawlerManager initialized: interval={self.interval_minutes}m, "
                f"enabled={self.is_enabled}, notify_user_id={self.notify_user_id}, "
                f"notify_mode={self.notify_mode}, last_crawl_at={self.last_crawl_at}"
            )
        except Exception as e:
            logger.warning(f"Could not load crawler settings from DB (using defaults): {e}")

    async def _refresh_bot_message_count(self, db: AsyncSession):
        try:
            cnt_res = await db.execute(
                select(func.count(Message.id)).where(Message.client_temp_id.like(f"{BOT_TEMP_ID_PREFIX}%"))
            )
            self.bot_message_count = cnt_res.scalar_one_or_none() or 0
        except Exception:
            pass

    async def _persist_runtime_state(self, db: AsyncSession):
        """Lưu trạng thái lần quét gần nhất và nhật ký vào system_settings để không mất khi server restart."""
        try:
            state_payload = json.dumps({
                "last_crawl_at": self.last_crawl_at.isoformat() if self.last_crawl_at else None,
                "last_crawl_status": self.last_crawl_status,
                "last_crawl_count": self.last_crawl_count,
                "last_crawl_message": self.last_crawl_message,
            }, ensure_ascii=False)
            logs_payload = json.dumps(self.recent_logs[:25], ensure_ascii=False)

            await self._upsert_setting(db, "crawler_last_state", state_payload)
            await self._upsert_setting(db, "crawler_recent_logs", logs_payload)
            if self.public_base_url:
                await self._upsert_setting(db, "public_backend_url", self.public_base_url)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist crawler runtime state to DB: {e}")

    async def save_settings(
        self,
        db: AsyncSession,
        interval_minutes: int,
        is_enabled: bool,
        notify_user_id: Optional[str] = None,
        notify_mode: str = "ALWAYS"
    ):
        """Lưu cấu hình mới vào DB và cập nhật runtime ngay lập tức."""
        clamped_interval = max(1, min(1440, interval_minutes))
        clean_uid = notify_user_id.strip() if notify_user_id and notify_user_id.strip() else None
        clean_mode = notify_mode.upper().strip() if notify_mode else "ALWAYS"
        if clean_mode not in ("ALWAYS", "CHANGE_ONLY"):
            clean_mode = "ALWAYS"

        self.interval_minutes = clamped_interval
        self.is_enabled = is_enabled
        self.notify_user_id = clean_uid
        self.notify_mode = clean_mode

        await self._upsert_setting(db, "crawler_interval_minutes", str(clamped_interval))
        await self._upsert_setting(db, "crawler_enabled", "true" if is_enabled else "false")
        await self._upsert_setting(db, "crawler_notify_user_id", clean_uid or "")
        await self._upsert_setting(db, "crawler_notify_mode", clean_mode)

        today_vn = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        if not self.last_cleanup_date:
            self.last_cleanup_date = today_vn
            await self._upsert_setting(db, "crawler_last_cleanup_date", today_vn)

        await db.commit()
        await self._refresh_bot_message_count(db)

        now_utc = datetime.now(timezone.utc)
        if self.is_enabled:
            if self.last_crawl_at is not None:
                candidate = self.last_crawl_at + timedelta(minutes=self.interval_minutes)
                self.next_crawl_at = candidate if candidate > now_utc else now_utc
            else:
                self.next_crawl_at = now_utc
        else:
            self.next_crawl_at = None

        # Đánh thức vòng lặp ngủ để áp dụng cấu hình ngay lập tức
        self._sleep_event.set()
        logger.info(
            f"Crawler settings updated: interval={self.interval_minutes}m, "
            f"enabled={self.is_enabled}, notify_user_id={self.notify_user_id}, notify_mode={self.notify_mode}"
        )

    def _build_notification_content(
        self,
        now_utc: datetime,
        source: str,
        status_str: str,
        saved: int,
        msg: str
    ) -> str:
        """Tạo nội dung tin nhắn báo cáo kết quả quét giá vàng gửi từ Admin."""
        vn_time_str = now_utc.astimezone(VN_TZ).strftime("%H:%M:%S %d/%m/%Y")
        source_label = "Thủ công" if source == "MANUAL" else f"Tự động ({self.interval_minutes} phút/lần)"

        lines = [
            "🤖 [BOT GIÁ VÀNG - LỊCH SỬ CALL]",
            f"🕒 Thời gian: {vn_time_str}",
            f"⚙️ Phương thức: {source_label}",
        ]

        if status_str != "SUCCESS":
            lines.append(f"❌ Trạng thái: Lỗi kiểm tra giá ({msg})")
        elif saved > 0:
            lines.append(f"📈 Kết quả: Phát hiện {saved} loại vàng có biến động giá!")
        else:
            lines.append("✅ Kết quả: Giá vàng không thay đổi so với lần kiểm tra trước.")

        # Đính kèm chi tiết bảng giá vừa kiểm tra
        scraped = getattr(gold_price_service, "last_scraped", []) or []
        changes = getattr(gold_price_service, "last_changes", []) or []
        changes_by_type = {c["gold_type"]: c for c in changes if "gold_type" in c}

        if scraped:
            lines.append("────────────────────")
            for dto in scraped:
                chg = changes_by_type.get(dto.gold_type)
                buy_delta_str = _format_delta(chg.get("buy_delta")) if chg else ""
                sell_delta_str = _format_delta(chg.get("sell_delta")) if chg else ""
                lines.append(
                    f"• {dto.gold_type}: Mua {_format_vnd(dto.buy_price)}{buy_delta_str} | "
                    f"Bán {_format_vnd(dto.sell_price)}{sell_delta_str}"
                )

        lines.append("🧹 (Tin nhắn lịch sử bot tự động xóa lúc 00:00)")
        return "\n".join(lines)

    async def _send_crawl_notification_if_needed(
        self,
        db: AsyncSession,
        now_utc: datetime,
        source: str,
        status_str: str,
        saved: int,
        msg: str
    ) -> bool:
        """
        Gửi tin nhắn từ tài khoản admin tới tài khoản notify_user_id dựa trên cấu hình:
        - notify_mode == 'ALWAYS': Gửi mỗi lần bot call để kiểm tra giá vàng
        - notify_mode == 'CHANGE_ONLY': Chỉ gửi khi giá thay đổi (saved > 0)
        """
        if not self.notify_user_id:
            return False

        if self.notify_mode == "CHANGE_ONLY" and saved <= 0:
            logger.debug("Skip bot chat notification: notify_mode=CHANGE_ONLY and saved=0.")
            return False

        try:
            # 1. Tìm tài khoản nguồn gửi: admin
            admin_res = await db.execute(select(User).where(User.username == "admin"))
            admin_user = admin_res.scalars().first()
            if not admin_user:
                fallback_res = await db.execute(
                    select(User).where(User.role == "ADMIN").order_by(User.created_at.asc()).limit(1)
                )
                admin_user = fallback_res.scalars().first()

            if not admin_user:
                logger.warning("Cannot send bot notification: No admin user found in database.")
                return False

            self.sender_username = admin_user.username

            # 2. Kiểm tra tài khoản người nhận tồn tại và là Quản lý (ADMIN)
            target_res = await db.execute(select(User).where(User.id == self.notify_user_id))
            target_user = target_res.scalars().first()
            if not target_user:
                logger.warning(f"Cannot send bot notification: Target user {self.notify_user_id} not found.")
                return False
            if target_user.role != "ADMIN":
                logger.warning(f"Cannot send bot notification: Target user @{target_user.username} is not an ADMIN.")
                return False

            # 3. Lấy hoặc tạo cuộc trò chuyện giữa admin và tài khoản được chọn
            conv = await ChatService.get_or_create_bot_conversation(db, admin_user.id, target_user.id)

            # 4. Tạo nội dung và lưu tin nhắn với tiền tố client_temp_id = 'gold_bot_...'
            content = self._build_notification_content(now_utc, source, status_str, saved, msg)
            bot_temp_id = f"{BOT_TEMP_ID_PREFIX}{uuid.uuid4().hex}"

            msg_resp, member_ids = await ChatService.create_message(
                db,
                conversation_id=conv.id,
                sender_id=admin_user.id,
                content=content,
                client_temp_id=bot_temp_id
            )

            await self._refresh_bot_message_count(db)

            # 5. Đẩy sự kiện WebSocket thời gian thực tới các thành viên cuộc trò chuyện
            await manager.broadcast_to_users(
                {
                    "type": "NEW_MESSAGE",
                    "payload": msg_resp.model_dump(mode="json")
                },
                member_ids
            )
            logger.info(
                f"Sent gold crawl notification message from @{admin_user.username} "
                f"to @{target_user.username} (mode={self.notify_mode}, saved={saved})."
            )
            return True
        except Exception as e:
            logger.error(f"Error sending crawl notification message: {e}", exc_info=True)
            return False

    async def cleanup_bot_messages(
        self,
        db: Optional[AsyncSession] = None,
        new_date_str: Optional[str] = None
    ) -> int:
        """
        Xóa tất cả tin nhắn lịch sử call của bot (client_temp_id LIKE 'gold_bot_%')
        từ admin -> tài khoản nhận để tránh nặng DB.
        """
        deleted_count = 0
        affected_conv_ids: List[str] = []
        member_ids_to_notify: List[str] = []

        try:
            async with self._session_scope(db) as session:
                # Tìm các conversation_id có chứa tin nhắn bot
                conv_stmt = (
                    select(Message.conversation_id)
                    .where(Message.client_temp_id.like(f"{BOT_TEMP_ID_PREFIX}%"))
                    .distinct()
                )
                conv_res = await session.execute(conv_stmt)
                affected_conv_ids = [r for r in conv_res.scalars().all() if r]

                if affected_conv_ids:
                    mem_stmt = (
                        select(ConversationMember.user_id)
                        .where(ConversationMember.conversation_id.in_(affected_conv_ids))
                        .distinct()
                    )
                    mem_res = await session.execute(mem_stmt)
                    member_ids_to_notify = [u for u in mem_res.scalars().all() if u]

                # Thực hiện xóa toàn bộ tin nhắn thông báo của bot
                del_stmt = delete(Message).where(Message.client_temp_id.like(f"{BOT_TEMP_ID_PREFIX}%"))
                del_res = await session.execute(del_stmt)
                deleted_count = del_res.rowcount or 0

                today_vn = new_date_str or datetime.now(VN_TZ).strftime("%Y-%m-%d")
                self.last_cleanup_date = today_vn
                self.bot_message_count = 0
                await self._upsert_setting(session, "crawler_last_cleanup_date", today_vn)
                await session.commit()

            logger.info(
                f"Cleaned up {deleted_count} gold bot notification message(s) "
                f"(cleanup_date={self.last_cleanup_date})."
            )

            # Thông báo qua WebSocket để giao diện Chat xóa các tin nhắn bot ngay lập tức
            if deleted_count > 0 and member_ids_to_notify:
                await manager.broadcast_to_users(
                    {
                        "type": "BOT_MESSAGES_CLEARED",
                        "payload": {
                            "conversation_ids": affected_conv_ids,
                            "deleted_count": deleted_count
                        }
                    },
                    member_ids_to_notify
                )
        except Exception as e:
            logger.error(f"Error cleaning up bot messages: {e}", exc_info=True)

        return deleted_count

    async def check_and_run_midnight_cleanup(
        self,
        db: Optional[AsyncSession] = None,
        now_vn: Optional[datetime] = None
    ) -> int:
        """
        Kiểm tra nếu đồng hồ giờ Việt Nam (UTC+7) đã bước sang ngày mới (00:00)
        thì tự động xóa sạch toàn bộ tin nhắn thông báo của bot.
        """
        current_vn = now_vn or datetime.now(VN_TZ)
        today_vn_str = current_vn.strftime("%Y-%m-%d")

        if self.last_cleanup_date is None:
            self.last_cleanup_date = today_vn_str
            try:
                async with self._session_scope(db) as session:
                    await self._upsert_setting(session, "crawler_last_cleanup_date", today_vn_str)
                    await session.commit()
            except Exception:
                pass
            return 0

        if today_vn_str != self.last_cleanup_date:
            logger.info(
                f"=== [Gold Bot Cleanup] Midnight 00:00 VN crossed "
                f"({self.last_cleanup_date} -> {today_vn_str}). Deleting bot messages... ==="
            )
            return await self.cleanup_bot_messages(db=db, new_date_str=today_vn_str)

        return 0

    async def trigger_crawl(
        self,
        source: str = "MANUAL",
        db: Optional[AsyncSession] = None
    ) -> Dict:
        """Kích hoạt quét giá vàng ngay lập tức (thủ công hoặc tự động) và gửi tin nhắn báo cáo nếu bật."""
        if self.is_crawling:
            return {
                "success": False,
                "saved": 0,
                "message": "Quá trình quét giá vàng đang được thực thi. Vui lòng đợi trong giây lát."
            }

        self.is_crawling = True
        start_time = time.time()
        now_utc = datetime.now(timezone.utc)
        saved = 0
        status_str = "SUCCESS"
        msg = ""
        notified = False

        try:
            # Kiểm tra dọn dẹp 00:00 trước khi quét
            await self.check_and_run_midnight_cleanup(db=db)

            async with self._session_scope(db) as session:
                saved = await gold_price_service.crawl_and_save_changed_prices(session)
                if saved > 0:
                    msg = f"Quét thành công! Đã phát hiện và lưu {saved} biến động giá mới."
                else:
                    msg = "Quét thành công! Không có thay đổi giá so với lần cập nhật trước."

                # Gửi tin nhắn từ Admin -> Tài khoản nhận nếu được cấu hình
                notified = await self._send_crawl_notification_if_needed(
                    session, now_utc, source, status_str, saved, msg
                )
        except Exception as e:
            status_str = "ERROR"
            msg = f"Lỗi quét giá vàng: {str(e)}"
            logger.error(f"Error during crawl ({source}): {e}", exc_info=True)
            try:
                async with self._session_scope(db) as session:
                    notified = await self._send_crawl_notification_if_needed(
                        session, now_utc, source, status_str, 0, msg
                    )
            except Exception:
                pass
        finally:
            self.is_crawling = False
            duration_ms = int((time.time() - start_time) * 1000)

            self.last_crawl_at = now_utc
            self.last_crawl_status = status_str
            self.last_crawl_count = saved
            self.last_crawl_message = msg

            if self.is_enabled:
                self.next_crawl_at = now_utc + timedelta(minutes=self.interval_minutes)
            else:
                self.next_crawl_at = None

            log_entry = {
                "id": str(uuid.uuid4())[:8],
                "timestamp": now_utc.isoformat(),
                "source": "Thủ công" if source == "MANUAL" else "Tự động",
                "status": status_str,
                "saved_count": saved,
                "message": msg,
                "duration_ms": duration_ms
            }
            self.recent_logs.insert(0, log_entry)
            if len(self.recent_logs) > 25:
                self.recent_logs.pop()

            try:
                async with self._session_scope(db) as session:
                    await self._persist_runtime_state(session)
            except Exception as e:
                logger.warning(f"Failed to persist crawl log state: {e}")

        return {
            "success": status_str == "SUCCESS",
            "saved": saved,
            "notified": notified,
            "message": msg,
            "duration_ms": duration_ms
        }

    async def _maybe_send_keepalive_ping(self):
        """Gửi HTTP GET tới public health endpoint mỗi 4 phút để giữ Cloud container không bị ngủ đông."""
        if not self.is_enabled or not self.public_base_url:
            return
        now_mono = time.monotonic()
        if now_mono - self._last_keepalive_at < 240.0:
            return
        self._last_keepalive_at = now_mono
        ping_url = f"{self.public_base_url}/api/health"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                await client.get(ping_url, headers={"X-Keep-Alive": "gold-bot"})
                logger.debug(f"Keep-alive self-ping sent to {ping_url}")
        except Exception as e:
            logger.debug(f"Keep-alive self-ping skipped/failed: {e}")

    def ensure_scheduler_alive(self):
        """
        Đảm bảo background loop luôn sống và tự động đánh thức nếu đã quá hạn quét
        (hữu ích khi container vừa thức dậy sau cold-start).
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if self._task is None or self._task.done():
            logger.info("Restarting GoldCrawlerManager background task...")
            self._task = loop.create_task(self.run_loop())

        if self.is_enabled and not self.is_crawling:
            now_utc = datetime.now(timezone.utc)
            if self.next_crawl_at is None or now_utc >= self.next_crawl_at:
                self._sleep_event.set()

    async def run_loop(self):
        """Vòng lặp chạy crawler nền dựa trên chu kỳ đã cấu hình và tự động xóa tin nhắn bot lúc 00:00."""
        logger.info("Gold crawler scheduler loop started.")
        await asyncio.sleep(2)  # Chờ khởi động server ổn định

        while True:
            try:
                # 1. Kiểm tra mốc 00:00 (giờ Việt Nam UTC+7) để xóa tin nhắn bot
                await self.check_and_run_midnight_cleanup()

                # 2. Gửi Keep-Alive ping định kỳ nếu có public URL
                await self._maybe_send_keepalive_ping()

                if not self.is_enabled:
                    self.next_crawl_at = None
                    self._sleep_event.clear()
                    try:
                        await asyncio.wait_for(self._sleep_event.wait(), timeout=20.0)
                    except asyncio.TimeoutError:
                        pass
                    self._sleep_event.clear()
                    continue

                now_utc = datetime.now(timezone.utc)

                # 3. Xác định thời điểm quét tiếp theo dựa trên last_crawl_at thực tế
                if self.next_crawl_at is None:
                    if self.last_crawl_at is None:
                        self.next_crawl_at = now_utc
                    else:
                        candidate = self.last_crawl_at + timedelta(minutes=self.interval_minutes)
                        self.next_crawl_at = candidate if candidate > now_utc else now_utc

                # 4. Nếu đã tới hạn (hoặc quá hạn khi vừa khởi động) -> Quét ngay lập tức!
                if now_utc >= self.next_crawl_at:
                    logger.info(f"=== [Gold Scheduler] Starting scheduled crawl (every {self.interval_minutes}m) ===")
                    await self.trigger_crawl(source="SCHEDULED")
                    continue

                # 5. Ngủ theo nhịp ngắn (tối đa 15s) để phản hồi tức thì khi sang 00:00 hoặc đổi cấu hình
                remaining_seconds = max(1.0, (self.next_crawl_at - now_utc).total_seconds())
                sleep_chunk = min(15.0, remaining_seconds)

                self._sleep_event.clear()
                try:
                    await asyncio.wait_for(self._sleep_event.wait(), timeout=sleep_chunk)
                    self._sleep_event.clear()
                    logger.info("Crawler woke up early due to config/wake event. Recalculating...")
                except asyncio.TimeoutError:
                    pass

            except asyncio.CancelledError:
                logger.info("Gold crawler scheduler loop cancelled.")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in gold crawler loop: {e}", exc_info=True)
                await asyncio.sleep(10)

    def get_status(self) -> Dict:
        """Trả về toàn bộ trạng thái và cấu hình hiện tại của crawler."""
        return {
            "interval_minutes": self.interval_minutes,
            "is_enabled": self.is_enabled,
            "is_crawling": self.is_crawling,
            "last_crawl_at": self.last_crawl_at.isoformat() if self.last_crawl_at else None,
            "last_crawl_status": self.last_crawl_status,
            "last_crawl_count": self.last_crawl_count,
            "last_crawl_message": self.last_crawl_message,
            "next_crawl_at": self.next_crawl_at.isoformat() if self.next_crawl_at else None,
            "notify_user_id": self.notify_user_id,
            "notify_mode": self.notify_mode,
            "sender_username": self.sender_username,
            "last_cleanup_date": self.last_cleanup_date,
            "bot_message_count": self.bot_message_count,
            "recent_logs": self.recent_logs
        }


# Singleton instance
crawler_manager = GoldCrawlerManager()
