"""Test đa cửa hàng giá vàng: engine bóc tách, SSRF guard, CRUD admin, quét thử, cô lập dữ liệu theo cửa hàng.

Không gọi mạng thật: HTML lấy từ tests/fixtures/gold, tầng tải được monkeypatch.
"""
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from httpx import AsyncClient

from app.models.models import GoldSource
from app.schemas.gold import ExtractRules
from app.services import gold_scraper, gold_service
from app.services.gold_crawler_manager import crawler_manager
from app.services.url_guard import UnsafeUrlError, safe_fetch_text, validate_public_url

FIX = Path(__file__).parent / "fixtures" / "gold"
HVT_HOME = (FIX / "hieuvangtru_home.html").read_text(encoding="utf-8")
HVT_TABLE = (FIX / "hieuvangtru_load_bang_gia.html").read_text(encoding="utf-8")
NT_HOME = (FIX / "ngocthinh_home.html").read_text(encoding="utf-8")

SHOP_HVT = "https://shop-hvt.example.test/"
SHOP_NT = "https://shop-nt.example.test/"


def fake_fetch_factory(pages: dict):
    async def fake(url, **kwargs):
        if url in pages:
            return pages[url], url
        raise httpx.ConnectError("offline")
    return fake


@pytest.fixture
def offline(monkeypatch):
    pages = {
        SHOP_HVT: HVT_HOME,
        SHOP_HVT.rstrip("/") + "/layout/load_bang_gia.php": HVT_TABLE,
        SHOP_NT: NT_HOME,
    }
    monkeypatch.setattr(gold_scraper, "safe_fetch_text", fake_fetch_factory(pages))

    async def ok_validate(url):
        return url
    monkeypatch.setattr(gold_service, "validate_public_url", ok_validate)
    return pages


async def admin_headers(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username_or_email": "admin", "password": "123456"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def create_store(client, headers, name, url, **extra):
    res = await client.post("/api/v1/admin/gold-sources", json={"name": name, "url": url, **extra}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


async def delete_store(client, headers, sid):
    await client.delete(f"/api/v1/admin/gold-sources/{sid}", headers=headers)


# ---------------------------------------------------------------- engine ----

def test_table_strategy_hieuvangtru_sell_before_buy():
    prices, strategy, _ = gold_scraper.parse_html_with_strategy(HVT_TABLE)
    assert strategy == "TABLE"
    assert len(prices) == 3
    p9999 = next(p for p in prices if "9999" in p.gold_type)
    assert int(p9999.buy_price) == 11_880_000
    assert int(p9999.sell_price) == 12_040_000


def test_div_grid_strategy_ngocthinh_buy_before_sell_and_dedup():
    prices, strategy, _ = gold_scraper.parse_html_with_strategy(NT_HOME)
    assert strategy == "DIV_GRID"
    assert len(prices) == 7  # khối desktop/mobile trùng nhau phải được khử trùng
    p9999 = next(p for p in prices if "9999" in p.gold_type)
    assert int(p9999.buy_price) == 11_900_000
    assert int(p9999.sell_price) == 12_060_000
    assert all(p.buy_price <= p.sell_price for p in prices)


def test_css_rules_strategy():
    rules = ExtractRules(
        mode="CSS",
        row_selector=".contenttogoldflex > div",
        name_selector=".headerindex1",
        buy_selector=".headerindex2",
        sell_selector=".headerindex3",
    )
    prices, strategy, _ = gold_scraper.parse_html_with_strategy(NT_HOME, rules)
    assert strategy == "CSS"
    assert len(prices) >= 7


def test_invalid_css_selector_rejected():
    with pytest.raises(ValueError):
        ExtractRules(mode="CSS", row_selector="div[[[")


def test_empty_html_returns_none():
    assert gold_scraper.parse_html_with_strategy("")[1] == "NONE"
    assert gold_scraper.parse_html_with_strategy("<html><body>không có bảng</body></html>")[0] == []


def test_ajax_discovery_finds_endpoint():
    urls = gold_scraper.discover_ajax_price_urls(HVT_HOME, SHOP_HVT)
    assert any(u.endswith("/layout/load_bang_gia.php") for u in urls)


@pytest.mark.asyncio
async def test_scrape_auto_uses_ajax_discovery(offline):
    res = await gold_scraper.scrape(SHOP_HVT, retries=1)
    assert res.strategy == "AJAX_DISCOVERY"
    assert len(res.prices) == 3


# ------------------------------------------------------------- SSRF guard ----

@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "ftp://example.com/x",
    "file:///etc/passwd",
    "javascript:alert(1)",
    "http://localhost/",
    "http://127.0.0.1/",
    "http://169.254.169.254/latest/meta-data",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://[::1]/",
    "http://printer.local/",
    "",
])
async def test_ssrf_blocks_unsafe_urls(url):
    with pytest.raises(UnsafeUrlError):
        await validate_public_url(url)


