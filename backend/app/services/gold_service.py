import inspect
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import GoldPriceHistory, GoldSource
from app.schemas.gold import (
    ExtractRules,
    GoldBatchViewModel,
    GoldCardViewModel,
    GoldPriceDto,
    GoldSourceCreate,
    GoldSourceDeletePreview,
    GoldSourcePreviewItem,
    GoldSourceTestResult,
    GoldSourceUpdate,
)
from app.services.gold_crawler import GoldCrawler, gold_crawler
from app.services.gold_scraper import ScrapeResult, coerce_extract_rules, scrape
from app.services.url_guard import validate_public_url
from app.websocket.gold_sse import gold_sse_manager

logger = logging.getLogger("webchat.gold.service")

# Múi giờ chuẩn Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

DEFAULT_GOLD_SOURCES = [
    {
        "name": "Hiệu Vàng Trữ",
        "url": "https://hieuvangtru.vn",
        "interval_minutes": 10,
        "is_enabled": True,
        "sort_order": 0,
    },
    {
        "name": "Ngọc Thịnh Jewelry",
        "url": "https://ngocthinh-jewelry.vn",
        "interval_minutes": 10,
        "is_enabled": True,
        "sort_order": 1,
    },
]


def to_vietnam_time(dt: Optional[datetime]) -> Optional[datetime]:
    """Chuyển đổi datetime sang múi giờ Việt Nam (UTC+7)."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ)


class GoldSourceService:
    """Quản lý danh sách cửa hàng vàng (CRUD, kéo thả thứ tự, quét thử không lưu dữ liệu)."""

    @staticmethod
    async def ensure_default_sources(db: AsyncSession) -> List[GoldSource]:
        stmt = select(GoldSource).order_by(GoldSource.sort_order.asc(), GoldSource.id.asc())
        res = await db.execute(stmt)
        existing = list(res.scalars().all())
        if existing:
            return existing

        created: List[GoldSource] = []
        for item in DEFAULT_GOLD_SOURCES:
            src = GoldSource(**item)
            db.add(src)
            created.append(src)
        await db.commit()
        for src in created:
            await db.refresh(src)

        if created:
            first_id = created[0].id
            await db.execute(
                update(GoldPriceHistory)
                .where(GoldPriceHistory.source_id.is_(None))
                .values(source_id=first_id)
            )
            await db.commit()

        return created

    @staticmethod
    async def list_sources(db: AsyncSession, enabled_only: bool = False) -> List[GoldSource]:
        await GoldSourceService.ensure_default_sources(db)
        stmt = select(GoldSource)
        if enabled_only:
            stmt = stmt.where(GoldSource.is_enabled.is_(True))
        stmt = stmt.order_by(GoldSource.sort_order.asc(), GoldSource.id.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_source(db: AsyncSession, source_id: int) -> Optional[GoldSource]:
        await GoldSourceService.ensure_default_sources(db)
        res = await db.execute(select(GoldSource).where(GoldSource.id == source_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def get_default_source(db: AsyncSession) -> Optional[GoldSource]:
        sources = await GoldSourceService.list_sources(db, enabled_only=True)
        if sources:
            return sources[0]
        all_sources = await GoldSourceService.list_sources(db, enabled_only=False)
        return all_sources[0] if all_sources else None

    @staticmethod
    async def _validate_source_urls(url: str, rules: Optional[ExtractRules]) -> None:
        await validate_public_url(url)
        if rules and rules.price_url:
            full_price_url = urljoin(url, rules.price_url)
            await validate_public_url(full_price_url)

    @staticmethod
    async def create_source(db: AsyncSession, payload: GoldSourceCreate) -> GoldSource:
        await GoldSourceService.ensure_default_sources(db)
        await GoldSourceService._validate_source_urls(payload.url, payload.extract_rules)

        max_res = await db.execute(select(func.max(GoldSource.sort_order)))
        max_order = max_res.scalar_one_or_none()
        next_order = (max_order + 1) if max_order is not None else 0

        rules_json = (
            json.dumps(payload.extract_rules.model_dump(exclude_none=True), ensure_ascii=False)
            if payload.extract_rules
            else None
        )

        new_src = GoldSource(
            name=payload.name,
            url=payload.url,
            interval_minutes=payload.interval_minutes,
            is_enabled=payload.is_enabled,
            sort_order=next_order,
            extract_rules=rules_json,
            last_status="NEVER",
            last_row_count=0,
        )
        db.add(new_src)
        await db.commit()
        await db.refresh(new_src)
        return new_src

    @staticmethod
    async def update_source(db: AsyncSession, source_id: int, payload: GoldSourceUpdate) -> Optional[GoldSource]:
        src = await GoldSourceService.get_source(db, source_id)
        if not src:
            return None

        target_url = payload.url if payload.url is not None else src.url
        target_rules = (
            payload.extract_rules
            if payload.extract_rules is not None
            else coerce_extract_rules(src.extract_rules)
        )
        if payload.url is not None or payload.extract_rules is not None:
            await GoldSourceService._validate_source_urls(target_url, target_rules)

        if payload.name is not None:
            src.name = payload.name
        if payload.url is not None:
            src.url = payload.url
        if payload.interval_minutes is not None:
            src.interval_minutes = payload.interval_minutes
        if payload.is_enabled is not None:
            src.is_enabled = payload.is_enabled
        if "extract_rules" in payload.model_fields_set:
            src.extract_rules = (
                json.dumps(payload.extract_rules.model_dump(exclude_none=True), ensure_ascii=False)
                if payload.extract_rules
                else None
            )

        await db.commit()
        await db.refresh(src)
        return src

    @staticmethod
    async def count_history(db: AsyncSession, source_id: int) -> int:
        res = await db.execute(
            select(func.count(GoldPriceHistory.id)).where(GoldPriceHistory.source_id == source_id)
        )
        return res.scalar_one_or_none() or 0

    @staticmethod
    async def delete_source(db: AsyncSession, source_id: int, preview_only: bool = False) -> Optional[GoldSourceDeletePreview]:
        src = await GoldSourceService.get_source(db, source_id)
        if not src:
            return None

        history_count = await GoldSourceService.count_history(db, source_id)
        if preview_only:
            return GoldSourceDeletePreview(
                source_id=src.id,
                name=src.name,
                history_count=history_count,
                deleted=False,
                message=f"Cửa hàng '{src.name}' đang có {history_count} bản ghi lịch sử giá vàng.",
            )

        name = src.name
        await db.execute(delete(GoldPriceHistory).where(GoldPriceHistory.source_id == source_id))
        await db.delete(src)
        await db.commit()

        await gold_sse_manager.broadcast_price_update(history_count, source_id=source_id)
        return GoldSourceDeletePreview(
            source_id=source_id,
            name=name,
            history_count=history_count,
            deleted=True,
            message=f"Đã xóa cửa hàng '{name}' cùng {history_count} bản ghi lịch sử giá.",
        )

    @staticmethod
    async def set_interval_for_all(db: AsyncSession, interval_minutes: int) -> List[GoldSource]:
        """Áp dụng cùng một chu kỳ quét cho toàn bộ cửa hàng."""
        sources = await GoldSourceService.list_sources(db, enabled_only=False)
        for s in sources:
            s.interval_minutes = interval_minutes
        await db.commit()
        return await GoldSourceService.list_sources(db, enabled_only=False)

    @staticmethod
    async def reorder_sources(db: AsyncSession, ordered_ids: List[int]) -> List[GoldSource]:
        sources = await GoldSourceService.list_sources(db, enabled_only=False)
        existing_ids = {s.id for s in sources}

        if len(ordered_ids) != len(set(ordered_ids)):
            raise ValueError("Danh sách ID cửa hàng bị trùng lặp.")
        if set(ordered_ids) != existing_ids:
            raise ValueError("Danh sách ID cửa hàng không khớp với dữ liệu hiện có.")

        by_id = {s.id: s for s in sources}
        for idx, sid in enumerate(ordered_ids):
            by_id[sid].sort_order = idx

        await db.commit()
        return await GoldSourceService.list_sources(db, enabled_only=False)

    @staticmethod
    async def run_test_scrape(
        url: str,
        extract_rules: Optional[ExtractRules] = None,
    ) -> GoldSourceTestResult:
        """
        Thực hiện quét thử 1 URL (retries=1), KHÔNG lưu vào gold_price_history,
        KHÔNG gửi tin nhắn bot, KHÔNG phát SSE.
        """
        start_ts = time.perf_counter()
        try:
            res = await scrape(url, rules=extract_rules, retries=1)
            if not res.prices:
                return GoldSourceTestResult(
                    success=False,
                    status="ERROR",
                    message="Không tìm thấy bảng giá vàng trên trang này.",
                    strategy=res.strategy,
                    row_count=0,
                    duration_ms=res.duration_ms,
                    price_date=res.price_date or None,
                    final_url=res.final_url,
                    preview=[],
                )

            preview_items = [
                GoldSourcePreviewItem(
                    gold_type=p.gold_type,
                    buy_price=float(p.buy_price),
                    sell_price=float(p.sell_price),
                    price_date=p.price_date or None,
                )
                for p in res.prices[:15]
            ]
            return GoldSourceTestResult(
                success=True,
                status="SUCCESS",
                message=f"Lấy thành công {len(res.prices)} loại vàng.",
                strategy=res.strategy,
                row_count=len(res.prices),
                duration_ms=res.duration_ms,
                price_date=res.price_date or None,
                final_url=res.final_url,
                preview=preview_items,
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_ts) * 1000)
            return GoldSourceTestResult(
                success=False,
                status="ERROR",
                message=f"Quét thử thất bại: {str(e)}",
                strategy="NONE",
                row_count=0,
                duration_ms=duration_ms,
                price_date=None,
                final_url=url,
                preview=[],
            )

    @staticmethod
    async def test_saved_source(db: AsyncSession, source_id: int) -> Optional[GoldSourceTestResult]:
        """
        Quét thử một cửa hàng đã lưu trong DB:
        Cập nhật trạng thái quét (last_status, last_message, last_scan_at, last_row_count...)
        nhưng tuyệt đối KHÔNG lưu dữ liệu vào gold_price_history.
        """
        src = await GoldSourceService.get_source(db, source_id)
        if not src:
            return None

        rules = coerce_extract_rules(src.extract_rules)
        test_res = await GoldSourceService.run_test_scrape(src.url, rules)

        src.last_scan_at = datetime.now(timezone.utc)
        src.last_status = test_res.status
        src.last_message = test_res.message
        src.last_row_count = test_res.row_count
        src.last_duration_ms = test_res.duration_ms
        src.last_strategy = test_res.strategy
        await db.commit()
        await db.refresh(src)

        return test_res


class GoldPriceService:
    def __init__(self):
        self.last_scraped: List[GoldPriceDto] = []
        self.last_changes: List[Dict] = []

    async def _fetch_prices_for_source(self, source: Optional[GoldSource]) -> ScrapeResult:
        """
        Hỗ trợ cả cơ chế monkeypatch `gold_crawler.fetch_gold_prices` trong test cũ
        lẫn engine đa chiến lược `scrape(source.url, source.extract_rules)`.
        """
        fn = gold_crawler.fetch_gold_prices
        is_default_bound = getattr(fn, "__func__", None) is GoldCrawler.fetch_gold_prices

        if not is_default_bound:
            start_ts = time.perf_counter()
            sig = inspect.signature(fn)
            if len(sig.parameters) == 0:
                scraped = await fn()
            else:
                scraped = await fn(
                    url=source.url if source else None,
                    rules=source.extract_rules if source else None,
                )
            duration_ms = int((time.perf_counter() - start_ts) * 1000)
            prices = list(scraped or [])
            p_date = prices[0].price_date if prices else ""
            return ScrapeResult(
                prices=prices,
                strategy="MOCK",
                price_date=p_date,
                final_url=source.url if source else gold_crawler.target_url,
                duration_ms=duration_ms,
            )

        target_url = source.url if source else gold_crawler.target_url
        target_rules = source.extract_rules if source else None
        return await scrape(target_url, rules=target_rules, retries=3)

    async def crawl_and_save_with_details(
        self,
        db: AsyncSession,
        source: Optional[GoldSource] = None,
        source_id: Optional[int] = None,
    ) -> Dict:
        """
        Quét giá vàng cho cửa hàng được chỉ định (hoặc cửa hàng mặc định đầu tiên),
        chỉ lưu khi có biến động giá theo (source_id, gold_type), cập nhật trạng thái cửa hàng,
        và trả về chi tiết phục vụ audit & tin nhắn thông báo bot.
        """
        if source is None:
            if source_id is not None:
                source = await GoldSourceService.get_source(db, source_id)
            else:
                source = await GoldSourceService.get_default_source(db)

        default_src = await GoldSourceService.get_default_source(db)
        is_default_source = (
            source is not None and default_src is not None and source.id == default_src.id
        )
        active_source_id = source.id if source else None

        now_utc = datetime.now(timezone.utc)
        try:
            scrape_res = await self._fetch_prices_for_source(source)
        except Exception as e:
            if source is not None:
                source.last_scan_at = now_utc
                source.last_status = "ERROR"
                source.last_message = f"Quét thất bại: {str(e)}"
                source.last_row_count = 0
                await db.commit()
            raise

        scraped = scrape_res.prices
        self.last_scraped = list(scraped) if scraped else []
        self.last_changes = []

        if not scraped:
            logger.warning(f"No data fetched from gold scraper for source={active_source_id}; skipping persistence.")
            if source is not None:
                source.last_scan_at = now_utc
                source.last_status = "ERROR"
                source.last_message = "Không tìm thấy bảng giá vàng trên trang này."
                source.last_row_count = 0
                source.last_duration_ms = scrape_res.duration_ms
                source.last_strategy = scrape_res.strategy
                await db.commit()
            return {
                "source_id": active_source_id,
                "source_name": source.name if source else None,
                "saved_count": 0,
                "scraped": [],
                "changes": [],
                "strategy": scrape_res.strategy,
                "duration_ms": scrape_res.duration_ms,
            }

        batch_time = now_utc
        saved_count = 0
        changes: List[Dict] = []

        for dto in scraped:
            if not dto.gold_type or dto.buy_price is None or dto.sell_price is None:
                continue

            # Tìm bản ghi gần nhất của loại vàng này thuộc cùng cửa hàng
            if active_source_id is not None:
                if is_default_source:
                    source_cond = or_(
                        GoldPriceHistory.source_id == active_source_id,
                        GoldPriceHistory.source_id.is_(None),
                    )
                else:
                    source_cond = GoldPriceHistory.source_id == active_source_id
                stmt = (
                    select(GoldPriceHistory)
                    .where(source_cond, GoldPriceHistory.gold_type == dto.gold_type)
                    .order_by(GoldPriceHistory.updated_at.desc(), GoldPriceHistory.id.desc())
                    .limit(1)
                )
            else:
                stmt = (
                    select(GoldPriceHistory)
                    .where(GoldPriceHistory.gold_type == dto.gold_type)
                    .order_by(GoldPriceHistory.updated_at.desc(), GoldPriceHistory.id.desc())
                    .limit(1)
                )

            res = await db.execute(stmt)
            latest = res.scalar_one_or_none()

            should_save = False
            old_buy = float(latest.buy_price) if latest and latest.buy_price is not None else None
            old_sell = float(latest.sell_price) if latest and latest.sell_price is not None else None
            new_buy = float(dto.buy_price)
            new_sell = float(dto.sell_price)

            if latest is None:
                should_save = True
            else:
                buy_changed = latest.buy_price != dto.buy_price
                sell_changed = latest.sell_price != dto.sell_price
                if buy_changed or sell_changed:
                    should_save = True

            if should_save:
                new_record = GoldPriceHistory(
                    source_id=active_source_id,
                    gold_type=dto.gold_type,
                    buy_price=dto.buy_price,
                    sell_price=dto.sell_price,
                    price_date=dto.price_date,
                    updated_at=batch_time,
                )
                db.add(new_record)
                saved_count += 1
                changes.append(
                    {
                        "gold_type": dto.gold_type,
                        "old_buy": old_buy,
                        "new_buy": new_buy,
                        "old_sell": old_sell,
                        "new_sell": new_sell,
                        "buy_delta": (new_buy - old_buy) if old_buy is not None else None,
                        "sell_delta": (new_sell - old_sell) if old_sell is not None else None,
                    }
                )

        self.last_changes = changes

        if source is not None:
            source.last_scan_at = batch_time
            source.last_status = "SUCCESS"
            source.last_row_count = len(scraped)
            source.last_duration_ms = scrape_res.duration_ms
            source.last_strategy = scrape_res.strategy
            if saved_count > 0:
                source.last_message = f"Quét thành công ({saved_count}/{len(scraped)} loại vàng thay đổi)."
            else:
                source.last_message = f"Quét thành công ({len(scraped)} loại vàng, giá không đổi)."

        await db.commit()

        if saved_count > 0:
            logger.info(
                f"Gold crawl complete for source={active_source_id}: "
                f"{saved_count} new record(s) saved out of {len(scraped)} scraped."
            )
            await gold_sse_manager.broadcast_price_update(saved_count, source_id=active_source_id)

        return {
            "source_id": active_source_id,
            "source_name": source.name if source else None,
            "saved_count": saved_count,
            "scraped": scraped,
            "changes": changes,
            "strategy": scrape_res.strategy,
            "duration_ms": scrape_res.duration_ms,
        }

    async def crawl_and_save_changed_prices(
        self,
        db: AsyncSession,
        source: Optional[GoldSource] = None,
        source_id: Optional[int] = None,
    ) -> int:
        details = await self.crawl_and_save_with_details(db, source=source, source_id=source_id)
        return details["saved_count"]

    @staticmethod
    async def _build_source_filter(db: AsyncSession, source_id: Optional[int] = None):
        default_src = await GoldSourceService.get_default_source(db)
        target_id = source_id if source_id is not None else (default_src.id if default_src else None)
        if target_id is None:
            return None, None
        is_default = default_src is not None and target_id == default_src.id
        if is_default:
            return target_id, or_(
                GoldPriceHistory.source_id == target_id,
                GoldPriceHistory.source_id.is_(None),
            )
        return target_id, (GoldPriceHistory.source_id == target_id)

    @staticmethod
    async def delete_price_batch(db: AsyncSession, ids: List[int]) -> int:
        if not ids:
            return 0

        stmt = delete(GoldPriceHistory).where(GoldPriceHistory.id.in_(ids))
        result = await db.execute(stmt)
        deleted_count = result.rowcount or 0
        await db.commit()

        logger.info(f"Đã xóa {deleted_count} bản ghi giá vàng (IDs: {ids}).")
        if deleted_count > 0:
            await gold_sse_manager.broadcast_price_update(deleted_count)

        return deleted_count

    @staticmethod
    async def get_all_gold_types(db: AsyncSession, source_id: Optional[int] = None) -> List[str]:
        """Trả về danh sách các loại vàng của cửa hàng đang chọn."""
        _, source_cond = await GoldPriceService._build_source_filter(db, source_id)
        stmt = select(GoldPriceHistory.gold_type).distinct()
        if source_cond is not None:
            stmt = stmt.where(source_cond)
        stmt = stmt.order_by(GoldPriceHistory.gold_type.asc())
        res = await db.execute(stmt)
        records = res.scalars().all()
        return [r for r in records if r]

    @staticmethod
    async def get_latest_update_time_millis(db: AsyncSession, source_id: Optional[int] = None) -> int:
        _, source_cond = await GoldPriceService._build_source_filter(db, source_id)
        stmt = select(func.max(GoldPriceHistory.updated_at))
        if source_cond is not None:
            stmt = stmt.where(source_cond)
        res = await db.execute(stmt)
        max_time = res.scalar_one_or_none()
        if max_time:
            return int(max_time.timestamp() * 1000)
        return 0

    @staticmethod
    async def get_price_batches(
        db: AsyncSession,
        gold_type_filter: Optional[str] = None,
        source_id: Optional[int] = None,
    ) -> List[GoldBatchViewModel]:
        """
        Gom nhóm lịch sử giá vàng của cửa hàng theo từng đợt cập nhật, tính toán delta và spread.
        Thứ tự các thẻ trong cùng một đợt giữ nguyên thứ tự hàng của website (id tăng dần).
        """
        resolved_source_id, source_cond = await GoldPriceService._build_source_filter(db, source_id)

        stmt = select(GoldPriceHistory).order_by(
            GoldPriceHistory.updated_at.desc(), GoldPriceHistory.id.desc()
        )
        if source_cond is not None:
            stmt = stmt.where(source_cond)

        if gold_type_filter and gold_type_filter.strip() and gold_type_filter.upper() != "ALL":
            stmt = stmt.where(GoldPriceHistory.gold_type == gold_type_filter.strip())

        res = await db.execute(stmt)
        records = res.scalars().all()
        if not records:
            return []

        # 1. Gom bản ghi thành các đợt (batches) theo mốc thời gian / loại vàng duy nhất
        batches_raw: List[Dict] = []
        current_batch_cards: List[GoldPriceHistory] = []
        current_batch_time: Optional[datetime] = None
        seen_types_in_batch = set()

        for row in records:
            row_time = row.updated_at
            is_new_batch = False

            if current_batch_time is None:
                is_new_batch = True
            elif row.gold_type in seen_types_in_batch:
                is_new_batch = True
            elif row_time is not None and current_batch_time is not None:
                seconds_diff = abs((current_batch_time - row_time).total_seconds())
                if seconds_diff > 15:
                    is_new_batch = True

            if is_new_batch:
                if current_batch_cards:
                    batches_raw.append(
                        {
                            "batch_time": current_batch_time,
                            "cards": list(current_batch_cards),
                        }
                    )
                    current_batch_cards.clear()
                    seen_types_in_batch.clear()
                current_batch_time = row_time

            current_batch_cards.append(row)
            seen_types_in_batch.add(row.gold_type)

        if current_batch_cards:
            batches_raw.append(
                {
                    "batch_time": current_batch_time,
                    "cards": list(current_batch_cards),
                }
            )

        # 2. Tính toán delta (so sánh đợt i với các đợt cũ hơn i+1, i+2... của cùng loại vàng)
        result_batches: List[GoldBatchViewModel] = []

        for i, batch in enumerate(batches_raw):
            batch_time: datetime = batch["batch_time"]
            vn_time = to_vietnam_time(batch_time)
            formatted_time = vn_time.strftime("%H:%M:%S %d/%m/%Y") if vn_time else "–"
            is_latest = i == 0

            # Giữ nguyên thứ tự hàng như trên website (id tăng dần)
            raw_cards: List[GoldPriceHistory] = batch["cards"]
            raw_cards.sort(key=lambda c: (c.id or 0, c.gold_type or ""))

            card_view_models: List[GoldCardViewModel] = []

            for card in raw_cards:
                current_buy = float(card.buy_price)
                current_sell = float(card.sell_price)
                vn_card_updated = to_vietnam_time(card.updated_at)

                prev_buy = None
                prev_sell = None
                for prev_batch in batches_raw[i + 1 :]:
                    for prev_card in prev_batch["cards"]:
                        if prev_card.gold_type == card.gold_type:
                            prev_buy = float(prev_card.buy_price)
                            prev_sell = float(prev_card.sell_price)
                            break
                    if prev_buy is not None:
                        break

                buy_delta = (current_buy - prev_buy) if prev_buy is not None else None
                sell_delta = (current_sell - prev_sell) if prev_sell is not None else None

                card_view_models.append(
                    GoldCardViewModel(
                        id=card.id,
                        source_id=card.source_id or resolved_source_id,
                        gold_type=card.gold_type,
                        buy_price=current_buy,
                        sell_price=current_sell,
                        price_date=card.price_date,
                        updated_at=vn_card_updated,
                        buy_price_delta=buy_delta,
                        sell_price_delta=sell_delta,
                    )
                )

            result_batches.append(
                GoldBatchViewModel(
                    source_id=resolved_source_id,
                    batch_time=vn_time,
                    formatted_batch_time=formatted_time,
                    is_latest=is_latest,
                    cards=card_view_models,
                )
            )

        return result_batches


gold_price_service = GoldPriceService()
gold_source_service = GoldSourceService()
