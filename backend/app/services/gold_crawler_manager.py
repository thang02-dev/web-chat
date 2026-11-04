import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.gold_service import gold_price_service

logger = logging.getLogger("webchat.gold.crawler_manager")

VN_TZ = timezone(timedelta(hours=7))


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
        self._sleep_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def init_from_db(self):
        """Khởi tạo cấu hình crawler từ bảng system_settings nếu có."""
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(text("SELECT value FROM system_settings WHERE key = 'crawler_interval_minutes';"))
                val = res.scalar_one_or_none()
                if val:
                    self.interval_minutes = max(1, min(1440, int(val)))

                res_en = await db.execute(text("SELECT value FROM system_settings WHERE key = 'crawler_enabled';"))
                val_en = res_en.scalar_one_or_none()
                if val_en is not None:
                    self.is_enabled = val_en.lower() in ("true", "1", "yes")

            logger.info(f"GoldCrawlerManager initialized: interval={self.interval_minutes}m, enabled={self.is_enabled}")
        except Exception as e:
            logger.warning(f"Could not load crawler settings from DB (using defaults): {e}")

    async def save_settings(self, db: AsyncSession, interval_minutes: int, is_enabled: bool):
        """Lưu cấu hình mới vào DB và cập nhật runtime ngay lập tức."""
        clamped_interval = max(1, min(1440, interval_minutes))
        self.interval_minutes = clamped_interval
        self.is_enabled = is_enabled

        # Persist to database
        await db.execute(text("""
            INSERT INTO system_settings (key, value, updated_at)
            VALUES ('crawler_interval_minutes', :interval, NOW())
            ON CONFLICT (key) DO UPDATE SET value = :interval, updated_at = NOW();
        """), {"interval": str(clamped_interval)})

        await db.execute(text("""
            INSERT INTO system_settings (key, value, updated_at)
            VALUES ('crawler_enabled', :enabled, NOW())
            ON CONFLICT (key) DO UPDATE SET value = :enabled, updated_at = NOW();
        """), {"enabled": "true" if is_enabled else "false"})

        await db.commit()

        if self.is_enabled:
            self.next_crawl_at = datetime.now(timezone.utc) + timedelta(minutes=self.interval_minutes)
        else:
            self.next_crawl_at = None

        # Wake up sleep loop to apply new timing immediately
        self._sleep_event.set()
        logger.info(f"Crawler settings updated: interval={self.interval_minutes}m, enabled={self.is_enabled}")

    async def trigger_crawl(self, source: str = "MANUAL") -> Dict:
        """Kích hoạt quét giá vàng ngay lập tức (thủ công hoặc tự động)."""
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

        try:
            async with AsyncSessionLocal() as db:
                saved = await gold_price_service.crawl_and_save_changed_prices(db)
                if saved > 0:
                    msg = f"Quét thành công! Đã phát hiện và lưu {saved} biến động giá mới."
                else:
                    msg = "Quét thành công! Không có thay đổi giá so với lần cập nhật trước."
        except Exception as e:
            status_str = "ERROR"
            msg = f"Lỗi quét giá vàng: {str(e)}"
            logger.error(f"Error during crawl ({source}): {e}", exc_info=True)
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

            # Append to in-memory audit log
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

        return {
            "success": status_str == "SUCCESS",
            "saved": saved,
            "message": msg,
            "duration_ms": duration_ms
        }

    async def run_loop(self):
        """Vòng lặp chạy crawler nền dựa trên chu kỳ đã cấu hình."""
        logger.info("Gold crawler scheduler loop started.")
        await asyncio.sleep(5)  # Wait for startup to complete

        while True:
            if not self.is_enabled:
                self.next_crawl_at = None
                self._sleep_event.clear()
                logger.info("Gold crawler is paused. Waiting for enable event...")
                await self._sleep_event.wait()
                self._sleep_event.clear()
                continue

            # Calculate next crawl time
            self.next_crawl_at = datetime.now(timezone.utc) + timedelta(minutes=self.interval_minutes)
            wait_seconds = self.interval_minutes * 60

            self._sleep_event.clear()
            try:
                # Sleep with interruptibility
                await asyncio.wait_for(self._sleep_event.wait(), timeout=wait_seconds)
                # If event was set early, restart loop with updated config
                self._sleep_event.clear()
                logger.info("Crawler woke up early due to config change. Recalculating...")
                continue
            except asyncio.TimeoutError:
                # Timer expired normally, time to crawl!
                pass

            if self.is_enabled:
                logger.info(f"=== [Gold Scheduler] Starting scheduled crawl (every {self.interval_minutes}m) ===")
                await self.trigger_crawl(source="SCHEDULED")

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
            "recent_logs": self.recent_logs
        }


# Singleton instance
crawler_manager = GoldCrawlerManager()