class _Resp:
    def __init__(self, status=200, headers=None, body=b"ok"):
        self.status_code = status
        self.headers = headers or {"content-type": "text/html"}
        self._body = body
        self.encoding = "utf-8"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    async def aiter_bytes(self):
        yield self._body


class _Client:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def stream(self, method, url, **kw):
        self.calls.append(url)
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_redirect_to_private_ip_is_blocked():
    c = _Client([_Resp(302, {"location": "http://127.0.0.1/admin"})])
    with pytest.raises(UnsafeUrlError):
        await safe_fetch_text("http://8.8.8.8/", client=c)
    assert c.calls == ["http://8.8.8.8/"]  # không bao giờ request tới IP nội bộ


@pytest.mark.asyncio
async def test_too_many_redirects_blocked():
    c = _Client([_Resp(302, {"location": "http://8.8.4.4/"}) for _ in range(6)])
    with pytest.raises(UnsafeUrlError):
        await safe_fetch_text("http://8.8.8.8/", client=c)


@pytest.mark.asyncio
async def test_oversize_and_bad_content_type_blocked():
    big = _Client([_Resp(body=b"x" * (3 * 1024 * 1024 + 1))])
    with pytest.raises(UnsafeUrlError):
        await safe_fetch_text("http://8.8.8.8/", client=big)
    img = _Client([_Resp(headers={"content-type": "image/png"})])
    with pytest.raises(UnsafeUrlError):
        await safe_fetch_text("http://8.8.8.8/", client=img)


@pytest.mark.asyncio
async def test_safe_fetch_returns_text_for_public_ip():
    c = _Client([_Resp(body="Vàng 9999".encode())])
    text, final = await safe_fetch_text("http://8.8.8.8/", client=c)
    assert "9999" in text and final == "http://8.8.8.8/"


# ------------------------------------------------------- admin API: authz ----

@pytest.mark.asyncio
async def test_admin_endpoints_require_admin(client: AsyncClient):
    for method, path in [
        ("get", "/api/v1/admin/gold-sources"),
        ("post", "/api/v1/admin/gold-sources/test"),
        ("put", "/api/v1/admin/gold-sources/reorder"),
        ("post", "/api/v1/admin/gold-sources/1/test"),
        ("delete", "/api/v1/admin/gold-sources/1"),
    ]:
        res = await getattr(client, method)(path)
        assert res.status_code in (401, 403, 422), (method, path, res.status_code)
    # 401 chắc chắn cho GET danh sách khi chưa đăng nhập
    assert (await client.get("/api/v1/admin/gold-sources")).status_code == 401

    suffix = uuid.uuid4().hex[:8]
    reg = await client.post("/api/v1/auth/register", json={
        "username": f"u_{suffix}", "email": f"u_{suffix}@example.com",
        "password": "Password123!", "full_name": "User Thuong",
    })
    assert reg.status_code == 201
    login = await client.post("/api/v1/auth/login", json={
        "username_or_email": f"u_{suffix}", "password": "Password123!"})
    uh = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/api/v1/admin/gold-sources", headers=uh)).status_code == 403
    assert (await client.post("/api/v1/admin/gold-sources", headers=uh,
                              json={"name": "x", "url": "https://x.example.test"})).status_code == 403


# ---------------------------------------------------------- admin API: CRUD ----

@pytest.mark.asyncio
async def test_crud_and_validation(client: AsyncClient, offline):
    h = await admin_headers(client)
    created = await create_store(client, h, "Tiệm Test CRUD", SHOP_HVT, interval_minutes=15)
    sid = created["id"]
    try:
        assert created["last_status"] == "NEVER"
        assert created["interval_minutes"] == 15

        lst = (await client.get("/api/v1/admin/gold-sources", headers=h)).json()
        assert sid in [s["id"] for s in lst]
        # cửa hàng mới luôn nằm cuối
        assert lst[-1]["id"] == sid

        upd = await client.patch(f"/api/v1/admin/gold-sources/{sid}", headers=h,
                                 json={"name": "Tiệm Đã Sửa", "interval_minutes": 30, "is_enabled": False})
        assert upd.status_code == 200
        assert upd.json()["name"] == "Tiệm Đã Sửa" and upd.json()["is_enabled"] is False

        # disabled không hiện ở public
        pub = (await client.get("/api/v1/prices/sources")).json()
        assert sid not in [s["id"] for s in pub]

        # validation
        bad = [
            {"name": "", "url": SHOP_HVT},
            {"name": "A", "url": "ftp://x.example.test"},
            {"name": "A", "url": SHOP_HVT, "interval_minutes": 0},
            {"name": "A", "url": SHOP_HVT, "interval_minutes": 1441},
            {"name": "A", "url": SHOP_HVT, "extract_rules": {"mode": "CSS", "row_selector": "div[[["}},
        ]
        for body in bad:
            r = await client.post("/api/v1/admin/gold-sources", json=body, headers=h)
            assert r.status_code == 422, body

        assert (await client.patch("/api/v1/admin/gold-sources/99999999", headers=h,
                                   json={"name": "x"})).status_code == 404
    finally:
        await delete_store(client, h, sid)


