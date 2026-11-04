import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime
from app.models.models import GoldPriceHistory
from tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_gold_endpoints_accessible_without_auth(client: AsyncClient):
    """Kiểm tra các endpoint giá vàng là public, không cần JWT token."""
    res_batches = await client.get("/api/v1/prices/batches")
    assert res_batches.status_code == 200
    assert isinstance(res_batches.json(), list)

    res_types = await client.get("/api/v1/prices/types")
    assert res_types.status_code == 200
    assert isinstance(res_types.json(), list)

    res_ver = await client.get("/api/v1/prices/version")
    assert res_ver.status_code == 200
    data = res_ver.json()
    assert "latest_time" in data


@pytest.mark.asyncio
async def test_gold_batches_calculation():
    """Kiểm tra tính toán delta ▲/▼ và chênh lệch Mua - Bán (spread)."""
    from app.services.gold_service import gold_price_service

    async with TestAsyncSessionLocal() as db:
        test_type = f"Vàng Test {uuid.uuid4().hex[:6]}"
        # Tạo bản ghi đợt 1 (cũ hơn)
        row1 = GoldPriceHistory(
            gold_type=test_type,
            buy_price=80000000.0,
            sell_price=82000000.0,
            price_date="01/11/2026",
            updated_at=datetime(2026, 11, 1, 9, 0, 0)
        )
        # Tạo bản ghi đợt 2 (mới hơn, giá tăng)
        row2 = GoldPriceHistory(
            gold_type=test_type,
            buy_price=81000000.0,
            sell_price=83500000.0,
            price_date="02/11/2026",
            updated_at=datetime(2026, 11, 2, 9, 0, 0)
        )
        db.add_all([row1, row2])
        await db.commit()

        batches = await gold_price_service.get_price_batches(db, test_type)
        assert len(batches) >= 2
        # Đợt mới nhất là batch 0
        latest_batch = batches[0]
        assert latest_batch.is_latest is True
        latest_card = latest_batch.cards[0]
        assert latest_card.gold_type == test_type
        # Spread = 83.500.000 - 81.000.000 = 2.500.000
        assert latest_card.spread == 2500000.0
        # Delta buy = 81.000.000 - 80.000.000 = +1.000.000
        assert latest_card.buy_price_delta == 1000000.0
        # Delta sell = 83.500.000 - 82.000.000 = +1.500.000
        assert latest_card.sell_price_delta == 1500000.0


@pytest.mark.asyncio
async def test_alias_endpoints(client: AsyncClient):
    """Kiểm tra các endpoint alias /api/prices/* phục vụ tương thích tối đa."""
    res = await client.get("/api/prices/types")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res_batches = await client.get("/api/prices/batches")
    assert res_batches.status_code == 200
    assert isinstance(res_batches.json(), list)


@pytest.mark.asyncio
async def test_delete_batch_endpoint(client: AsyncClient):
    """Kiểm tra xóa đợt giá vàng qua API."""
    async with TestAsyncSessionLocal() as db:
        test_type = f"Vàng Xóa {uuid.uuid4().hex[:6]}"
        row = GoldPriceHistory(
            gold_type=test_type,
            buy_price=50000000.0,
            sell_price=51000000.0,
            price_date="04/11/2026",
            updated_at=datetime.now()
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        row_id = row.id

    # Gửi yêu cầu xóa bản ghi
    res = await client.post("/api/v1/prices/batch/delete", json={"ids": [row_id]})
    assert res.status_code == 200
    data = res.json()
    assert data["deleted"] == 1

    # Kiểm tra lại DB không còn bản ghi đó
    async with TestAsyncSessionLocal() as db:
        from sqlalchemy import select
        res_db = await db.execute(select(GoldPriceHistory).where(GoldPriceHistory.id == row_id))
        assert res_db.scalar_one_or_none() is None

