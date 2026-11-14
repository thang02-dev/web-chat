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


@pytest.mark.asyncio
async def test_gold_bot_notification_modes_and_midnight_cleanup(client: AsyncClient, monkeypatch):
    """
    Kiểm tra toàn diện:
    1. Gửi tin nhắn lịch sử call từ tài khoản 'admin' -> tài khoản được chọn.
    2. Chế độ ALWAYS (gửi mỗi lần call kiểm tra, kể cả khi giá không đổi).
    3. Chế độ CHANGE_ONLY (chỉ gửi khi giá thay đổi).
    4. Tự động xóa toàn bộ tin nhắn thông báo bot lúc 00:00 (giờ VN) nhưng bảo toàn tin nhắn chat thường.
    5. Khôi phục bền vững trạng thái và nhật ký quét từ DB khi khởi động lại GoldCrawlerManager.
    """
    from decimal import Decimal
    from datetime import timedelta
    from sqlalchemy import select
    from app.schemas.gold import GoldPriceDto
    from app.services.gold_crawler import gold_crawler
    from app.services.gold_crawler_manager import crawler_manager, GoldCrawlerManager, VN_TZ
    from app.services.chat_service import ChatService
    from app.models.models import User, Message

    suffix = uuid.uuid4().hex[:8]
    gold_type_name = f"Vàng Bot Test {suffix}"

    # 1. Đăng ký tài khoản người nhận thông báo
    reg_res = await client.post("/api/v1/auth/register", json={
        "username": f"bot_recv_{suffix}",
        "email": f"bot_recv_{suffix}@example.com",
        "password": "Password123!",
        "full_name": f"Người Nhận Bot {suffix}"
    })
    assert reg_res.status_code == 201
    recipient_id = reg_res.json()["id"]

    # Mock dữ liệu giá vàng trả về từ crawler
    current_prices = [
        GoldPriceDto(
            gold_type=gold_type_name,
            buy_price=Decimal("12500000"),
            sell_price=Decimal("12650000"),
            price_date="14/11/2026"
        )
    ]

    async def mock_fetch_gold_prices():
        return current_prices

    monkeypatch.setattr(gold_crawler, "fetch_gold_prices", mock_fetch_gold_prices)

    async with TestAsyncSessionLocal() as db:
        # Đảm bảo dọn sạch tin nhắn bot cũ trước khi test
        await crawler_manager.cleanup_bot_messages(db=db)

        # Cấu hình: Chọn người nhận + chế độ ALWAYS (Mỗi lần call)
        await crawler_manager.save_settings(
            db,
            interval_minutes=10,
            is_enabled=True,
            notify_user_id=recipient_id,
            notify_mode="ALWAYS"
        )

        # Lượt call 1: Giá mới (saved = 1) -> Phải gửi tin nhắn từ admin
        res1 = await crawler_manager.trigger_crawl(source="SCHEDULED", db=db)
        assert res1["success"] is True
        assert res1["saved"] == 1
        assert res1["notified"] is True

        # Lượt call 2: Giá giữ nguyên (saved = 0), chế độ ALWAYS -> Vẫn phải gửi tin nhắn báo cáo
        res2 = await crawler_manager.trigger_crawl(source="SCHEDULED", db=db)
        assert res2["success"] is True
        assert res2["saved"] == 0
        assert res2["notified"] is True

        # Chuyển sang chế độ CHANGE_ONLY (Chỉ khi giá thay đổi)
        await crawler_manager.save_settings(
            db,
            interval_minutes=10,
            is_enabled=True,
            notify_user_id=recipient_id,
            notify_mode="CHANGE_ONLY"
        )

        # Lượt call 3: Giá vẫn giữ nguyên (saved = 0), chế độ CHANGE_ONLY -> KHÔNG gửi tin nhắn
        res3 = await crawler_manager.trigger_crawl(source="SCHEDULED", db=db)
        assert res3["success"] is True
        assert res3["saved"] == 0
        assert res3["notified"] is False

        # Lượt call 4: Giá tăng (saved = 1), chế độ CHANGE_ONLY -> PHẢI gửi tin nhắn
        current_prices = [
            GoldPriceDto(
                gold_type=gold_type_name,
                buy_price=Decimal("12550000"),
                sell_price=Decimal("12700000"),
                price_date="14/11/2026"
            )
        ]
        res4 = await crawler_manager.trigger_crawl(source="SCHEDULED", db=db)
        assert res4["success"] is True
        assert res4["saved"] == 1
        assert res4["notified"] is True

        # Kiểm tra các tin nhắn trong cuộc trò chuyện giữa admin và recipient_id
        admin_res = await db.execute(select(User).where(User.username == "admin"))
        admin_user = admin_res.scalars().first()
        assert admin_user is not None

        conv = await ChatService.get_or_create_bot_conversation(db, admin_user.id, recipient_id)
        msgs_res = await db.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.asc())
        )
        bot_msgs = list(msgs_res.scalars().all())
        # Tổng cộng 3 tin nhắn bot đã được gửi (res1, res2, res4)
        assert len(bot_msgs) == 3
        for m in bot_msgs:
            assert m.sender_id == admin_user.id
            assert m.client_temp_id.startswith("gold_bot_")
            assert "[BOT GIÁ VÀNG - LỊCH SỬ CALL]" in m.content

        # Tạo thêm 1 tin nhắn trò chuyện bình thường giữa recipient và admin
        normal_msg, _ = await ChatService.create_message(
            db,
            conversation_id=conv.id,
            sender_id=recipient_id,
            content="Tin nhắn trao đổi bình thường không được xóa!",
            client_temp_id=f"user_msg_{suffix}"
        )

        # Kiểm tra khôi phục trạng thái bền vững từ DB khi khởi tạo manager mới (mô phỏng server restart)
        restarted_mgr = GoldCrawlerManager()
        await restarted_mgr.init_from_db(db=db)
        assert restarted_mgr.notify_user_id == recipient_id
        assert restarted_mgr.notify_mode == "CHANGE_ONLY"
        assert restarted_mgr.last_crawl_at is not None
        assert len(restarted_mgr.recent_logs) >= 4
        assert restarted_mgr.bot_message_count == 3

        # Mô phỏng đồng hồ bước qua 00:00 (0h đêm ngày hôm sau theo giờ Việt Nam)
        tomorrow_vn = datetime.now(VN_TZ) + timedelta(days=1)
        deleted_count = await crawler_manager.check_and_run_midnight_cleanup(db=db, now_vn=tomorrow_vn)
        assert deleted_count == 3
        assert crawler_manager.bot_message_count == 0

        # Kiểm tra lại DB: toàn bộ tin nhắn bot đã bị xóa, nhưng tin nhắn chat thường vẫn còn nguyên
        remaining_res = await db.execute(
            select(Message).where(Message.conversation_id == conv.id)
        )
        remaining_msgs = list(remaining_res.scalars().all())
        assert len(remaining_msgs) == 1
        assert remaining_msgs[0].id == normal_msg.id
        assert remaining_msgs[0].content == "Tin nhắn trao đổi bình thường không được xóa!"