@pytest.mark.asyncio
async def test_create_rejects_private_url(client: AsyncClient):
    h = await admin_headers(client)
    for url in ("http://127.0.0.1/", "http://169.254.169.254/", "http://localhost:8000/"):
        r = await client.post("/api/v1/admin/gold-sources", json={"name": "Xấu", "url": url}, headers=h)
        assert r.status_code == 400, url


@pytest.mark.asyncio
async def test_reorder_atomic_and_validation(client: AsyncClient, offline):
    h = await admin_headers(client)
    a = await create_store(client, h, "Reorder A", SHOP_HVT)
    b = await create_store(client, h, "Reorder B", SHOP_NT)
    original = [s["id"] for s in (await client.get("/api/v1/admin/gold-sources", headers=h)).json()]
    try:
        new_order = list(reversed(original))
        r = await client.put("/api/v1/admin/gold-sources/reorder", json={"ids": new_order}, headers=h)
        assert r.status_code == 200
        assert [s["id"] for s in r.json()] == new_order
        pub_ids = [s["id"] for s in (await client.get("/api/v1/prices/sources")).json()]
        assert pub_ids == [i for i in new_order if i in pub_ids]

        # trùng ID / thiếu ID / ID lạ -> 400 và thứ tự cũ giữ nguyên
        for ids in ([new_order[0], new_order[0]], new_order[:-1], new_order + [99999999]):
            assert (await client.put("/api/v1/admin/gold-sources/reorder",
                                     json={"ids": ids}, headers=h)).status_code == 400
        after = [s["id"] for s in (await client.get("/api/v1/admin/gold-sources", headers=h)).json()]
        assert after == new_order
    finally:
        await client.put("/api/v1/admin/gold-sources/reorder", json={"ids": original}, headers=h)
        await delete_store(client, h, a["id"])
        await delete_store(client, h, b["id"])


# ------------------------------------------------------------ test-scrape ----

@pytest.mark.asyncio
async def test_draft_test_scrape_success_and_failure(client: AsyncClient, offline):
    h = await admin_headers(client)
    ok = await client.post("/api/v1/admin/gold-sources/test", json={"url": SHOP_NT}, headers=h)
    assert ok.status_code == 200
    body = ok.json()
    assert body["success"] is True and body["status"] == "SUCCESS"
    assert body["strategy"] == "DIV_GRID" and body["row_count"] == 7
    assert len(body["preview"]) == 7

    fail = await client.post("/api/v1/admin/gold-sources/test",
                             json={"url": "https://khong-ton-tai.example.test/"}, headers=h)
    assert fail.status_code == 200
    assert fail.json()["success"] is False and fail.json()["status"] == "ERROR"

    blocked = await client.post("/api/v1/admin/gold-sources/test",
                                json={"url": "http://127.0.0.1/"}, headers=h)
    assert blocked.status_code == 200 and blocked.json()["success"] is False


@pytest.mark.asyncio
async def test_saved_test_scrape_updates_status_but_not_history(client: AsyncClient, offline):
    h = await admin_headers(client)
    ok_store = await create_store(client, h, "Test Quét OK", SHOP_HVT)
    bad_store = await create_store(client, h, "Test Quét Lỗi", "https://down.example.test/")
    try:
        r1 = await client.post(f"/api/v1/admin/gold-sources/{ok_store['id']}/test", headers=h)
        r2 = await client.post(f"/api/v1/admin/gold-sources/{bad_store['id']}/test", headers=h)
        assert r1.json()["success"] is True
        assert r2.json()["success"] is False

        stores = {s["id"]: s for s in (await client.get("/api/v1/admin/gold-sources", headers=h)).json()}
        assert stores[ok_store["id"]]["last_status"] == "SUCCESS"
        assert stores[ok_store["id"]]["last_row_count"] == 3
        assert stores[ok_store["id"]]["last_scan_at"] is not None
        assert stores[bad_store["id"]]["last_status"] == "ERROR"

        # KHÔNG lưu lịch sử
        for sid in (ok_store["id"], bad_store["id"]):
            prev = await client.delete(f"/api/v1/admin/gold-sources/{sid}?preview=true", headers=h)
            assert prev.status_code == 200
            assert prev.json()["history_count"] == 0 and prev.json()["deleted"] is False
        types = await client.get(f"/api/v1/prices/types?source_id={ok_store['id']}")
        assert types.json() == []

        assert (await client.post("/api/v1/admin/gold-sources/99999999/test", headers=h)).status_code == 404
    finally:
        await delete_store(client, h, ok_store["id"])
        await delete_store(client, h, bad_store["id"])


