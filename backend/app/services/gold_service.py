import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import GoldPriceHistory
from app.schemas.gold import GoldBatchViewModel, GoldCardViewModel, GoldPriceDto
from app.services.gold_crawler import gold_crawler
from app.websocket.gold_sse import gold_sse_manager

logger = logging.getLogger("webchat.gold.service")

# Múi giờ chuẩn Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))


def to_vietnam_time(dt: Optional[datetime]) -> Optional[datetime]:
    """Chuyển đổi datetime sang múi giờ Việt Nam (UTC+7)."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ)


PREFERRED_TYPE_ORDER = [
    "Vàng 9999",
    "Vàng 98%",
    "Vàng Nữ trang 98%"
]


def get_sort_priority(gold_type: str) -> int:
    """Returns sorting index for standard gold display order."""
    if not gold_type:
        return 999
    gt_clean = gold_type.strip().lower()
    for idx, pref in enumerate(PREFERRED_TYPE_ORDER):
        if pref.lower() == gt_clean:
            return idx
    return 999


class GoldPriceService:
    def __init__(self):
        self.last_scraped: List[GoldPriceDto] = []
        self.last_changes: List[Dict] = []

    async def crawl_and_save_with_details(self, db: AsyncSession) -> Dict:
        """
        Crawls hieuvangtru.vn, detects price changes, persists only changed rows,
        and returns detailed scrape & change metadata for audit and chat notification.
        """
        scraped = await gold_crawler.fetch_gold_prices()
        self.last_scraped = list(scraped) if scraped else []
        self.last_changes = []

        if not scraped:
            logger.warning("No data fetched from gold crawler; skipping persistence.")
            return {
                "saved_count": 0,
                "scraped": [],
                "changes": []
            }

        batch_time = datetime.now(timezone.utc)
        saved_count = 0
        changes: List[Dict] = []

        for dto in scraped:
            if not dto.gold_type or dto.buy_price is None or dto.sell_price is None:
                continue

            # Find most recent record for this gold type
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
                logger.debug(f"First record for '{dto.gold_type}': will save.")
                should_save = True
            else:
                buy_changed = latest.buy_price != dto.buy_price
                sell_changed = latest.sell_price != dto.sell_price
                if buy_changed or sell_changed:
                    logger.info(
                        f"Price change detected for '{dto.gold_type}': "
                        f"buy {latest.buy_price} -> {dto.buy_price}, "
                        f"sell {latest.sell_price} -> {dto.sell_price}"
                    )
                    should_save = True

            if should_save:
                new_record = GoldPriceHistory(
                    gold_type=dto.gold_type,
                    buy_price=dto.buy_price,
                    sell_price=dto.sell_price,
                    price_date=dto.price_date,
                    updated_at=batch_time,
                )
                db.add(new_record)
                saved_count += 1
                changes.append({
                    "gold_type": dto.gold_type,
                    "old_buy": old_buy,
                    "new_buy": new_buy,
                    "old_sell": old_sell,
                    "new_sell": new_sell,
                    "buy_delta": (new_buy - old_buy) if old_buy is not None else None,
                    "sell_delta": (new_sell - old_sell) if old_sell is not None else None,
                })

        self.last_changes = changes

        if saved_count > 0:
            await db.commit()
            logger.info(f"Gold crawl cycle complete: {saved_count} new record(s) saved out of {len(scraped)} scraped.")
            await gold_sse_manager.broadcast_price_update(saved_count)
        else:
            logger.debug("Gold crawl cycle complete: 0 new record(s) saved.")

        return {
            "saved_count": saved_count,
            "scraped": scraped,
            "changes": changes
        }

    async def crawl_and_save_changed_prices(self, db: AsyncSession) -> int:
        """
        Crawls hieuvangtru.vn, detects price changes, and persists only changed rows.
        Broadcasts SSE event if any changes were saved.
        """
        details = await self.crawl_and_save_with_details(db)
        return details["saved_count"]

    @staticmethod
    async def delete_price_batch(db: AsyncSession, ids: List[int]) -> int:
        """
        Xóa các bản ghi giá vàng theo danh sách ID và phát tín hiệu SSE cập nhật.
        """
        if not ids:
            return 0

        from sqlalchemy import delete
        stmt = delete(GoldPriceHistory).where(GoldPriceHistory.id.in_(ids))
        result = await db.execute(stmt)
        deleted_count = result.rowcount or 0
        await db.commit()

        logger.info(f"Đã xóa {deleted_count} bản ghi giá vàng (IDs: {ids}).")
        if deleted_count > 0:
            await gold_sse_manager.broadcast_price_update(deleted_count)

        return deleted_count

    @staticmethod
    async def get_all_gold_types(db: AsyncSession) -> List[str]:
        """Returns all distinct gold type names for the filter dropdown."""
        stmt = (
            select(GoldPriceHistory.gold_type)
            .distinct()
            .order_by(GoldPriceHistory.gold_type.asc())
        )
        res = await db.execute(stmt)
        records = res.scalars().all()
        return [r for r in records if r]

    @staticmethod
    async def get_latest_update_time_millis(db: AsyncSession) -> int:
        """Returns the epoch millis of the latest record's updated_at."""
        stmt = select(func.max(GoldPriceHistory.updated_at))
        res = await db.execute(stmt)
        max_time = res.scalar_one_or_none()
        if max_time:
            return int(max_time.timestamp() * 1000)
        return 0

    @staticmethod
    async def get_price_batches(db: AsyncSession, gold_type_filter: Optional[str] = None) -> List[GoldBatchViewModel]:
        """
        Groups all history records into chronological batches with deltas & spread computed.
        First batch is marked is_latest=True.
        """
        stmt = select(GoldPriceHistory).order_by(
            GoldPriceHistory.updated_at.desc(), GoldPriceHistory.id.desc()
        )

        if gold_type_filter and gold_type_filter.strip() and gold_type_filter.upper() != "ALL":
            stmt = stmt.where(GoldPriceHistory.gold_type == gold_type_filter.strip())

        res = await db.execute(stmt)
        records = res.scalars().all()
        if not records:
            return []

        # 1. Group records into batches by timestamp / distinct gold type
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
                    batches_raw.append({
                        "batch_time": current_batch_time,
                        "cards": list(current_batch_cards)
                    })
                    current_batch_cards.clear()
                    seen_types_in_batch.clear()
                current_batch_time = row_time

            current_batch_cards.append(row)
            seen_types_in_batch.add(row.gold_type)

        if current_batch_cards:
            batches_raw.append({
                "batch_time": current_batch_time,
                "cards": list(current_batch_cards)
            })

        # 2. Compute deltas (compare batch i with earlier batches i+1, i+2... for same gold_type)
        result_batches: List[GoldBatchViewModel] = []

        for i, batch in enumerate(batches_raw):
            batch_time: datetime = batch["batch_time"]
            vn_time = to_vietnam_time(batch_time)
            formatted_time = vn_time.strftime("%H:%M:%S %d/%m/%Y") if vn_time else "–"
            is_latest = (i == 0)

            # Sort cards according to standard priority
            raw_cards: List[GoldPriceHistory] = batch["cards"]
            raw_cards.sort(key=lambda c: (get_sort_priority(c.gold_type), c.gold_type))

            card_view_models: List[GoldCardViewModel] = []

            for card in raw_cards:
                current_buy = float(card.buy_price)
                current_sell = float(card.sell_price)
                vn_card_updated = to_vietnam_time(card.updated_at)

                prev_buy = None
                prev_sell = None
                for prev_batch in batches_raw[i + 1:]:
                    for prev_card in prev_batch["cards"]:
                        if prev_card.gold_type == card.gold_type:
                            prev_buy = float(prev_card.buy_price)
                            prev_sell = float(prev_card.sell_price)
                            break
                    if prev_buy is not None:
                        break

                buy_delta = (current_buy - prev_buy) if prev_buy is not None else None
                sell_delta = (current_sell - prev_sell) if prev_sell is not None else None

                card_view_models.append(GoldCardViewModel(
                    id=card.id,
                    gold_type=card.gold_type,
                    buy_price=current_buy,
                    sell_price=current_sell,
                    price_date=card.price_date,
                    updated_at=vn_card_updated,
                    buy_price_delta=buy_delta,
                    sell_price_delta=sell_delta
                ))

            result_batches.append(GoldBatchViewModel(
                batch_time=vn_time,
                formatted_batch_time=formatted_time,
                is_latest=is_latest,
                cards=card_view_models
            ))

        return result_batches


gold_price_service = GoldPriceService()