@pytest.mark.asyncio
async def test_gold_bot_self_admin_recipient_and_cleanup_api(client: AsyncClient, monkeypatch):
    """
    Kiểm tra các trường hợp biên:
    1. Admin chọn chính tài khoản 'admin' làm tài khoản nhận tin lịch sử call.
    2. Gọi API POST /api/v1/users/admin/crawler-cleanup xóa sạch tin nhắn bot.
    3. Tắt chọn tài khoản nhận (notify_user_id = None) -> không gửi tin nhắn.
    4. Khi khởi động lại mà last_crawl_at đã quá hạn interval_minutes -> next_crawl_at đặt về hiện tại để quét ngay.
    """
    from decimal import Decimal
    from datetime import timedelta, timezone
    from app.schemas.gold import GoldPriceDto
    from app.services.gold_crawler import gold_crawler
    from app.services.gold_crawler_manager import crawler_manager, GoldCrawlerManager

    suffix = uuid.uuid4().hex[:8]

    # Login admin
    res_login = await client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "123456"
    })
    assert res_login.status_code == 200
    admin_token = res_login.json()["access_token"]
    admin_id = res_login.json()["user"]["id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    async def mock_fetch():
        return [
            GoldPriceDto(
                gold_type=f"Vàng 9999 {suffix}",
                buy_price=Decimal("12600000"),
                sell_price=Decimal("12750000"),
                price_date="14/11/2026"
            )
        ]

    monkeypatch.setattr(gold_crawler, "fetch_gold_prices", mock_fetch)

    # 1. Cấu hình người nhận là chính tài khoản admin
    cfg_res = await client.post(
        "/api/v1/users/admin/crawler-config",
        json={
            "interval_minutes": 10,
            "is_enabled": True,
            "notify_user_id": admin_id,
            "notify_mode": "ALWAYS"
        },
        headers=admin_headers
    )
    assert cfg_res.status_code == 200
    assert cfg_res.json()["notify_user_id"] == admin_id

    # Kích hoạt quét qua API admin
    trig_res = await client.post("/api/v1/users/admin/crawler-trigger", headers=admin_headers)
    assert trig_res.status_code == 200
    assert trig_res.json()["success"] is True
    assert trig_res.json()["notified"] is True

    # Kiểm tra bot_message_count >= 1
    status_res = await client.get("/api/v1/users/admin/crawler-config", headers=admin_headers)
    assert status_res.status_code == 200
    assert status_res.json()["bot_message_count"] >= 1

    # 2. Gọi API xóa tin nhắn bot ngay lập tức
    cleanup_res = await client.post("/api/v1/users/admin/crawler-cleanup", headers=admin_headers)
    assert cleanup_res.status_code == 200
    assert cleanup_res.json()["success"] is True
    assert cleanup_res.json()["deleted"] >= 1

    status_after = await client.get("/api/v1/users/admin/crawler-config", headers=admin_headers)
    assert status_after.json()["bot_message_count"] == 0

    # 3. Tắt thông báo (notify_user_id = None)
    await client.post(
        "/api/v1/users/admin/crawler-config",
        json={
            "interval_minutes": 10,
            "is_enabled": True,
            "notify_user_id": None,
            "notify_mode": "ALWAYS"
        },
        headers=admin_headers
    )
    trig_disabled = await client.post("/api/v1/users/admin/crawler-trigger", headers=admin_headers)
    assert trig_disabled.status_code == 200
    assert trig_disabled.json()["notified"] is False

    # 4. Kiểm tra thuật toán catch-up khi last_crawl_at quá hạn
    async with TestAsyncSessionLocal() as db:
        crawler_manager.last_crawl_at = datetime.now(timezone.utc) - timedelta(minutes=25)
        crawler_manager.interval_minutes = 10
        crawler_manager.is_enabled = True
        await crawler_manager._persist_runtime_state(db)

        cold_start_mgr = GoldCrawlerManager()
        await cold_start_mgr.init_from_db(db=db)
        assert cold_start_mgr.next_crawl_at is not None
        # Vì 25 phút > 10 phút nên next_crawl_at phải <= thời điểm hiện tại để quét ngay lập tức
        assert cold_start_mgr.next_crawl_at <= datetime.now(timezone.utc) + timedelta(seconds=1)