# ------------------------------------------- isolation, cascade, scheduler ----

@pytest.mark.asyncio
async def test_multi_source_isolation_and_cascade_delete(client: AsyncClient, offline):
    h = await admin_headers(client)
    a = await create_store(client, h, "Cô lập A", SHOP_HVT)
    b = await create_store(client, h, "Cô lập B", SHOP_NT)
    try:
        crawl = await client.post(f"/api/v1/prices/crawl?source_id={a['id']}")
        assert crawl.status_code == 200
        assert crawl.json()["saved"] == 3

        types_a = (await client.get(f"/api/v1/prices/types?source_id={a['id']}")).json()
        types_b = (await client.get(f"/api/v1/prices/types?source_id={b['id']}")).json()
        assert any("9999" in t for t in types_a)
        assert types_b == []

        batches_a = (await client.get(f"/api/v1/prices/batches?source_id={a['id']}")).json()
        batches_b = (await client.get(f"/api/v1/prices/batches?source_id={b['id']}")).json()
        assert len(batches_a) >= 1 and batches_b == []

        # quét lần 2 giá không đổi -> không lưu thêm
        again = await client.post(f"/api/v1/prices/crawl?source_id={a['id']}")
        assert again.json()["saved"] == 0

        # quét B không ảnh hưởng A
        await client.post(f"/api/v1/prices/crawl?source_id={b['id']}")
        types_b2 = (await client.get(f"/api/v1/prices/types?source_id={b['id']}")).json()
        assert any("9999" in t for t in types_b2)
        assert (await client.get(f"/api/v1/prices/types?source_id={a['id']}")).json() == types_a

        # preview rồi xóa -> cascade lịch sử
        prev = (await client.delete(f"/api/v1/admin/gold-sources/{a['id']}?preview=true", headers=h)).json()
        assert prev["history_count"] == 3
        done = (await client.delete(f"/api/v1/admin/gold-sources/{a['id']}", headers=h)).json()
        assert done["deleted"] is True and done["history_count"] == 3
        assert (await client.get(f"/api/v1/prices/types?source_id={b['id']}")).json() == types_b2
        assert (await client.delete(f"/api/v1/admin/gold-sources/{a['id']}", headers=h)).status_code == 404
    finally:
        await delete_store(client, h, a["id"])
        await delete_store(client, h, b["id"])


@pytest.mark.asyncio
async def test_crawl_unknown_source_returns_404(client: AsyncClient):
    assert (await client.post("/api/v1/prices/crawl?source_id=99999999")).status_code == 404


def test_scheduler_per_source_due_logic():
    now = datetime.now(timezone.utc)

    def src(**kw):
        d = dict(is_enabled=True, interval_minutes=10, last_scan_at=None)
        d.update(kw)
        return GoldSource(name="s", url="https://s.example.test", **d)

    assert crawler_manager._is_source_due(src(), now) is True  # chưa quét lần nào
    assert crawler_manager._is_source_due(src(is_enabled=False), now) is False
    assert crawler_manager._is_source_due(src(last_scan_at=now - timedelta(minutes=3)), now) is False
    assert crawler_manager._is_source_due(src(last_scan_at=now - timedelta(minutes=11)), now) is True
    assert crawler_manager._is_source_due(
        src(interval_minutes=60, last_scan_at=now - timedelta(minutes=30)), now) is False
    naive = (now - timedelta(minutes=30)).replace(tzinfo=None)
    assert crawler_manager._is_source_due(src(interval_minutes=5, last_scan_at=naive), now) is True


@pytest.mark.asyncio
async def test_public_sources_default_is_first_and_config_per_source(client: AsyncClient):
    pub = (await client.get("/api/v1/prices/sources")).json()
    assert len(pub) >= 2
    assert [s["sort_order"] for s in pub] == sorted(s["sort_order"] for s in pub)
    cfg = (await client.get(f"/api/v1/prices/config?source_id={pub[0]['id']}")).json()
    assert cfg["source_id"] == pub[0]["id"]
    default_cfg = (await client.get("/api/v1/prices/config")).json()
    assert default_cfg["source_id"] == pub[0]["id"]

